import unittest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))

try:
    from boolean_index import BooleanIndex
    from tokenizer import Tokenizer
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))
    from boolean_index import BooleanIndex
    from tokenizer import Tokenizer


class TestBooleanIndex(unittest.TestCase):
    def setUp(self):
        self.index = BooleanIndex()
    
    def test_add_document(self):
        tokens = ['cat', 'dog', 'cat', 'bird']
        self.index.add_document(1, tokens)
        
        self.assertEqual(self.index.stats['total_documents'], 1)
        self.assertEqual(self.index.stats['total_terms'], 3)
        
        self.assertIn('cat', self.index.index)
        self.assertIn('dog', self.index.index)
        self.assertIn('bird', self.index.index)
    
    def test_get_documents(self):
        self.index.add_document(1, ['cat', 'dog'])
        self.index.add_document(2, ['cat', 'bird'])
        self.index.add_document(3, ['dog', 'fish'])

        doc_ids = self.index.get_documents('cat')
        self.assertEqual(doc_ids, {1, 2})

        doc_ids = self.index.get_documents('dog')
        self.assertEqual(doc_ids, {1, 3})

        doc_ids = self.index.get_documents('nonexistent')
        self.assertEqual(doc_ids, set())
    
    def test_get_document_count(self):
        self.index.add_document(1, ['cat', 'dog'])
        self.index.add_document(2, ['cat', 'bird'])
        self.index.add_document(3, ['cat', 'fish'])
        
        count = self.index.get_document_count('cat')
        self.assertEqual(count, 3)
        
        count = self.index.get_document_count('dog')
        self.assertEqual(count, 1)
    
    def test_get_all_terms(self):
        self.index.add_document(1, ['cat', 'dog'])
        self.index.add_document(2, ['bird', 'fish'])
        
        terms = self.index.get_all_terms()
        self.assertEqual(len(terms), 4)
        self.assertIn('cat', terms)
        self.assertIn('dog', terms)
        self.assertIn('bird', terms)
        self.assertIn('fish', terms)
    
    def test_get_index_statistics(self):
        self.index.add_document(1, ['cat', 'dog'])
        self.index.add_document(2, ['cat', 'bird'])
        
        stats = self.index.get_index_statistics()
        
        self.assertIn('total_documents', stats)
        self.assertIn('total_terms', stats)
        self.assertIn('index_size', stats)
        self.assertIn('top_terms', stats)
        
        self.assertEqual(stats['total_documents'], 2)
        self.assertEqual(stats['total_terms'], 3)
    
    def test_save_and_load(self):
        temp_dir = tempfile.mkdtemp()
        
        try:
            self.index.add_document(1, ['cat', 'dog'])
            self.index.add_document(2, ['cat', 'bird'])

            index_file = Path(temp_dir) / 'test_index.json'
            self.index.save(index_file)
            
            new_index = BooleanIndex()
            new_index.load(index_file)

            self.assertEqual(new_index.stats['total_documents'], 2)
            self.assertEqual(new_index.stats['total_terms'], 3)

            doc_ids = new_index.get_documents('cat')
            self.assertEqual(doc_ids, {1, 2})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_export_to_text(self):
        temp_dir = tempfile.mkdtemp()
        
        try:
            self.index.add_document(1, ['cat', 'dog'])
            self.index.add_document(2, ['cat', 'bird'])
            
            text_file = Path(temp_dir) / 'index.txt'
            self.index.export_to_text(text_file)
            
            self.assertTrue(text_file.exists())
            
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Boolean Index', content)
                self.assertIn('cat', content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_unique_terms(self):
        tokens = ['cat', 'cat', 'dog', 'cat', 'bird']
        self.index.add_document(1, tokens)
        
        self.assertEqual(self.index.stats['total_terms'], 3)

        self.assertIn(1, self.index.get_documents('cat'))
        self.assertIn(1, self.index.get_documents('dog'))
        self.assertIn(1, self.index.get_documents('bird'))


class TestBooleanIndexIntegration(unittest.TestCase):
    def test_build_from_corpus(self):
        temp_dir = tempfile.mkdtemp()
        
        try:
            corpus_dir = Path(temp_dir) / 'corpus'
            corpus_dir.mkdir()

            doc1 = corpus_dir / 'doc_00000001.txt'
            with open(doc1, 'w', encoding='utf-8') as f:
                f.write("TITLE: Test Document 1\n")
                f.write("CONTENT:\n")
                f.write("The cat sat on the mat.")
            
            doc2 = corpus_dir / 'doc_00000002.txt'
            with open(doc2, 'w', encoding='utf-8') as f:
                f.write("TITLE: Test Document 2\n")
                f.write("CONTENT:\n")
                f.write("The dog ran in the park.")

            index = BooleanIndex()
            tokenizer = Tokenizer(lowercase=True, min_length=1)
            build_stats = index.build_from_corpus(corpus_dir, tokenizer)
            
            self.assertEqual(build_stats['documents_processed'], 2)
            self.assertGreater(index.stats['total_terms'], 0)

            the_docs = index.get_documents('the')
            self.assertGreater(len(the_docs), 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_build_with_stemmer(self):
        temp_dir = tempfile.mkdtemp()
        
        try:
            from stemmer import Stemmer
            
            corpus_dir = Path(temp_dir) / 'corpus'
            corpus_dir.mkdir()
            
            doc1 = corpus_dir / 'doc_00000001.txt'
            with open(doc1, 'w', encoding='utf-8') as f:
                f.write("CONTENT:\n")
                f.write("cats dogs")
            
            index = BooleanIndex()
            tokenizer = Tokenizer(lowercase=True, min_length=1)
            stemmer = Stemmer(language='english')
            build_stats = index.build_from_corpus(corpus_dir, tokenizer, stemmer)
            
            self.assertEqual(build_stats['documents_processed'], 1)
            self.assertGreater(index.stats['total_terms'], 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBooleanIndex))
    suite.addTests(loader.loadTestsFromTestCase(TestBooleanIndexIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
