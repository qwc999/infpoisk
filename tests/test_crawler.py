import unittest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))

try:
    from web_crawler import WebCrawler, RobotsTxtParser
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))
    from web_crawler import WebCrawler, RobotsTxtParser


class TestRobotsTxtParser(unittest.TestCase):

    def setUp(self):
        self.parser = RobotsTxtParser(user_agent='TestBot/1.0')
    
    def test_normalize_url(self):
        crawler = WebCrawler(output_dir=tempfile.mkdtemp())
        self.assertEqual(
            crawler._normalize_url('https://example.com/page'),
            'https://example.com/page'
        )
        self.assertEqual(
            crawler._normalize_url('https://example.com/page/'),
            'https://example.com/page'
        )
        self.assertEqual(
            crawler._normalize_url('https://example.com/page?query=1#fragment'),
            'https://example.com/page'
        )
    
    def test_is_valid_url(self):
        crawler = WebCrawler(output_dir=tempfile.mkdtemp())
        self.assertTrue(crawler._is_valid_url('https://example.com/page'))
        self.assertTrue(crawler._is_valid_url('http://example.com/page'))
        self.assertFalse(crawler._is_valid_url('ftp://example.com/file'))
        self.assertFalse(crawler._is_valid_url('https://example.com/file.pdf'))
        self.assertFalse(crawler._is_valid_url('https://example.com/image.jpg'))


class TestWebCrawler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.crawler = WebCrawler(output_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        self.assertIsNotNone(self.crawler.output_dir)
        self.assertIsNotNone(self.crawler.session)
        self.assertEqual(len(self.crawler.visited_urls), 0)
        self.assertEqual(len(self.crawler.url_queue), 0)
    
    def test_extract_content(self):
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <article>
                    <p>This is test content with enough text to pass minimum length requirement.</p>
                    <p>More content here to make sure we have sufficient length.</p>
                </article>
            </body>
        </html>
        """
        title, content, date = self.crawler._extract_content(html)
        self.assertIsNotNone(title)
        self.assertIsNotNone(content)
        self.assertIn('test content', content.lower())
    
    def test_extract_links(self):
        html = """
        <html>
            <body>
                <a href="/page1">Link 1</a>
                <a href="https://example.com/page2">Link 2</a>
                <a href="mailto:test@example.com">Email</a>
            </body>
        </html>
        """
        base_url = 'https://example.com'
        links = self.crawler._extract_links(html, base_url)
        self.assertGreater(len(links), 0)
        self.assertTrue(any('/page1' in link or 'page1' in link for link in links))
    
    def test_save_document(self):
        doc_id = 1
        url = 'https://example.com/test'
        title = 'Test Document'
        content = 'This is test content with sufficient length to pass validation.'
        content = content * 10
        
        result = self.crawler._save_document(doc_id, url, title, content)
        self.assertTrue(result)
        
        text_file = self.crawler.output_dir / f"doc_{doc_id:08d}.txt"
        meta_file = self.crawler.output_dir / f"doc_{doc_id:08d}.meta.json"
        
        self.assertTrue(text_file.exists())
        self.assertTrue(meta_file.exists())
        
        with open(text_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
            self.assertIn(title, text_content)
            self.assertIn(content, text_content)
    
    def test_state_save_load(self):
        self.crawler.last_doc_id = 5
        self.crawler.visited_urls.add('https://example.com/test')
        self.crawler._save_state()
        
        new_crawler = WebCrawler(output_dir=self.temp_dir)
        self.assertEqual(new_crawler.last_doc_id, 5)
        self.assertIn('https://example.com/test', new_crawler.visited_urls)


class TestCrawlerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.crawler = WebCrawler(output_dir=self.temp_dir)
        self.crawler.min_content_length = 100
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_crawl_single_page(self):
        seed_urls = ['https://httpbin.org/html']
        stats = self.crawler.crawl(seed_urls=seed_urls, max_pages=1, max_depth=1)
        
        self.assertIsNotNone(stats)
        self.assertIn('documents_saved', stats)
        self.assertIn('urls_visited', stats)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestRobotsTxtParser))
    suite.addTests(loader.loadTestsFromTestCase(TestWebCrawler))
    suite.addTests(loader.loadTestsFromTestCase(TestCrawlerIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
