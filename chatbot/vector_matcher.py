
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict, Optional
import pickle
import os

class VectorMatcher:
    def __init__(self, model_path: str = 'chatbot/models'):
        self.model_path = model_path
        self.vectorizer = None
        self.query_vectors = None
        self.queries_with_responses = []
        self.similarity_threshold = 0.3
        
        # Create models directory
        os.makedirs(model_path, exist_ok=True)
        
        # Load existing data
        self.load_vectors()
    
    def add_query_response(self, query: str, response: str, intent: str = None):
        """Add a query-response pair to the vector database"""
        self.queries_with_responses.append({
            'query': query.lower().strip(),
            'response': response,
            'intent': intent
        })
        
        # Rebuild vectors
        self._rebuild_vectors()
    
    def _rebuild_vectors(self):
        """Rebuild the vector index with all queries"""
        if not self.queries_with_responses:
            return
        
        queries = [item['query'] for item in self.queries_with_responses]
        
        # Create or update vectorizer
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                stop_words='english',
                lowercase=True
            )
            self.query_vectors = self.vectorizer.fit_transform(queries)
        else:
            # Update with new queries
            try:
                self.query_vectors = self.vectorizer.transform(queries)
            except:
                # If vocabulary changed significantly, retrain
                self.vectorizer = TfidfVectorizer(
                    max_features=500,
                    ngram_range=(1, 2),
                    stop_words='english',
                    lowercase=True
                )
                self.query_vectors = self.vectorizer.fit_transform(queries)
        
        # Save updated vectors
        self.save_vectors()
    
    def find_similar_queries(self, query: str, top_k: int = 3) -> List[Dict]:
        """Find similar queries and their responses"""
        if not self.queries_with_responses or self.vectorizer is None:
            return []
        
        # Vectorize the input query
        try:
            query_vector = self.vectorizer.transform([query.lower().strip()])
        except:
            return []
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.query_vectors)[0]
        
        # Get top similar queries above threshold
        similar_indices = []
        for i, sim in enumerate(similarities):
            if sim >= self.similarity_threshold:
                similar_indices.append((i, sim))
        
        # Sort by similarity and get top k
        similar_indices.sort(key=lambda x: x[1], reverse=True)
        similar_indices = similar_indices[:top_k]
        
        # Return results
        results = []
        for idx, similarity in similar_indices:
            item = self.queries_with_responses[idx].copy()
            item['similarity'] = similarity
            results.append(item)
        
        return results
    
    def get_best_match(self, query: str) -> Optional[Dict]:
        """Get the best matching query-response pair"""
        similar_queries = self.find_similar_queries(query, top_k=1)
        
        if similar_queries and similar_queries[0]['similarity'] >= self.similarity_threshold:
            return similar_queries[0]
        
        return None
    
    def save_vectors(self):
        """Save vectorizer and query data"""
        vector_file = os.path.join(self.model_path, 'vector_matcher.pkl')
        data = {
            'vectorizer': self.vectorizer,
            'queries_with_responses': self.queries_with_responses,
            'query_vectors': self.query_vectors
        }
        
        try:
            with open(vector_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving vectors: {e}")
    
    def load_vectors(self):
        """Load vectorizer and query data"""
        vector_file = os.path.join(self.model_path, 'vector_matcher.pkl')
        
        if os.path.exists(vector_file):
            try:
                with open(vector_file, 'rb') as f:
                    data = pickle.load(f)
                
                self.vectorizer = data.get('vectorizer')
                self.queries_with_responses = data.get('queries_with_responses', [])
                self.query_vectors = data.get('query_vectors')
                
                print(f"Vectors loaded from {vector_file}")
                return True
            except Exception as e:
                print(f"Error loading vectors: {e}")
                return False
        return False
    
    def update_from_logs(self, bot_logs: List[Dict]):
        """Update vector database from bot interaction logs"""
        for log in bot_logs:
            if log.get('feedback') == 1:  # Only add positively rated responses
                self.add_query_response(
                    query=log['query'],
                    response=log['response'],
                    intent=log.get('intent')
                )
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector database"""
        return {
            'total_queries': len(self.queries_with_responses),
            'has_vectorizer': self.vectorizer is not None,
            'similarity_threshold': self.similarity_threshold
        }
