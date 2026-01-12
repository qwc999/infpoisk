import unittest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))

try:
    from tokenizer import Tokenizer
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))
    from tokenizer import Tokenizer


class TestTokenizer(unittest.TestCase):
    
    def setUp(self):
        self.tokenizer = Tokenizer()
    
    def test_basic_tokenization(self):
        text = "Hello world! This is a test."
        tokens = self.tokenizer.tokenize(text)
        self.assertGreater(len(tokens), 0)
        self.assertIn('hello', tokens)
        self.assertIn('world', tokens)
        self.assertIn('test', tokens)
    
    def test_russian_tokenization(self):
        text = "Привет мир! Это теѝтовый текѝт."
        tokens = self.tokenizer.tokenize(text)
        self.assertGreater(len(tokens), 0)
        self.assertIn('привет', tokens)
        self.assertIn('мир', tokens)
        self.assertIn('теѝтовый', tokens)
    
    def test_lowercase(self):
        tokenizer = Tokenizer(lowercase=True)
        text = "Hello WORLD Test"
        tokens = tokenizer.tokenize(text)
        self.assertTrue(all(token.islower() for token in tokens))
        
        tokenizer = Tokenizer(lowercase=False)
        tokens = tokenizer.tokenize(text)
        self.assertTrue(any(not token.islower() for token in tokens))
    
    def test_min_length(self):
        tokenizer = Tokenizer(min_length=3)
        text = "a an the cat dog"
        tokens = tokenizer.tokenize(text)
        self.assertTrue(all(len(token) >= 3 for token in tokens))
        self.assertNotIn('a', tokens)
        self.assertNotIn('an', tokens)
        self.assertIn('cat', tokens)
        self.assertIn('dog', tokens)
    
    def test_remove_stopwords(self):
        tokenizer = Tokenizer(remove_stopwords=True)
        text = "the cat and the dog"
        tokens = tokenizer.tokenize(text)
        self.assertNotIn('the', tokens)
        self.assertNotIn('and', tokens)
        self.assertIn('cat', tokens)
        self.assertIn('dog', tokens)
    
    def test_numbers(self):
        text = "The year is 2025 and the price is 100 dollars"
        tokens = self.tokenizer.tokenize(text)
        self.assertIn('2025', tokens)
        self.assertIn('100', tokens)
    
    def test_punctuation(self):
        text = "Hello, world! How are you?"
        tokens = self.tokenizer.tokenize(text)
        self.assertIn('hello', tokens)
        self.assertIn('world', tokens)
        self.assertIn('how', tokens)
    
    def test_mixed_languages(self):
        text = "Hello мир! This is теѝт."
        tokens = self.tokenizer.tokenize(text)
        self.assertIn('hello', tokens)
        self.assertIn('мир', tokens)
        self.assertIn('this', tokens)
        self.assertIn('теѝт', tokens)
    
    def test_empty_text(self):
        tokens = self.tokenizer.tokenize("")
        self.assertEqual(len(tokens), 0)
        
        tokens = self.tokenizer.tokenize("   ")
        self.assertEqual(len(tokens), 0)
    
    def test_token_frequencies(self):
        text = "cat dog cat bird dog cat"
        tokens = self.tokenizer.tokenize(text)
        frequencies = self.tokenizer.get_token_frequencies(tokens)
        
        self.assertEqual(frequencies['cat'], 3)
        self.assertEqual(frequencies['dog'], 2)
        self.assertEqual(frequencies['bird'], 1)
    
    def test_vocabulary(self):
        text = "cat dog cat bird dog"
        tokens = self.tokenizer.tokenize(text)
        vocabulary = self.tokenizer.get_vocabulary(tokens)
        
        self.assertEqual(len(vocabulary), 3)
        self.assertIn('cat', vocabulary)
        self.assertIn('dog', vocabulary)
        self.assertIn('bird', vocabulary)
    
    def test_document_tokenization(self):
        temp_dir = tempfile.mkdtemp()
        try:
            doc_file = Path(temp_dir) / "test_doc.txt"
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write("TITLE: Test Document\n")
                f.write("SOURCE: Test\n")
                f.write("-" * 80 + "\n")
                f.write("CONTENT:\n")
                f.write("This is a test document. It contains multiple sentences.")
            
            result = self.tokenizer.tokenize_document(doc_file)
            
            self.assertIn('document_id', result)
            self.assertGreater(result['total_tokens'], 0)
            self.assertGreater(result['unique_tokens'], 0)
            self.assertIn('tokens', result)
            self.assertIn('frequencies', result)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_corpus_tokenization(self):
        temp_dir = tempfile.mkdtemp()
        output_dir = Path(temp_dir) / "output"
        
        try:
            corpus_dir = Path(temp_dir) / "corpus"
            corpus_dir.mkdir()
            
            for i in range(3):
                doc_file = corpus_dir / f"doc_{i:08d}.txt"
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write("TITLE: Test Document\n")
                    f.write("CONTENT:\n")
                    f.write(f"This is test document {i}. It has some content.")
            
            result = self.tokenizer.tokenize_corpus(corpus_dir, output_dir)
            
            self.assertEqual(result['total_documents'], 3)
            self.assertGreater(result['total_tokens'], 0)
            self.assertGreater(result['unique_tokens'], 0)
            self.assertIn('corpus_frequencies', result)
            self.assertIn('document_stats', result)

            self.assertTrue(output_dir.exists())
            stats_file = output_dir / 'corpus_tokenization_stats.json'
            self.assertTrue(stats_file.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTokenizer))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
