import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from web_crawler import WebCrawler


def main():
    parser = argparse.ArgumentParser(
        description='Web crawler for information retrieval system'
    )
    parser.add_argument(
        '--seed-urls',
        type=str,
        nargs='+',
        required=True,
        help='Seed URLs to start crawling from'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='Maximum number of pages to crawl (default: 100)'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=3,
        help='Maximum crawl depth (default: 3)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='corpus/crawled',
        help='Output directory for crawled documents (default: corpus/crawled)'
    )
    parser.add_argument(
        '--min-content-length',
        type=int,
        default=500,
        help='Minimum content length in characters (default: 500)'
    )
    parser.add_argument(
        '--user-agent',
        type=str,
        default='InfoSearchBot/1.0',
        help='User agent string (default: InfoSearchBot/1.0)'
    )
    parser.add_argument(
        '--stats-output',
        type=str,
        default=None,
        help='Output file for statistics (JSON format)'
    )
    
    args = parser.parse_args()
    
    crawler = WebCrawler(
        output_dir=args.output,
        user_agent=args.user_agent
    )
    crawler.min_content_length = args.min_content_length
    
    print(f"Starting crawl with {len(args.seed_urls)} seed URLs")
    print(f"Max pages: {args.max_pages}, Max depth: {args.max_depth}")
    print(f"Output directory: {args.output}")
    print("-" * 80)
    
    stats = crawler.crawl(
        seed_urls=args.seed_urls,
        max_pages=args.max_pages,
        max_depth=args.max_depth
    )
    
    print("-" * 80)
    print("CRAWL STATISTICS:")
    print(f"Total documents saved: {stats['documents_saved']}")
    print(f"URLs visited: {stats['urls_visited']}")
    print(f"URLs failed: {stats['urls_failed']}")
    print(f"URLs skipped: {stats['urls_skipped']}")
    print(f"Pages crawled: {stats.get('pages_crawled', 0)}")
    print(f"Start time: {stats.get('start_time', 'N/A')}")
    print(f"End time: {stats.get('end_time', 'N/A')}")
    
    if args.stats_output:
        with open(args.stats_output, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"Statistics saved to: {args.stats_output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
