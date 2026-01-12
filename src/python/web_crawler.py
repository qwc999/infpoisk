import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set, List, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from collections import deque
import requests
from bs4 import BeautifulSoup


class RobotsTxtParser:
    def __init__(self, user_agent: str = '*'):
        self.user_agent = user_agent
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.crawl_delays: Dict[str, float] = {}
    
    def get_robots_parser(self, base_url: str) -> RobotFileParser:
        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self.robots_cache:
            robots_url = urljoin(domain, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self.robots_cache[domain] = rp
                delay = rp.crawl_delay(self.user_agent)
                if delay:
                    self.crawl_delays[domain] = delay
            except Exception as e:
                logging.warning(f"Error reading robots.txt from {robots_url}: {e}")
                rp = RobotFileParser()
                rp.set_url(robots_url)
                self.robots_cache[domain] = rp
        
        return self.robots_cache[domain]
    
    def can_fetch(self, url: str) -> bool:
        try:
            parser = self.get_robots_parser(url)
            return parser.can_fetch(self.user_agent, url)
        except Exception:
            return True
    
    def get_crawl_delay(self, url: str) -> float:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        return self.crawl_delays.get(domain, 1.0)


class WebCrawler:

    def __init__(self, output_dir: str = "corpus/crawled", user_agent: str = "InfoSearchBot/1.0"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_agent = user_agent
        self.robots_parser = RobotsTxtParser(user_agent)
        
        self._setup_logging()
        
        self.state_file = self.output_dir / '.crawler_state.json'
        self._load_state()
        
        self.url_queue: deque = deque()
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        
        self.stats = {
            'total_documents': self.last_doc_id,
            'urls_visited': 0,
            'urls_failed': 0,
            'urls_skipped': 0,
            'documents_saved': 0,
            'start_time': datetime.now().isoformat()
        }
        
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        self.session = self._create_session()
        
        self.max_depth = 3
        self.max_pages_per_domain = 100
        self.min_content_length = 500
        self.domain_page_counts: Dict[str, int] = {}
    
    def _create_session(self) -> requests.Session:
        from requests.adapters import HTTPAdapter
        try:
            from urllib3.util.retry import Retry
        except ImportError:
            from requests.packages.urllib3.util.retry import Retry
        
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update(self.headers)
        
        return session
    
    def _setup_logging(self):
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _load_state(self):
        self.last_doc_id = 0
        self.visited_urls = set()
        
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.last_doc_id = state.get('last_doc_id', 0)
                    self.visited_urls = set(state.get('visited_urls', []))
                logging.info(f"Loaded state: {len(self.visited_urls)} visited URLs, last doc ID: {self.last_doc_id}")
            except Exception as e:
                logging.warning(f"Error loading state file: {e}")
        
        if self.output_dir.exists():
            existing_files = list(self.output_dir.glob('doc_*.txt'))
            if existing_files:
                max_id = 0
                for file in existing_files:
                    try:
                        num_str = file.stem.split('_')[1]
                        doc_id = int(num_str)
                        max_id = max(max_id, doc_id)
                    except (ValueError, IndexError):
                        continue
                
                if max_id > self.last_doc_id:
                    self.last_doc_id = max_id
                    logging.info(f"Found existing documents, last doc ID: {self.last_doc_id}")
    
    def _save_state(self):
        try:
            state = {
                'last_doc_id': self.last_doc_id,
                'visited_urls': list(self.visited_urls),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"Error saving state file: {e}")
    
    def _normalize_url(self, url: str, base_url: str = None) -> str:
        if not url:
            return ""
        
        if base_url:
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            parsed.params,
            '',  # Remove query
            ''   # Remove fragment
        ))
        
        return normalized
    
    def _is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        
        if not parsed.scheme or parsed.scheme not in ['http', 'https']:
            return False
        
        if not parsed.netloc:
            return False
        
        excluded_extensions = ['.pdf', '.doc', '.docx', '.zip', '.rar', '.exe', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi']
        if any(url.lower().endswith(ext) for ext in excluded_extensions):
            return False
        
        return True
    
    def _extract_links(self, html_content: str, base_url: str) -> List[str]:
        links = []
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href:
                    full_url = self._normalize_url(href, base_url)
                    if full_url and self._is_valid_url(full_url):
                        links.append(full_url)
        except Exception as e:
            logging.warning(f"Error extracting links from {base_url}: {e}")
        
        return links
    
    def _extract_content(self, html_content: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            for script in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
                script.decompose()
            
            title = None
            title_elem = soup.find('title') or soup.find('h1')
            if title_elem:
                title = title_elem.get_text().strip()
            
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.main-content',
                '#content',
                '.story-body',
                '.article-body',
                '.b-article__body',
                '.article__text',
                '.news-text'
            ]
            
            text_content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    largest = max(elements, key=lambda x: len(x.get_text()))
                    text_content = largest.get_text()
                    break
            
            if not text_content:
                body = soup.find('body')
                if body:
                    text_content = body.get_text()
            
            if text_content:
                text_content = ' '.join(text_content.split())
                text_content = text_content.strip()
            
            date_str = None
            date_elem = soup.find('time') or soup.find(class_=re.compile('date|time'))
            if date_elem:
                date_str = date_elem.get('datetime', '') or date_elem.get_text()
            
            return title, text_content, date_str
            
        except Exception as e:
            logging.warning(f"Error extracting content: {e}")
            return None, None, None
    
    def _fetch_url(self, url: str, timeout: int = 30) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        except Exception as e:
            logging.warning(f"Error fetching {url}: {e}")
            return None
    
    def _save_document(self, doc_id: int, url: str, title: str, content: str, date: str = None) -> bool:
        try:
            parsed = urlparse(url)
            source = parsed.netloc
            
            text_file = self.output_dir / f"doc_{doc_id:08d}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"TITLE: {title or 'Untitled'}\n")
                f.write(f"SOURCE: {source}\n")
                f.write(f"URL: {url}\n")
                f.write(f"DATE: {date or ''}\n")
                f.write("-" * 80 + "\n")
                f.write("CONTENT:\n")
                f.write(content)
            
            meta_file = self.output_dir / f"doc_{doc_id:08d}.meta.json"
            meta_data = {
                'title': title or 'Untitled',
                'source': source,
                'url': url,
                'date': date or '',
                'text': content,
                'type': 'crawled_web_page'
            }
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logging.error(f"Error saving document {doc_id}: {e}")
            return False
    
    def _get_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc
    
    def crawl(self, seed_urls: List[str], max_pages: int = 100, max_depth: int = 3) -> Dict:
        logging.info(f"Starting crawl with {len(seed_urls)} seed URLs")
        
        self.max_depth = max_depth
        
        for url in seed_urls:
            normalized = self._normalize_url(url)
            if normalized and normalized not in self.visited_urls:
                self.url_queue.append((normalized, 0))
        
        pages_crawled = 0
        
        while self.url_queue and pages_crawled < max_pages:
            if not self.url_queue:
                break
            
            url, depth = self.url_queue.popleft()
            
            if url in self.visited_urls:
                continue
            
            if depth > self.max_depth:
                continue
            
            domain = self._get_domain(url)
            if self.domain_page_counts.get(domain, 0) >= self.max_pages_per_domain:
                continue
            
            if not self.robots_parser.can_fetch(url):
                logging.debug(f"Skipping {url} (robots.txt)")
                self.stats['urls_skipped'] += 1
                continue
            
            self.visited_urls.add(url)
            self.stats['urls_visited'] += 1
            self.domain_page_counts[domain] = self.domain_page_counts.get(domain, 0) + 1
            
            crawl_delay = self.robots_parser.get_crawl_delay(url)
            time.sleep(crawl_delay)
            
            html_content = self._fetch_url(url)
            if not html_content:
                self.failed_urls.add(url)
                self.stats['urls_failed'] += 1
                continue
            
            title, text_content, date_str = self._extract_content(html_content)
            
            if text_content and len(text_content) >= self.min_content_length:
                doc_id = self.last_doc_id + 1
                if self._save_document(doc_id, url, title or 'Untitled', text_content, date_str):
                    self.last_doc_id = doc_id
                    self.stats['documents_saved'] += 1
                    pages_crawled += 1
                    
                    if pages_crawled % 10 == 0:
                        self._save_state()
                        logging.info(f"Crawled {pages_crawled} pages, saved {self.stats['documents_saved']} documents")
            
            if depth < self.max_depth:
                links = self._extract_links(html_content, url)
                for link in links:
                    normalized_link = self._normalize_url(link)
                    if normalized_link and normalized_link not in self.visited_urls:
                        if normalized_link not in [item[0] for item in self.url_queue]:
                            self.url_queue.append((normalized_link, depth + 1))
        
        self._save_state()
        
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['pages_crawled'] = pages_crawled
        
        logging.info(f"Crawl completed: {pages_crawled} pages crawled, {self.stats['documents_saved']} documents saved")
        
        return self.stats
    
    def get_statistics(self) -> Dict:
        return self.stats.copy()
