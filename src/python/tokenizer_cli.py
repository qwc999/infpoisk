import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tokenizer import Tokenizer


def main():
    parser = argparse.ArgumentParser(
        description='Tokenizer for Russian and English text'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input file or directory (corpus directory for batch processing)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output directory for tokenized results (default: tokenized_output)'
    )
    parser.add_argument(
        '--lowercase',
        action='store_true',
        default=True,
        help='Convert tokens to lowercase (default: True)'
    )
    parser.add_argument(
        '--no-lowercase',
        action='store_false',
        dest='lowercase',
        help='Do not convert tokens to lowercase'
    )
    parser.add_argument(
        '--remove-punctuation',
        action='store_true',
        help='Remove punctuation from tokens'
    )
    parser.add_argument(
        '--min-length',
        type=int,
        default=1,
        help='Minimum token length (default: 1)'
    )
    parser.add_argument(
        '--remove-stopwords',
        action='store_true',
        help='Remove stop words'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['single', 'corpus'],
        default='single',
        help='Processing mode: single file or corpus (default: single)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only output statistics, not token lists'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        return 1
    
    tokenizer = Tokenizer(
        lowercase=args.lowercase,
        remove_punctuation=args.remove_punctuation,
        min_length=args.min_length,
        remove_stopwords=args.remove_stopwords
    )
    
    if args.mode == 'corpus' or input_path.is_dir():
        output_dir = Path(args.output) if args.output else Path('tokenized_output')
        print(f"Tokenizing corpus: {input_path}")
        print(f"Output directory: {output_dir}")
        print("-" * 80)
        
        stats = tokenizer.tokenize_corpus(input_path, output_dir)
        
        if 'error' in stats:
            print(f"Error: {stats['error']}")
            return 1
        
        print("-" * 80)
        print("TOKENIZATION STATISTICS:")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"Unique tokens: {stats['unique_tokens']}")
        print(f"Average tokens per document: {stats['total_tokens'] / stats['total_documents']:.2f}")
        
        if not args.stats_only:
            print("\nTop 20 most frequent tokens:")
            sorted_freq = sorted(stats['corpus_frequencies'].items(), 
                                key=lambda x: x[1], reverse=True)
            for token, freq in sorted_freq[:20]:
                print(f"  {token}: {freq}")
        
        print(f"\nResults saved to: {output_dir}")
        
    else:
        print(f"Tokenizing file: {input_path}")
        print("-" * 80)
        
        result = tokenizer.tokenize_document(input_path)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            return 1
        
        print(f"Document ID: {result['document_id']}")
        print(f"Total tokens: {result['total_tokens']}")
        print(f"Unique tokens: {result['unique_tokens']}")
        
        if not args.stats_only:
            print(f"\nFirst 50 tokens:")
            print(' '.join(result['tokens'][:50]))
            
            print(f"\nTop 20 most frequent tokens:")
            sorted_freq = sorted(result['frequencies'].items(), 
                                key=lambda x: x[1], reverse=True)
            for token, freq in sorted_freq[:20]:
                print(f"  {token}: {freq}")

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
