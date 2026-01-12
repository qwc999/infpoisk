import re
from typing import List, Dict, Set
from pathlib import Path
import json


class Tokenizer:
    def __init__(self, lowercase: bool = True, remove_punctuation: bool = False, 
                 min_length: int = 1, remove_stopwords: bool = False):

        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.min_length = min_length
        self.remove_stopwords = remove_stopwords
        
        self.stopwords = self._load_stopwords() if remove_stopwords else set()

        self.word_pattern = re.compile(
            r'[а-ѝёН-ЯНa-zA-Z]+|[0-9]+|[а-ѝёН-ЯНa-zA-Z0-9]+',
            re.UNICODE
        )

        self.split_pattern = re.compile(
            r'[\s\.,;:!?\-—–\(\)\[\]{}"\''']+',
            re.UNICODE
        )
    
    def _load_stopwords(self) -> Set[str]:
        stopwords = {
            'и', 'в', 'на', 'ѝ', 'по', 'длѝ', 'от', 'из', 'к', 'о', 'а', 'как',
            'что', 'ѝто', 'так', 'он', 'она', 'они', 'мы', 'вы', 'ѝ', 'ты',
            'быть', 'был', 'была', 'было', 'были', 'еѝть', 'бы', 'не', 'нет',
            'но', 'или', 'еѝли', 'то', 'же', 'ли', 'уже', 'еще', 'тоже',
            'вѝе', 'вѝего', 'вѝех', 'вѝегда', 'вѝегда', 'вѝе', 'вѝе',
            'который', 'котораѝ', 'которое', 'которые', 'которого', 'которой',
            'которым', 'которыми', 'котором', 'которой', 'которую',
            'ѝтот', 'ѝта', 'ѝто', 'ѝти', 'ѝтого', 'ѝтой', 'ѝтому', 'ѝтим',
            'ѝтими', 'ѝтом', 'ѝту',
            'тот', 'та', 'те', 'того', 'той', 'тому', 'тем', 'теми', 'том', 'ту',
            'где', 'когда', 'как', 'почему', 'зачем', 'куда', 'откуда',
            'при', 'про', 'под', 'над', 'перед', 'за', 'между', 'ѝреди',
            'через', 'около', 'возле', 'вдоль', 'вокруг', 'внутри', 'вне',
            'до', 'поѝле', 'во', 'ѝо', 'об', 'обо',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its',
            'our', 'their', 'what', 'which', 'who', 'whom', 'whose', 'where',
            'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'now'
        }
        return stopwords
    
    def tokenize(self, text: str) -> List[str]:
        if not text:
            return []

        tokens = self.word_pattern.findall(text)

        processed_tokens = []
        for token in tokens:
            if self.remove_punctuation:
                token = re.sub(r'[^\w\s]', '', token)

            if self.lowercase:
                token = token.lower()

            if len(token) < self.min_length:
                continue

            if self.remove_stopwords and token in self.stopwords:
                continue
            
            processed_tokens.append(token)
        
        return processed_tokens
    
    def tokenize_simple(self, text: str) -> List[str]:
        if not text:
            return []

        tokens = self.split_pattern.split(text)
        
        processed_tokens = []
        for token in tokens:
            token = token.strip()
            
            if not token:
                continue

            if self.lowercase:
                token = token.lower()

            if len(token) < self.min_length:
                continue

            if self.remove_stopwords and token in self.stopwords:
                continue
            
            processed_tokens.append(token)
        
        return processed_tokens
    
    def get_token_frequencies(self, tokens: List[str]) -> Dict[str, int]:
        frequencies = {}
        for token in tokens:
            frequencies[token] = frequencies.get(token, 0) + 1
        return frequencies
    
    def get_vocabulary(self, tokens: List[str]) -> Set[str]:
        return set(tokens)
    
    def tokenize_document(self, document_path: Path) -> Dict:
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'CONTENT:' in content:
                content = content.split('CONTENT:')[1].strip()
            
            tokens = self.tokenize(content)
            frequencies = self.get_token_frequencies(tokens)
            vocabulary = self.get_vocabulary(tokens)
            
            return {
                'document_id': document_path.stem,
                'total_tokens': len(tokens),
                'unique_tokens': len(vocabulary),
                'tokens': tokens,
                'frequencies': frequencies,
                'vocabulary': list(vocabulary)
            }
        except Exception as e:
            return {
                'document_id': document_path.stem,
                'error': str(e),
                'total_tokens': 0,
                'unique_tokens': 0,
                'tokens': [],
                'frequencies': {},
                'vocabulary': []
            }
    
    def tokenize_corpus(self, corpus_dir: Path, output_dir: Path = None) -> Dict:
        corpus_dir = Path(corpus_dir)
        if not corpus_dir.exists():
            return {'error': f'Corpus directory does not exist: {corpus_dir}'}

        text_files = sorted(corpus_dir.glob('doc_*.txt'))
        
        if not text_files:
            return {'error': f'No documents found in {corpus_dir}'}
        
        all_tokens = []
        all_vocabulary = set()
        document_stats = []
        
        for doc_file in text_files:
            result = self.tokenize_document(doc_file)
            document_stats.append(result)
            
            if 'error' not in result:
                all_tokens.extend(result['tokens'])
                all_vocabulary.update(result['vocabulary'])
        
        corpus_frequencies = self.get_token_frequencies(all_tokens)
        
        corpus_stats = {
            'total_documents': len(text_files),
            'total_tokens': len(all_tokens),
            'unique_tokens': len(all_vocabulary),
            'corpus_frequencies': corpus_frequencies,
            'document_stats': document_stats
        }

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            stats_file = output_dir / 'corpus_tokenization_stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(corpus_stats, f, ensure_ascii=False, indent=2)

            tokens_dir = output_dir / 'tokenized_documents'
            tokens_dir.mkdir(exist_ok=True)
            
            for doc_stat in document_stats:
                if 'error' not in doc_stat:
                    token_file = tokens_dir / f"{doc_stat['document_id']}_tokens.json"
                    with open(token_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'document_id': doc_stat['document_id'],
                            'tokens': doc_stat['tokens'],
                            'frequencies': doc_stat['frequencies']
                        }, f, ensure_ascii=False, indent=2)
        
        return corpus_stats
