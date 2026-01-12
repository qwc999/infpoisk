import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from boolean_search import BooleanSearchEngine
from boolean_index import BooleanIndex


def main():
    parser = argparse.ArgumentParser(
        description='Boolean search engine for information retrieval system'
    )
    
    parser.add_argument(
        '--index',
        type=str,
        required=True,
        help='Path to boolean index file'
    )
    parser.add_argument(
        '--query',
        type=str,
        default=None,
        help='Search query'
    )
    parser.add_argument(
        '--query-file',
        type=str,
        default=None,
        help='File with search queries (one per line)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for results (JSON format)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of results to return'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive search mode'
    )
    
    args = parser.parse_args()

    index_path = Path(args.index)
    if not index_path.exists():
        print(f"Error: Index file does not exist: {index_path}")
        return 1
    
    print(f"Loading index from: {index_path}")
    engine = BooleanSearchEngine(index_path=index_path)
    print(f"Index loaded: {engine.index.stats['total_documents']} documents, "
          f"{engine.index.stats['total_terms']} terms")
    print("-" * 80)

    if args.interactive:
        print("Interactive search mode (type 'quit' to exit)")
        print("Example queries:")
        print("  cat AND dog")
        print("  cat OR dog")
        print("  cat AND NOT dog")
        print("  (cat OR dog) AND bird")
        print("-" * 80)
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                if not query or query.lower() in ('quit', 'exit', 'q'):
                    break
                
                result = engine.search(query, limit=args.limit)
                
                print(f"\nResults: {result['result_count']} documents found")
                
                if result['results']:
                    print("\nDocument IDs:")
                    doc_ids = [r['doc_id'] for r in result['results']]
                    print(doc_ids[:50])
                    if len(doc_ids) > 50:
                        print(f"... (and {len(doc_ids) - 50} more)")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        return 0

    if args.query_file:
        query_file = Path(args.query_file)
        if not query_file.exists():
            print(f"Error: Query file does not exist: {query_file}")
            return 1
        
        print(f"Processing queries from: {query_file}")
        print("-" * 80)
        
        all_results = []
        with open(query_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}/{len(queries)}: {query}")
            result = engine.search(query, limit=args.limit)
            
            print(f"  Results: {result['result_count']} documents")
            
            all_results.append(result)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_path}")
        
        return 0

    if args.query:
        print(f"Query: {args.query}")
        print("-" * 80)
        
        result = engine.search(args.query, limit=args.limit)
        
        print(f"Results: {result['result_count']} documents found")
        
        if result['results']:
            print("\nDocument IDs:")
            doc_ids = [r['doc_id'] for r in result['results']]
            print(doc_ids[:50])
            if len(doc_ids) > 50:
                print(f"... (and {len(doc_ids) - 50} more)")

            print("\nFirst 10 results:")
            for res in result['results'][:10]:
                doc_id = res['doc_id']
                metadata = res.get('metadata', {})
                title = metadata.get('title', 'No title')
                print(f"  Document {doc_id}: {title}")

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_path}")
        
        return 0
    
    print("Error: No query specified. Use --query, --query-file, or --interactive")
    return 1


if __name__ == '__main__':
    sys.exit(main())
