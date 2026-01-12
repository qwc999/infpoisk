import unittest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))

try:
    from boolean_search import BooleanSearch, BooleanSearchEngine
    from boolean_index import BooleanIndex
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))
    from boolean_search import BooleanSearch, BooleanSearchEngine
    from boolean_index import BooleanIndex


class TestBooleanSearch(unittest.TestCase):

    def setUp(self):
        self.index = BooleanIndex()
        self.index.add_document(1, ['cat', 'dog', 'bird'])
        self.index.add_document(2, ['cat', 'dog'])
        self.index.add_document(3, ['cat', 'bird'])
        self.index.add_document(4, ['dog', 'fish'])
        self.index.add_document(5, ['bird', 'fish'])
        
        self.search_engine = BooleanSearch(self.index)
    
    def test_simple_term(self):
        doc_ids, metadata = self.search_engine.search('cat')
        self.assertEqual(doc_ids, {1, 2, 3})
        self.assertGreater(metadata['result_count'], 0)
    
    def test_and_operator(self):
        doc_ids, metadata = self.search_engine.search('cat AND dog')
        self.assertEqual(doc_ids, {1, 2})
        self.assertEqual(metadata['result_count'], 2)
    
    def test_or_operator(self):
        doc_ids, metadata = self.search_engine.search('cat OR fish')
        self.assertEqual(doc_ids, {1, 2, 3, 4, 5})
        self.assertEqual(metadata['result_count'], 5)
    
    def test_not_operator(self):
        doc_ids, metadata = self.search_engine.search('cat AND NOT dog')
        self.assertEqual(doc_ids, {3})
        self.assertEqual(metadata['result_count'], 1)
    
    def test_complex_query(self):
        doc_ids, metadata = self.search_engine.search('(cat OR dog) AND bird')
        self.assertEqual(doc_ids, {1, 3})
        self.assertEqual(metadata['result_count'], 2)
    
    def test_search_simple(self):
        # AND search
        doc_ids = self.search_engine.search_simple(['cat', 'dog'], 'AND')
        self.assertEqual(doc_ids, {1, 2})
        
        # OR search
        doc_ids = self.search_engine.search_simple(['cat', 'fish'], 'OR')
        self.assertEqual(doc_ids, {1, 2, 3, 4, 5})
    
    def test_empty_query(self):
        doc_ids, metadata = self.search_engine.search('')
        self.assertEqual(doc_ids, set())
        self.assertIn('error', metadata)
    
    def test_nonexistent_term(self):
        doc_ids, metadata = self.search_engine.search('nonexistent')
        self.assertEqual(doc_ids, set())
        self.assertEqual(metadata['result_count'], 0)
    
    def test_get_results_with_metadata(self):
        doc_ids = {1, 2, 3}
        results = self.search_engine.get_results_with_metadata(doc_ids, limit=2)
        
        self.assertEqual(len(results), 2)
        self.assertIn('doc_id', results[0])
        self.assertIn('metadata', results[0])


class TestBooleanSearchEngine(unittest.TestCase):

    def setUp(self):
        self.index = BooleanIndex()
        self.index.add_document(1, ['cat', 'dog'])
        self.index.add_document(2, ['cat', 'bird'])
        self.index.add_document(3, ['dog', 'fish'])
        
        self.engine = BooleanSearchEngine(index=self.index)
    
    def test_search(self):
        result = self.engine.search('cat AND dog')
        
        self.assertIn('query', result)
        self.assertIn('results', result)
        self.assertIn('result_count', result)
        self.assertEqual(result['result_count'], 1)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['doc_id'], 1)
    
    def test_search_with_limit(self):
        result = self.engine.search('cat OR dog', limit=2)
        
        self.assertLessEqual(len(result['results']), 2)
    
    def test_load_from_file(self):
        temp_dir = tempfile.mkdtemp()
        
        try:
            index_file = Path(temp_dir) / 'test_index.json'
            self.index.save(index_file)

            engine = BooleanSearchEngine(index_path=index_file)

            result = engine.search('cat')
            self.assertGreater(result['result_count'], 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestQueryParsing(unittest.TestCase):
    
    def setUp(self):
        self.index = BooleanIndex()
        self.index.add_document(1, ['cat', 'dog'])
        self.index.add_document(2, ['cat', 'bird'])
        self.index.add_document(3, ['dog', 'fish'])
        
        self.search_engine = BooleanSearch(self.index)
    
    def test_case_insensitive(self):
        doc_ids1, _ = self.search_engine.search('cat AND dog')
        doc_ids2, _ = self.search_engine.search('cat and dog')
        doc_ids3, _ = self.search_engine.search('cat And DoG')
        
        self.assertEqual(doc_ids1, doc_ids2)
        self.assertEqual(doc_ids1, doc_ids3)
    
    def test_operator_precedence(self):
        doc_ids, _ = self.search_engine.search('NOT cat AND dog')

        self.assertEqual(doc_ids, {3})


class TestBooleanSearchIntegration(unittest.TestCase):

    def test_complex_queries(self):
        index = BooleanIndex()
        index.add_document(1, ['cat', 'dog', 'bird'])
        index.add_document(2, ['cat', 'dog'])
        index.add_document(3, ['cat', 'bird'])
        index.add_document(4, ['dog', 'fish'])
        index.add_document(5, ['bird', 'fish'])
        index.add_document(6, ['cat'])
        
        search_engine = BooleanSearch(index)
        
        doc_ids, _ = search_engine.search('cat AND (dog OR bird)')
        self.assertEqual(doc_ids, {1, 2, 3, 6})

        doc_ids, _ = search_engine.search('(cat OR dog) AND NOT fish')
        self.assertEqual(doc_ids, {1, 2, 3, 6})


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBooleanSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestBooleanSearchEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestBooleanSearchIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
