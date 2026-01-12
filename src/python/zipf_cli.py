import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from zipf_analyzer import ZipfAnalyzer
from tokenizer import Tokenizer


def main():
    parser = argparse.ArgumentParser(
        description="Zipf's Law analyzer for text corpus"
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
        help='Output directory for analysis results (default: zipf_output)'
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
        help='Tokenize input text before analysis'
    )
    parser.add_argument(
        '--max-rank',
        type=int,
        default=1000,
        help='Maximum rank for plotting (default: 1000)'
    )
    parser.add_argument(
        '--no-plot',
        action='store_true',
        help='Do not generate plots'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        return 1
    
    analyzer = ZipfAnalyzer()
    output_dir = Path(args.output) if args.output else Path('zipf_output')
    
    if args.mode == 'corpus' or (input_path.is_dir() and args.mode == 'text'):
        print(f"Analyzing Zipf's Law for corpus: {input_path}")
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
        
        stats = analyzer.analyze_corpus(corpus_tokens, output_dir if not args.no_plot else None)
        
        print("-" * 80)
        print("ZIPF'S LAW STATISTICS:")
        print(f"Total tokens: {stats['total_tokens']:,}")
        print(f"Unique tokens: {stats['unique_tokens']:,}")
        print(f"Zipf constant (C): {stats['zipf_constant']:.2f}")
        print(f"Correlation with Zipf's Law: {stats['correlation']:.4f}")
        
        print("\nTop 10 words:")
        for word_info in stats['top_words']:
            print(f"  Rank {word_info['rank']:4d}: {word_info['token']:20s} "
                  f"Frequency: {word_info['frequency']:6d} "
                  f"({word_info['relative_frequency']*100:.2f}%)")
        
        if not args.no_plot and 'plots' in stats and stats['plots']:
            print(f"\nPlots saved:")
            for plot_path in stats['plots']:
                print(f"  {plot_path}")
        
        print(f"\nResults saved to: {output_dir}")
        
    elif args.mode == 'tokens':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tokens = data.get('tokens', [])
        if not tokens:
            print("Error: No tokens found in input file")
            return 1
        
        print(f"Analyzing Zipf's Law for {len(tokens)} tokens")
        print("-" * 80)
        
        analyzer.calculate_frequencies(tokens)
        analyzer.get_ranked_frequencies()
        stats = analyzer.get_statistics()
        
        print(f"Total tokens: {stats['total_tokens']:,}")
        print(f"Unique tokens: {stats['unique_tokens']:,}")
        print(f"Zipf constant (C): {stats['zipf_constant']:.2f}")
        print(f"Correlation with Zipf's Law: {stats['correlation']:.4f}")
        
        print("\nTop 10 words:")
        for word_info in stats['top_words']:
            print(f"  Rank {word_info['rank']:4d}: {word_info['token']:20s} "
                  f"Frequency: {word_info['frequency']:6d} "
                  f"({word_info['relative_frequency']*100:.2f}%)")
        
        if not args.no_plot:
            try:
                plot1 = analyzer.plot_zipf_law(output_dir / 'zipf_law_plot.png', max_rank=args.max_rank)
                plot2 = analyzer.plot_rank_frequency(output_dir / 'zipf_rank_frequency.png', max_rank=100)
                print(f"\nPlots saved:")
                print(f"  {plot1}")
                print(f"  {plot2}")
            except ImportError:
                print("\nWarning: matplotlib not available, plots not generated")

        stats_file = output_dir / 'zipf_statistics.json'
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"\nStatistics saved to: {stats_file}")
    
    else:
        print(f"Analyzing Zipf's Law for file: {input_path}")
        print("-" * 80)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if args.tokenize:
            tokenizer = Tokenizer(lowercase=True, min_length=1)
            tokens = tokenizer.tokenize(text)
            print(f"Tokenized into {len(tokens)} tokens")
        else:
            tokens = text.split()
        
        analyzer.calculate_frequencies(tokens)
        analyzer.get_ranked_frequencies()
        stats = analyzer.get_statistics()
        
        print(f"Total tokens: {stats['total_tokens']:,}")
        print(f"Unique tokens: {stats['unique_tokens']:,}")
        print(f"Zipf constant (C): {stats['zipf_constant']:.2f}")
        print(f"Correlation with Zipf's Law: {stats['correlation']:.4f}")
        
        print("\nTop 10 words:")
        for word_info in stats['top_words']:
            print(f"  Rank {word_info['rank']:4d}: {word_info['token']:20s} "
                  f"Frequency: {word_info['frequency']:6d} "
                  f"({word_info['relative_frequency']*100:.2f}%)")
        
        if not args.no_plot:
            try:
                plot1 = analyzer.plot_zipf_law(output_dir / 'zipf_law_plot.png', max_rank=args.max_rank)
                plot2 = analyzer.plot_rank_frequency(output_dir / 'zipf_rank_frequency.png', max_rank=100)
                print(f"\nPlots saved:")
                print(f"  {plot1}")
                print(f"  {plot2}")
            except ImportError:
                print("\nWarning: matplotlib not available, plots not generated")

        stats_file = output_dir / 'zipf_statistics.json'
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"\nStatistics saved to: {stats_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
