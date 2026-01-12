import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from boolean_index import BooleanIndex
from tokenizer import Tokenizer
from stemmer import Stemmer


def main():
    parser = argparse.ArgumentParser(
        description='Boolean index builder for information retrieval system'
    )
    
    parser.add_argument(
        '--corpus',
        type=str,
        required=True,
        help='Corpus directory containing documents'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='boolean_index.json',
        help='Output file for index (default: boolean_index.json)'
    )
    parser.add_argument(
        '--text-output',
        type=str,
        default=None,
        help='Output file for human-readable text format'
    )
    parser.add_argument(
        '--use-stemming',
        action='store_true',
        help='Use stemming for terms'
    )
    parser.add_argument(
        '--language',
        type=str,
        choices=['russian', 'english'],
        default='russian',
        help='Language for stemming (default: russian)'
    )
    parser.add_argument(
        '--remove-stopwords',
        action='store_true',
        help='Remove stop words during tokenization'
    )
    parser.add_argument(
        '--query',
        type=str,
        default=None,
        help='Query term to search in index'
    )
    parser.add_argument(
        '--load',
        type=str,
        default=None,
        help='Load existing index from file instead of building'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show index statistics'
    )
    
    args = parser.parse_args()
    
    index = BooleanIndex()
    
    if args.load:
        print(f"Loading index from: {args.load}")
        index.load(Path(args.load))
        print(f"Loaded index with {index.stats['total_documents']} documents")
    else:
        corpus_dir = Path(args.corpus)
        if not corpus_dir.exists():
            print(f"Error: Corpus directory does not exist: {corpus_dir}")
            return 1
        
        print(f"Building boolean index from corpus: {corpus_dir}")

        tokenizer = Tokenizer(
            lowercase=True,
            min_length=1,
            remove_stopwords=args.remove_stopwords
        )

        stemmer = None
        if args.use_stemming:
            stemmer = Stemmer(language=args.language)
            print(f"Using stemming (language: {args.language})")

        build_stats = index.build_from_corpus(corpus_dir, tokenizer, stemmer)
        
        print("-" * 80)
        print("INDEX BUILD STATISTICS:")
        print(f"Documents processed: {build_stats['documents_processed']}")
        print(f"Errors: {build_stats['errors']}")
        print(f"Total documents in index: {build_stats['index_statistics']['total_documents']}")
        print(f"Total terms: {build_stats['index_statistics']['total_terms']}")
        print(f"Index size: {build_stats['index_statistics']['index_size']}")
        print(f"Average terms per document: {build_stats['index_statistics']['average_terms_per_document']:.2f}")

        output_path = Path(args.output)
        index.save(output_path)
        print(f"\nIndex saved to: {output_path}")

        if args.text_output:
            text_path = Path(args.text_output)
            index.export_to_text(text_path, max_terms=100)
            print(f"Text export saved to: {text_path}")

    if args.stats:
        stats = index.get_index_statistics()
        print("\n" + "=" * 80)
        print("INDEX STATISTICS:")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total terms: {stats['total_terms']}")
        print(f"Index size: {stats['index_size']}")
        print(f"Average terms per document: {stats['average_terms_per_document']:.2f}")
        
        print("\nTop 20 terms by document frequency:")
        for term_info in stats['top_terms']:
            print(f"  {term_info['term']:30s} {term_info['document_frequency']:6d} documents")

    if args.query:
        print("\n" + "=" * 80)
        print(f"QUERY: '{args.query}'")
        
        doc_ids = index.get_documents(args.query)
        doc_count = len(doc_ids)
        
        print(f"Found in {doc_count} documents")
        
        if doc_count > 0:
            doc_list = sorted(list(doc_ids))
            print(f"Document IDs: {doc_list[:50]}")
            if len(doc_list) > 50:
                print(f"... (and {len(doc_list) - 50} more)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
