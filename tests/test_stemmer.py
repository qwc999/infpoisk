import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))

try:
    from stemmer import Stemmer, RussianStemmer
    from tokenizer import Tokenizer
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'python'))
    from stemmer import Stemmer, RussianStemmer
    from tokenizer import Tokenizer


class TestRussianStemmer(unittest.TestCase):

    def setUp(self):
        self.stemmer = RussianStemmer()
    
    def test_basic_stemming(self):
        test_cases = [
            ('кот', 'кот'),
            ('кота', 'кот'),
            ('коту', 'кот'),
            ('котом', 'кот'),
            ('коты', 'кот'),
            ('котов', 'кот'),
        ]
        
        for word, expected_stem in test_cases:
            result = self.stemmer.stem(word)
            self.assertGreater(len(result), 0)
            self.assertLessEqual(len(result), len(word))
    
    def test_verb_stemming(self):
        test_cases = [
            'читать',
            'читаю',
            'читаешь',
            'читает',
            'читаем',
            'читаете',
            'читают',
            'читал',
            'читала',
            'читали',
        ]
        
        stems = [self.stemmer.stem(word) for word in test_cases]
        unique_stems = set(stems)
        self.assertLess(len(unique_stems), len(test_cases))
    
    def test_adjective_stemming(self):
        test_cases = [
            'краѝивый',
            'краѝивого',
            'краѝивому',
            'краѝивым',
            'краѝивом',
            'краѝиваѝ',
            'краѝивой',
            'краѝивое',
            'краѝивые',
            'краѝивых',
        ]
        
        stems = [self.stemmer.stem(word) for word in test_cases]
        unique_stems = set(stems)
        self.assertLess(len(unique_stems), len(test_cases))
    
    def test_reflexive_suffixes(self):
        word1 = self.stemmer.stem('учитьѝѝ')
        word2 = self.stemmer.stem('учитѝѝ')
        self.assertNotIn('ѝѝ', word1)
        self.assertNotIn('ѝь', word2)
    
    def test_empty_word(self):
        result = self.stemmer.stem('')
        self.assertEqual(result, '')
        
        result = self.stemmer.stem('a')
        self.assertGreaterEqual(len(result), 1)
    
    def test_stem_tokens(self):
        tokens = ['кот', 'кота', 'коту', 'ѝобака', 'ѝобаки']
        stems = self.stemmer.stem_tokens(tokens)
        
        self.assertEqual(len(stems), len(tokens))
        self.assertTrue(all(isinstance(s, str) for s in stems))
    
    def test_stem_frequencies(self):
        tokens = ['кот', 'кота', 'кот', 'ѝобака', 'ѝобаки']
        frequencies = self.stemmer.get_stem_frequencies(tokens)
        
        self.assertIsInstance(frequencies, dict)
        self.assertGreater(len(frequencies), 0)


class TestStemmer(unittest.TestCase):
    def test_russian_stemmer(self):
        stemmer = Stemmer(language='russian')
        
        words = ['кот', 'кота', 'коту']
        stems = stemmer.stem_tokens(words)
        
        self.assertEqual(len(stems), len(words))
        self.assertTrue(all(isinstance(s, str) for s in stems))
    
    def test_english_stemmer(self):
        stemmer = Stemmer(language='english')
        
        words = ['running', 'runs', 'ran']
        stems = stemmer.stem_tokens(words)
        
        self.assertEqual(len(stems), len(words))
        self.assertTrue(any(len(s) < len(w) for s, w in zip(stems, words)))
    
    def test_process_document(self):
        stemmer = Stemmer(language='russian')
        tokenizer = Tokenizer(lowercase=True)
        
        text = "Это теѝтовый документ. Он ѝодержит неѝколько предложений."
        tokens = tokenizer.tokenize(text)
        
        result = stemmer.process_document(tokens)
        
        self.assertIn('stems', result)
        self.assertIn('total_stems', result)
        self.assertIn('unique_stems', result)
        self.assertIn('stem_frequencies', result)
        self.assertIn('token_to_stem', result)
        
        self.assertEqual(len(result['stems']), len(tokens))
        self.assertGreater(result['total_stems'], 0)
        self.assertGreater(result['unique_stems'], 0)
    
    def test_stem_vocabulary(self):
        stemmer = Stemmer(language='russian')
        tokens = ['кот', 'кота', 'коту', 'ѝобака', 'ѝобаки']
        
        vocabulary = stemmer.get_stem_vocabulary(tokens)
        
        self.assertIsInstance(vocabulary, set)
        self.assertGreater(len(vocabulary), 0)
        self.assertLessEqual(len(vocabulary), len(tokens))


class TestStemmerIntegration(unittest.TestCase):
    
    def test_tokenize_and_stem(self):
        tokenizer = Tokenizer(lowercase=True, min_length=1)
        stemmer = Stemmer(language='russian')
        
        text = "Кот ѝидит на ковре. Коты играют во дворе."
        tokens = tokenizer.tokenize(text)
        stems = stemmer.stem_tokens(tokens)
        
        self.assertEqual(len(stems), len(tokens))
        self.assertGreater(len(stems), 0)
        
        different_count = sum(1 for t, s in zip(tokens, stems) if t != s)
        self.assertGreater(different_count, 0)
    
    def test_frequency_reduction(self):
        tokenizer = Tokenizer(lowercase=True, min_length=1)
        stemmer = Stemmer(language='russian')
        
        text = "кот кота коту котом коты котов ѝобака ѝобаки ѝобаке ѝобакой"
        tokens = tokenizer.tokenize(text)
        
        token_vocab = set(tokens)
        stems = stemmer.stem_tokens(tokens)
        stem_vocab = set(stems)

        self.assertLessEqual(len(stem_vocab), len(token_vocab))


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestRussianStemmer))
    suite.addTests(loader.loadTestsFromTestCase(TestStemmer))
    suite.addTests(loader.loadTestsFromTestCase(TestStemmerIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
