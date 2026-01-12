import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from stemmer import Stemmer
from tokenizer import Tokenizer


def main():
    parser = argparse.ArgumentParser(
        description='Stemmer for Russian and English text'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input file, directory, or tokenized JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output directory for stemmed results (default: stemmed_output)'
    )
    parser.add_argument(
        '--language',
        type=str,
        choices=['russian', 'english'],
        default='russian',
        help='Language for stemming (default: russian)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['text', 'tokens', 'corpus'],
        default='text',
        help='Input mode: text file, tokenized JSON, or corpus directory (default: text)'
    )
    parser.add_argument(
        '--tokenize',
        action='store_true',
        help='Tokenize input text before stemming'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only output statistics, not stem lists'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        return 1
    
    stemmer = Stemmer(language=args.language)
    
    if args.mode == 'corpus' or (input_path.is_dir() and args.mode == 'text'):
        output_dir = Path(args.output) if args.output else Path('stemmed_output')
        print(f"Stemming corpus: {input_path}")
        print(f"Language: {args.language}")
        print(f"Output directory: {output_dir}")
        print("-" * 80)

        tokenized_dir = input_path / 'tokenized_documents'
        if tokenized_dir.exists():
            corpus_tokens = {}
            for json_file in tokenized_dir.glob('*_tokens.json'):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    doc_id = data.get('document_id', json_file.stem)
                    tokens = data.get('tokens', [])
                    corpus_tokens[doc_id] = tokens
        else:
            print("Tokenizing corpus first...")
            tokenizer = Tokenizer(lowercase=True, min_length=1)
            corpus_stats = tokenizer.tokenize_corpus(input_path)
            
            if 'error' in corpus_stats:
                print(f"Error: {corpus_stats['error']}")
                return 1
            
            corpus_tokens = {}
            for doc_stat in corpus_stats['document_stats']:
                if 'error' not in doc_stat:
                    corpus_tokens[doc_stat['document_id']] = doc_stat['tokens']
        
        stats = stemmer.process_corpus(corpus_tokens, output_dir)
        
        print("-" * 80)
        print("STEMMING STATISTICS:")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total stems: {stats['total_stems']}")
        print(f"Unique stems: {stats['unique_stems']}")
        print(f"Average stems per document: {stats['total_stems'] / stats['total_documents']:.2f}")
        
        if not args.stats_only:
            print("\nTop 20 most frequent stems:")
            sorted_freq = sorted(stats['corpus_stem_frequencies'].items(), 
                                key=lambda x: x[1], reverse=True)
            for stem, freq in sorted_freq[:20]:
                print(f"  {stem}: {freq}")
        
        print(f"\nResults saved to: {output_dir}")
        
    elif args.mode == 'tokens':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tokens = data.get('tokens', [])
        if not tokens:
            print("Error: No tokens found in input file")
            return 1
        
        print(f"Stemming {len(tokens)} tokens")
        print(f"Language: {args.language}")
        print("-" * 80)
        
        result = stemmer.process_document(tokens)
        
        print(f"Total stems: {result['total_stems']}")
        print(f"Unique stems: {result['unique_stems']}")
        
        if not args.stats_only:
            print(f"\nFirst 50 stems:")
            print(' '.join(result['stems'][:50]))
            
            print(f"\nTop 20 most frequent stems:")
            sorted_freq = sorted(result['stem_frequencies'].items(), 
                                key=lambda x: x[1], reverse=True)
            for stem, freq in sorted_freq[:20]:
                print(f"  {stem}: {freq}")

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_path}")
    
    else:
        print(f"Stemming file: {input_path}")
        print(f"Language: {args.language}")
        print("-" * 80)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if args.tokenize:
            tokenizer = Tokenizer(lowercase=True, min_length=1)
            tokens = tokenizer.tokenize(text)
            print(f"Tokenized into {len(tokens)} tokens")
        else:
            tokens = text.split()
        
        result = stemmer.process_document(tokens)
        
        print(f"Total stems: {result['total_stems']}")
        print(f"Unique stems: {result['unique_stems']}")
        
        if not args.stats_only:
            print(f"\nFirst 50 stems:")
            print(' '.join(result['stems'][:50]))
            
            print(f"\nTop 20 most frequent stems:")
            sorted_freq = sorted(result['stem_frequencies'].items(), 
                                key=lambda x: x[1], reverse=True)
            for stem, freq in sorted_freq[:20]:
                print(f"  {stem}: {freq}")
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
