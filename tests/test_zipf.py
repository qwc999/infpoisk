import unittest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))

try:
    from zipf_analyzer import ZipfAnalyzer
    from tokenizer import Tokenizer
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))
    from zipf_analyzer import ZipfAnalyzer
    from tokenizer import Tokenizer


class TestZipfAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = ZipfAnalyzer()
    
    def test_calculate_frequencies(self):
        tokens = ['cat', 'dog', 'cat', 'bird', 'cat', 'dog']
        frequencies = self.analyzer.calculate_frequencies(tokens)
        
        self.assertEqual(frequencies['cat'], 3)
        self.assertEqual(frequencies['dog'], 2)
        self.assertEqual(frequencies['bird'], 1)
        self.assertEqual(self.analyzer.total_tokens, 6)
        self.assertEqual(self.analyzer.unique_tokens, 3)
    
    def test_get_ranked_frequencies(self):
        tokens = ['cat', 'dog', 'cat', 'bird', 'cat', 'dog']
        self.analyzer.calculate_frequencies(tokens)
        ranked = self.analyzer.get_ranked_frequencies()
        
        self.assertEqual(len(ranked), 3)
        # First should be 'cat' with rank 1
        self.assertEqual(ranked[0][1], 'cat')
        self.assertEqual(ranked[0][0], 1)
        self.assertEqual(ranked[0][2], 3)
    
    def test_calculate_zipf_constant(self):
        tokens = ['cat', 'dog', 'cat', 'bird', 'cat', 'dog']
        self.analyzer.calculate_frequencies(tokens)
        self.analyzer.get_ranked_frequencies()
        
        constant = self.analyzer.calculate_zipf_constant()
        self.assertEqual(constant, 3.0)
    
    def test_calculate_zipf_predicted(self):
        tokens = ['cat', 'dog', 'cat', 'bird', 'cat', 'dog']
        self.analyzer.calculate_frequencies(tokens)
        self.analyzer.get_ranked_frequencies()
        
        constant = self.analyzer.calculate_zipf_constant()
        predicted = self.analyzer.calculate_zipf_predicted(1, constant)

        self.assertEqual(predicted, constant)

        predicted2 = self.analyzer.calculate_zipf_predicted(2, constant)
        self.assertEqual(predicted2, constant / 2)
    
    def test_calculate_correlation(self):

        tokens = ['a'] * 10 + ['b'] * 5 + ['c'] * 3 + ['d'] * 2 + ['e'] * 1
        self.analyzer.calculate_frequencies(tokens)
        self.analyzer.get_ranked_frequencies()
        
        correlation = self.analyzer.calculate_correlation()

        self.assertGreaterEqual(correlation, -1.0)
        self.assertLessEqual(correlation, 1.0)
    
    def test_get_statistics(self):
        tokens = ['cat', 'dog', 'cat', 'bird', 'cat', 'dog']
        self.analyzer.calculate_frequencies(tokens)
        self.analyzer.get_ranked_frequencies()
        
        stats = self.analyzer.get_statistics()
        
        self.assertIn('total_tokens', stats)
        self.assertIn('unique_tokens', stats)
        self.assertIn('zipf_constant', stats)
        self.assertIn('correlation', stats)
        self.assertIn('top_words', stats)
        self.assertIn('ranked_frequencies', stats)
        
        self.assertEqual(stats['total_tokens'], 6)
        self.assertEqual(stats['unique_tokens'], 3)
        self.assertEqual(len(stats['top_words']), 3)  # All 3 words
    
    def test_empty_tokens(self):
        frequencies = self.analyzer.calculate_frequencies([])
        self.assertEqual(len(frequencies), 0)
        self.assertEqual(self.analyzer.total_tokens, 0)
        
        ranked = self.analyzer.get_ranked_frequencies()
        self.assertEqual(len(ranked), 0)
        
        constant = self.analyzer.calculate_zipf_constant()
        self.assertEqual(constant, 0.0)


class TestZipfAnalyzerIntegration(unittest.TestCase):
    
    def test_with_tokenizer(self):
        tokenizer = Tokenizer(lowercase=True, min_length=1)
        analyzer = ZipfAnalyzer()
        
        text = "The cat sat on the mat. The cat was happy."
        tokens = tokenizer.tokenize(text)
        
        analyzer.calculate_frequencies(tokens)
        analyzer.get_ranked_frequencies()
        stats = analyzer.get_statistics()
        
        self.assertGreater(stats['total_tokens'], 0)
        self.assertGreater(stats['unique_tokens'], 0)
        self.assertGreater(stats['zipf_constant'], 0)
    
    def test_analyze_corpus(self):
        temp_dir = tempfile.mkdtemp()
        output_dir = Path(temp_dir) / "output"
        
        try:
            corpus_tokens = {
                'doc1': ['cat', 'dog', 'cat', 'bird'],
                'doc2': ['cat', 'dog', 'fish', 'cat'],
                'doc3': ['bird', 'cat', 'dog', 'bird']
            }
            
            analyzer = ZipfAnalyzer()
            stats = analyzer.analyze_corpus(corpus_tokens, output_dir)
            
            self.assertIn('total_tokens', stats)
            self.assertIn('unique_tokens', stats)
            self.assertIn('zipf_constant', stats)
            self.assertIn('correlation', stats)
            self.assertIn('top_words', stats)

            expected_total = sum(len(tokens) for tokens in corpus_tokens.values())
            self.assertEqual(stats['total_tokens'], expected_total)

            if output_dir.exists():
                stats_file = output_dir / 'zipf_statistics.json'
                self.assertTrue(output_dir.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestZipfLawValidation(unittest.TestCase):
    
    def test_zipf_law_approximation(self):
        tokens = []
        for i in range(1, 11):
            word = f'word{i}'
            freq = int(100 / i)
            tokens.extend([word] * freq)
        
        analyzer = ZipfAnalyzer()
        analyzer.calculate_frequencies(tokens)
        analyzer.get_ranked_frequencies()
        
        correlation = analyzer.calculate_correlation()
        self.assertGreater(correlation, 0.5)
    
    def test_rank_order(self):
        tokens = ['a'] * 10 + ['b'] * 5 + ['c'] * 3 + ['d'] * 2
        analyzer = ZipfAnalyzer()
        analyzer.calculate_frequencies(tokens)
        ranked = analyzer.get_ranked_frequencies()

        for i in range(len(ranked) - 1):
            self.assertGreaterEqual(ranked[i][2], ranked[i+1][2])


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestZipfAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestZipfAnalyzerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestZipfLawValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
