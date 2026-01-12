import json
from typing import Dict, Set, List
from pathlib import Path
from collections import defaultdict


class BooleanIndex:

    def __init__(self):
        self.index: Dict[str, Set[int]] = defaultdict(set)

        self.documents: Dict[int, Dict] = {}

        self.stats = {
            'total_documents': 0,
            'total_terms': 0,
            'index_size': 0
        }
    
    def add_document(self, doc_id: int, tokens: List[str], metadata: Dict = None):
        terms = set(tokens)

        for term in terms:
            self.index[term].add(doc_id)
        if metadata is None:
            metadata = {}
        self.documents[doc_id] = metadata

        self.stats['total_documents'] = len(self.documents)
        self.stats['total_terms'] = len(self.index)
        self.stats['index_size'] = sum(len(doc_ids) for doc_ids in self.index.values())
    
    def get_documents(self, term: str) -> Set[int]:
        return self.index.get(term, set())
    
    def get_document_count(self, term: str) -> int:
        return len(self.get_documents(term))
    
    def get_term_frequency(self, term: str) -> int:
        return self.get_document_count(term)
    
    def get_all_terms(self) -> List[str]:
        return sorted(self.index.keys())
    
    def get_index_statistics(self) -> Dict:
        term_frequencies = {
            term: len(doc_ids) for term, doc_ids in self.index.items()
        }

        sorted_terms = sorted(term_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_documents': self.stats['total_documents'],
            'total_terms': self.stats['total_terms'],
            'index_size': self.stats['index_size'],
            'average_terms_per_document': (
                self.stats['index_size'] / self.stats['total_documents']
                if self.stats['total_documents'] > 0 else 0
            ),
            'top_terms': [
                {'term': term, 'document_frequency': freq}
                for term, freq in sorted_terms[:20]
            ]
        }
    
    def build_from_corpus(self, corpus_dir: Path, tokenizer=None, stemmer=None):
        from tokenizer import Tokenizer
        
        if tokenizer is None:
            tokenizer = Tokenizer(lowercase=True, min_length=1)
        
        corpus_dir = Path(corpus_dir)
        if not corpus_dir.exists():
            raise ValueError(f"Corpus directory does not exist: {corpus_dir}")

        text_files = sorted(corpus_dir.glob('doc_*.txt'))
        
        if not text_files:
            raise ValueError(f"No documents found in {corpus_dir}")
        
        documents_processed = 0
        errors = 0
        
        for text_file in text_files:
            try:
                doc_id_str = text_file.stem.split('_')[1]
                doc_id = int(doc_id_str)

                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'CONTENT:' in content:
                    content = content.split('CONTENT:')[1].strip()

                tokens = tokenizer.tokenize(content)

                if stemmer:
                    tokens = stemmer.stem_tokens(tokens)

                metadata = {}
                if 'TITLE:' in content:
                    title_line = [line for line in content.split('\n') if line.startswith('TITLE:')]
                    if title_line:
                        metadata['title'] = title_line[0].replace('TITLE:', '').strip()

                self.add_document(doc_id, tokens, metadata)
                documents_processed += 1
                
            except Exception as e:
                errors += 1
                continue
        
        return {
            'documents_processed': documents_processed,
            'errors': errors,
            'index_statistics': self.get_index_statistics()
        }
    
    def save(self, output_path: Path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        index_data = {
            'index': {
                term: sorted(list(doc_ids))
                for term, doc_ids in self.index.items()
            },
            'documents': self.documents,
            'stats': self.stats
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def load(self, input_path: Path):
        input_path = Path(input_path)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        self.index = {
            term: set(doc_ids)
            for term, doc_ids in index_data['index'].items()
        }
        
        self.documents = index_data.get('documents', {})
        self.stats = index_data.get('stats', {
            'total_documents': 0,
            'total_terms': 0,
            'index_size': 0
        })
    
    def export_to_text(self, output_path: Path, max_terms: int = None):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Boolean Index\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total documents: {self.stats['total_documents']}\n")
            f.write(f"Total terms: {self.stats['total_terms']}\n")
            f.write(f"Index size: {self.stats['index_size']}\n\n")
            f.write("Term -> Document IDs\n")
            f.write("-" * 80 + "\n\n")

            sorted_terms = sorted(
                self.index.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            if max_terms:
                sorted_terms = sorted_terms[:max_terms]
            
            for term, doc_ids in sorted_terms:
                doc_list = sorted(list(doc_ids))
                f.write(f"{term}: {len(doc_ids)} documents\n")
                f.write(f"  Documents: {doc_list[:20]}")
                if len(doc_list) > 20:
                    f.write(f" ... (and {len(doc_list) - 20} more)")
                f.write("\n\n")
