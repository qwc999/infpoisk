import re
from typing import List, Set, Dict, Tuple, Optional
from pathlib import Path

from boolean_index import BooleanIndex


class BooleanSearch:

    def __init__(self, index: BooleanIndex):
        self.index = index
        self.operators = {'AND', 'OR', 'NOT'}
    
    def _tokenize_query(self, query: str) -> List[str]:
        query = query.strip()

        tokens = []
        current_term = ""
        i = 0
        
        while i < len(query):
            operator_found = False
            for op in sorted(self.operators, key=len, reverse=True):
                op_lower = op.lower()
                if query[i:i+len(op_lower)].lower() == op_lower:
                    if current_term.strip():
                        tokens.append(current_term.strip())
                        current_term = ""
                    tokens.append(op)
                    i += len(op)
                    operator_found = True
                    break
            
            if not operator_found:
                current_term += query[i]
                i += 1

        if current_term.strip():
            tokens.append(current_term.strip())
        
        return tokens
    
    def _parse_query(self, query: str) -> List:
        tokens = self._tokenize_query(query)

        processed_tokens = []
        i = 0
        while i < len(tokens):
            if tokens[i].upper() == 'NOT':
                processed_tokens.append('NOT')
                i += 1
            elif tokens[i].upper() in ('AND', 'OR'):
                processed_tokens.append(tokens[i].upper())
                i += 1
            else:
                processed_tokens.append(tokens[i])
                i += 1

        output = []
        operator_stack = []
        
        for token in processed_tokens:
            if token.upper() in self.operators:
                precedence = {'NOT': 3, 'AND': 2, 'OR': 1}
                token_prec = precedence.get(token.upper(), 0)
                
                while (operator_stack and 
                       operator_stack[-1].upper() in self.operators and
                       precedence.get(operator_stack[-1].upper(), 0) >= token_prec):
                    output.append(operator_stack.pop())
                
                operator_stack.append(token.upper())
            else:
                output.append(token)

        while operator_stack:
            output.append(operator_stack.pop())
        
        return output
    
    def _evaluate_term(self, term: str) -> Set[int]:
        term = term.strip().strip('"').strip("'")
        return self.index.get_documents(term)
    
    def _evaluate_query_postfix(self, postfix: List) -> Set[int]:
        stack = []
        
        for token in postfix:
            if token.upper() == 'NOT':
                if not stack:
                    continue
                operand = stack.pop()
                all_docs = set(range(1, self.index.stats['total_documents'] + 1))
                result = all_docs - operand
                stack.append(result)
            elif token.upper() == 'AND':
                if len(stack) < 2:
                    continue
                right = stack.pop()
                left = stack.pop()
                result = left & right
                stack.append(result)
            elif token.upper() == 'OR':
                if len(stack) < 2:
                    continue
                right = stack.pop()
                left = stack.pop()
                result = left | right
                stack.append(result)
            else:
                doc_ids = self._evaluate_term(token)
                stack.append(doc_ids)
        
        if not stack:
            return set()
        
        return stack.pop()
    
    def search(self, query: str) -> Tuple[Set[int], Dict]:
        if not query or not query.strip():
            return set(), {'error': 'Empty query'}
        
        try:
            postfix = self._parse_query(query)

            result_docs = self._evaluate_query_postfix(postfix)
            
            metadata = {
                'query': query,
                'parsed_query': postfix,
                'result_count': len(result_docs),
                'total_documents': self.index.stats['total_documents']
            }
            
            return result_docs, metadata
        except Exception as e:
            return set(), {'error': str(e), 'query': query}
    
    def search_simple(self, terms: List[str], operator: str = 'AND') -> Set[int]:
        if not terms:
            return set()
        
        operator = operator.upper()
        if operator not in ('AND', 'OR'):
            operator = 'AND'

        doc_sets = [self.index.get_documents(term.strip()) for term in terms]
        
        if not doc_sets:
            return set()

        if operator == 'AND':
            result = doc_sets[0]
            for doc_set in doc_sets[1:]:
                result = result & doc_set
        else:
            result = doc_sets[0]
            for doc_set in doc_sets[1:]:
                result = result | doc_set
        
        return result
    
    def get_results_with_metadata(self, doc_ids: Set[int], limit: int = None) -> List[Dict]:
        sorted_docs = sorted(list(doc_ids))
        
        if limit:
            sorted_docs = sorted_docs[:limit]
        
        results = []
        for doc_id in sorted_docs:
            metadata = self.index.documents.get(doc_id, {})
            results.append({
                'doc_id': doc_id,
                'metadata': metadata
            })
        
        return results


class BooleanSearchEngine:
    
    def __init__(self, index_path: Path = None, index: BooleanIndex = None):
        if index:
            self.index = index
        elif index_path:
            self.index = BooleanIndex()
            self.index.load(index_path)
        else:
            raise ValueError("Either index_path or index must be provided")
        
        self.search_engine = BooleanSearch(self.index)
    
    def search(self, query: str, limit: int = None) -> Dict:
        doc_ids, metadata = self.search_engine.search(query)
        
        results = self.search_engine.get_results_with_metadata(doc_ids, limit)
        
        return {
            'query': query,
            'results': results,
            'result_count': len(doc_ids),
            'metadata': metadata
        }
