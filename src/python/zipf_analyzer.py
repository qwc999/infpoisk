import json
import math
from typing import List, Dict, Tuple
from pathlib import Path
from collections import Counter

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ZipfAnalyzer:

    def __init__(self):
        self.frequencies = {}
        self.ranked_frequencies = []
        self.total_tokens = 0
        self.unique_tokens = 0
    
    def calculate_frequencies(self, tokens: List[str]) -> Dict[str, int]:
        self.frequencies = Counter(tokens)
        self.total_tokens = len(tokens)
        self.unique_tokens = len(self.frequencies)
        
        return dict(self.frequencies)
    
    def get_ranked_frequencies(self) -> List[Tuple[int, str, int, float]]:
        if not self.frequencies:
            return []

        sorted_items = sorted(self.frequencies.items(), key=lambda x: x[1], reverse=True)
        
        self.ranked_frequencies = []
        for rank, (token, freq) in enumerate(sorted_items, start=1):
            relative_freq = freq / self.total_tokens if self.total_tokens > 0 else 0
            self.ranked_frequencies.append((rank, token, freq, relative_freq))
        
        return self.ranked_frequencies
    
    def calculate_zipf_constant(self) -> float:
        if not self.ranked_frequencies:
            self.get_ranked_frequencies()
        
        if not self.ranked_frequencies:
            return 0.0

        rank, token, freq, _ = self.ranked_frequencies[0]
        return freq * rank
    
    def calculate_zipf_predicted(self, rank: int, constant: float = None) -> float:
        if constant is None:
            constant = self.calculate_zipf_constant()
        
        if constant == 0 or rank == 0:
            return 0.0
        
        return constant / rank
    
    def calculate_correlation(self) -> float:
        if not self.ranked_frequencies:
            self.get_ranked_frequencies()
        
        if len(self.ranked_frequencies) < 2:
            return 0.0
        
        constant = self.calculate_zipf_constant()
        
        actual_freqs = [freq for _, _, freq, _ in self.ranked_frequencies]
        predicted_freqs = [self.calculate_zipf_predicted(rank, constant) 
                          for rank, _, _, _ in self.ranked_frequencies]

        n = len(actual_freqs)
        if n < 2:
            return 0.0
        
        mean_actual = sum(actual_freqs) / n
        mean_predicted = sum(predicted_freqs) / n
        
        numerator = sum((a - mean_actual) * (p - mean_predicted) 
                       for a, p in zip(actual_freqs, predicted_freqs))
        
        sum_sq_actual = sum((a - mean_actual) ** 2 for a in actual_freqs)
        sum_sq_predicted = sum((p - mean_predicted) ** 2 for p in predicted_freqs)
        
        denominator = math.sqrt(sum_sq_actual * sum_sq_predicted)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def get_statistics(self) -> Dict:
        if not self.ranked_frequencies:
            self.get_ranked_frequencies()
        
        constant = self.calculate_zipf_constant()
        correlation = self.calculate_correlation()

        top_words = [
            {'rank': rank, 'token': token, 'frequency': freq, 'relative_frequency': rel_freq}
            for rank, token, freq, rel_freq in self.ranked_frequencies[:10]
        ]
        
        return {
            'total_tokens': self.total_tokens,
            'unique_tokens': self.unique_tokens,
            'zipf_constant': constant,
            'correlation': correlation,
            'top_words': top_words,
            'ranked_frequencies': [
                {'rank': rank, 'token': token, 'frequency': freq, 'relative_frequency': rel_freq}
                for rank, token, freq, rel_freq in self.ranked_frequencies
            ]
        }
    
    def plot_zipf_law(self, output_path: Path = None, max_rank: int = 1000) -> str:
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib is required for plotting")
        
        if not self.ranked_frequencies:
            self.get_ranked_frequencies()
        
        if not self.ranked_frequencies:
            raise ValueError("No data to plot")

        data = self.ranked_frequencies[:max_rank]
        
        ranks = [rank for rank, _, _, _ in data]
        frequencies = [freq for _, _, freq, _ in data]
        constant = self.calculate_zipf_constant()
        predicted = [self.calculate_zipf_predicted(rank, constant) for rank in ranks]

        plt.figure(figsize=(12, 8))

        plt.loglog(ranks, frequencies, 'b-', alpha=0.7, linewidth=2, label='Actual frequencies')

        plt.loglog(ranks, predicted, 'r--', alpha=0.7, linewidth=2, label="Zipf's Law prediction")
        
        plt.xlabel('Rank (log scale)', fontsize=12)
        plt.ylabel('Frequency (log scale)', fontsize=12)
        plt.title("Zipf's Law Analysis", fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)

        stats_text = f'Total tokens: {self.total_tokens:,}\n'
        stats_text += f'Unique tokens: {self.unique_tokens:,}\n'
        stats_text += f'Zipf constant: {constant:.2f}\n'
        stats_text += f'Correlation: {self.calculate_correlation():.4f}'
        
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()

        if output_path is None:
            output_path = Path('zipf_plot.png')
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def plot_rank_frequency(self, output_path: Path = None, max_rank: int = 100) -> str:
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib is required for plotting")
        
        if not self.ranked_frequencies:
            self.get_ranked_frequencies()
        
        if not self.ranked_frequencies:
            raise ValueError("No data to plot")

        data = self.ranked_frequencies[:max_rank]
        
        ranks = [rank for rank, _, _, _ in data]
        frequencies = [freq for _, _, freq, _ in data]
        constant = self.calculate_zipf_constant()
        predicted = [self.calculate_zipf_predicted(rank, constant) for rank in ranks]

        plt.figure(figsize=(12, 6))
        
        plt.plot(ranks, frequencies, 'b-o', markersize=4, alpha=0.7, label='Actual frequencies')
        plt.plot(ranks, predicted, 'r--', linewidth=2, alpha=0.7, label="Zipf's Law prediction")
        
        plt.xlabel('Rank', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.title(f"Zipf's Law: Top {max_rank} Words", fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()

        if output_path is None:
            output_path = Path('zipf_rank_frequency.png')
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def analyze_corpus(self, corpus_tokens: Dict[str, List[str]], output_dir: Path = None) -> Dict:
        all_tokens = []
        for tokens in corpus_tokens.values():
            all_tokens.extend(tokens)

        self.calculate_frequencies(all_tokens)
        self.get_ranked_frequencies()

        stats = self.get_statistics()

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            stats_file = output_dir / 'zipf_statistics.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

            try:
                plot1 = self.plot_zipf_law(output_dir / 'zipf_law_plot.png')
                plot2 = self.plot_rank_frequency(output_dir / 'zipf_rank_frequency.png', max_rank=100)
                stats['plots'] = [plot1, plot2]
            except ImportError:
                stats['plots'] = []
                stats['plot_error'] = 'matplotlib not available'
        
        return stats
