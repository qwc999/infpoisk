import re
from typing import List, Dict, Set
from pathlib import Path
import json


class RussianStemmer:

    def __init__(self):
        self.vowels = set('аеёиоуыѝюѝ')

        self.perfective_gerund_suffixes = [
            'вшиѝь', 'вши', 'вшиѝь', 'вшиѝь'
        ]

        self.adjectival_suffixes = [
            'ее', 'ие', 'ые', 'ое', 'ими', 'ыми', 'ей', 'ий', 'ый', 'ой',
            'ем', 'им', 'ым', 'ом', 'его', 'ого', 'ему', 'ому', 'их', 'ых',
            'ую', 'юю', 'аѝ', 'ѝѝ', 'ою', 'ею'
        ]

        self.reflexive_suffixes = ['ѝѝ', 'ѝь']

        self.verb_suffixes = [
            'ила', 'ыла', 'ена', 'ейте', 'уйте', 'ите', 'или', 'ыли', 'ей',
            'уй', 'ил', 'ыл', 'им', 'ым', 'ен', 'ило', 'ыло', 'ено', 'ѝт',
            'ует', 'уют', 'ит', 'ыт', 'ены', 'ить', 'ыть', 'ишь', 'ую', 'ю'
        ]

        self.noun_suffixes = [
            'ами', 'ами', 'ей', 'ев', 'ов', 'ие', 'ье', 'еи', 'ии', 'ей',
            'ой', 'ий', 'ѝм', 'ем', 'ам', 'ом', 'ах', 'ѝх', 'и', 'ы', 'ь',
            'ию', 'ью', 'у', 'ю', 'а', 'ѝ', 'о', 'е', 'ё', 'ѝ'
        ]

        self.derivational_suffixes = [
            'оѝт', 'оѝть'
        ]

        self.superlative_suffixes = [
            'ейш', 'ейше'
        ]

        self.common_endings = [
            'ами', 'ѝми', 'ами', 'ев', 'ов', 'ие', 'ье', 'еи', 'ии', 'ей',
            'ой', 'ий', 'ѝм', 'ем', 'ам', 'ом', 'ах', 'ѝх', 'ую', 'юю',
            'аѝ', 'ѝѝ', 'ою', 'ею', 'ите', 'йте', 'ила', 'ыла', 'ена',
            'ейте', 'уйте', 'или', 'ыли', 'ей', 'уй', 'ил', 'ыл', 'им',
            'ым', 'ен', 'ило', 'ыло', 'ено', 'ѝт', 'ует', 'уют', 'ит',
            'ыт', 'ены', 'ить', 'ыть', 'ишь', 'ую', 'ю', 'и', 'ы', 'ь',
            'а', 'ѝ', 'о', 'е', 'ё', 'ѝ', 'у'
        ]

        self.common_endings.sort(key=len, reverse=True)
    
    def _is_vowel(self, char: str) -> bool:
        return char.lower() in self.vowels
    
    def _has_vowel(self, word: str) -> bool:
        return any(self._is_vowel(c) for c in word)
    
    def _get_rv(self, word: str) -> str:
        for i, char in enumerate(word):
            if self._is_vowel(char):
                return word[i+1:]
        return ''
    
    def _get_r2(self, word: str) -> str:
        rv = self._get_rv(word)
        for i, char in enumerate(rv):
            if self._is_vowel(char):
                return rv[i+1:]
        return ''
    
    def _remove_suffix(self, word: str, suffix: str) -> str:
        if word.endswith(suffix):
            return word[:-len(suffix)]
        return word
    
    def _remove_suffixes(self, word: str, suffixes: List[str]) -> str:
        for suffix in suffixes:
            if word.endswith(suffix):
                return word[:-len(suffix)]
        return word
    
    def stem(self, word: str) -> str:
        if not word or len(word) < 2:
            return word
        
        word = word.lower().strip()

        for suffix in self.reflexive_suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                word = word[:-len(suffix)]
                break

        for suffix in self.adjectival_suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                word = word[:-len(suffix)]
                break

        for suffix in self.verb_suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                word = word[:-len(suffix)]
                break

        for suffix in self.noun_suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                word = word[:-len(suffix)]
                break

        original_word = word
        for ending in self.common_endings:
            if word.endswith(ending) and len(word) > len(ending) + 1:
                stem = word[:-len(ending)]
                if len(stem) >= 2 and self._has_vowel(stem):
                    word = stem
                    break

        if len(word) < 2:
            return original_word[:2] if len(original_word) >= 2 else original_word
        
        return word
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        return [self.stem(token) for token in tokens]
    
    def get_stem_frequencies(self, tokens: List[str]) -> Dict[str, int]:
        stems = self.stem_tokens(tokens)
        frequencies = {}
        for stem in stems:
            frequencies[stem] = frequencies.get(stem, 0) + 1
        return frequencies
    
    def get_stem_vocabulary(self, tokens: List[str]) -> Set[str]:
        stems = self.stem_tokens(tokens)
        return set(stems)


class Stemmer:

    def __init__(self, language: str = 'russian'):
        self.language = language.lower()
        
        if self.language == 'russian':
            self.stemmer = RussianStemmer()
        else:
            self.stemmer = None
    
    def stem(self, word: str) -> str:
        if not word:
            return word
        
        if self.language == 'russian':
            return self.stemmer.stem(word)
        else:
            return self._stem_english(word)
    
    def _stem_english(self, word: str) -> str:
        word = word.lower()

        suffixes = [
            'ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment',
            'able', 'ible', 'ful', 'less', 'ous', 'ious', 'es', 's'
        ]
        
        for suffix in sorted(suffixes, key=len, reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                word = word[:-len(suffix)]
                break
        
        return word
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        return [self.stem(token) for token in tokens]
    
    def get_stem_frequencies(self, tokens: List[str]) -> Dict[str, int]:
        stems = self.stem_tokens(tokens)
        frequencies = {}
        for stem in stems:
            frequencies[stem] = frequencies.get(stem, 0) + 1
        return frequencies
    
    def get_stem_vocabulary(self, tokens: List[str]) -> Set[str]:
        stems = self.stem_tokens(tokens)
        return set(stems)
    
    def process_document(self, tokens: List[str]) -> Dict:
        stems = self.stem_tokens(tokens)
        frequencies = self.get_stem_frequencies(tokens)
        vocabulary = self.get_stem_vocabulary(tokens)

        token_to_stem = {}
        for token, stem in zip(tokens, stems):
            if token not in token_to_stem:
                token_to_stem[token] = stem
        
        return {
            'stems': stems,
            'total_stems': len(stems),
            'unique_stems': len(vocabulary),
            'stem_frequencies': frequencies,
            'stem_vocabulary': list(vocabulary),
            'token_to_stem': token_to_stem
        }
    
    def process_corpus(self, corpus_tokens: Dict[str, List[str]], output_dir: Path = None) -> Dict:
        all_stems = []
        all_vocabulary = set()
        document_results = {}
        
        for doc_id, tokens in corpus_tokens.items():
            result = self.process_document(tokens)
            document_results[doc_id] = result
            
            all_stems.extend(result['stems'])
            all_vocabulary.update(result['stem_vocabulary'])
        
        corpus_frequencies = {}
        for stem in all_stems:
            corpus_frequencies[stem] = corpus_frequencies.get(stem, 0) + 1
        
        corpus_stats = {
            'total_documents': len(corpus_tokens),
            'total_stems': len(all_stems),
            'unique_stems': len(all_vocabulary),
            'corpus_stem_frequencies': corpus_frequencies,
            'document_results': document_results
        }

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            stats_file = output_dir / 'corpus_stemming_stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(corpus_stats, f, ensure_ascii=False, indent=2)

            stems_dir = output_dir / 'stemmed_documents'
            stems_dir.mkdir(exist_ok=True)
            
            for doc_id, result in document_results.items():
                stem_file = stems_dir / f"{doc_id}_stems.json"
                with open(stem_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'document_id': doc_id,
                        'stems': result['stems'],
                        'stem_frequencies': result['stem_frequencies'],
                        'token_to_stem': result['token_to_stem']
                    }, f, ensure_ascii=False, indent=2)
        
        return corpus_stats
