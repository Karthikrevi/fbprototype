import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional
import re

class VectorMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        self.response_database = self._build_response_database()
        self.fitted = False

        if self.response_database:
            self._fit_vectorizer()

    def _build_response_database(self) -> List[Dict]:
        """Build a database of query-response pairs for similarity matching"""
        return [
            {
                "query": "what are my top selling products",
                "response": "Let me show you your top selling products based on recent sales data.",
                "intent": "top_selling_products",
                "keywords": ["top", "selling", "best", "popular", "products"]
            },
            {
                "query": "show me products with low stock",
                "response": "Here are the products that are running low on inventory and may need reordering.",
                "intent": "low_stock_alerts",
                "keywords": ["low", "stock", "inventory", "reorder", "alert"]
            },
            {
                "query": "what is my revenue this month",
                "response": "Let me calculate your revenue and sales summary for the current period.",
                "intent": "revenue_report",
                "keywords": ["revenue", "sales", "income", "earnings", "money"]
            },
            {
                "query": "show me my profit analysis",
                "response": "I'll analyze your profit margins and provide a detailed breakdown of your profitability.",
                "intent": "profit_summary",
                "keywords": ["profit", "margin", "profitability", "earnings"]
            },
            {
                "query": "analyze my inventory performance",
                "response": "Let me analyze your inventory turnover rates and stock performance metrics.",
                "intent": "inventory_performance",
                "keywords": ["inventory", "performance", "turnover", "analysis"]
            },
            {
                "query": "what are my business expenses",
                "response": "Here's a summary of your business expenses and cost breakdown.",
                "intent": "expense_analysis",
                "keywords": ["expenses", "costs", "spending", "expenditure"]
            }
        ]

    def _fit_vectorizer(self):
        """Fit the vectorizer on the response database"""
        if not self.response_database:
            return

        queries = [item["query"] for item in self.response_database]
        self.vectorizer.fit(queries)
        self.fitted = True

    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for matching"""
        query = query.lower()
        query = re.sub(r'[^\w\s]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        return query

    def get_best_match(self, query: str, threshold: float = 0.3) -> Optional[Dict]:
        """Find the best matching response for a query"""
        if not self.fitted or not self.response_database:
            return None

        processed_query = self._preprocess_query(query)

        try:
            # Vectorize the input query
            query_vector = self.vectorizer.transform([processed_query])

            # Vectorize all database queries
            db_queries = [self._preprocess_query(item["query"]) for item in self.response_database]
            db_vectors = self.vectorizer.transform(db_queries)

            # Calculate similarities
            similarities = cosine_similarity(query_vector, db_vectors)[0]

            # Find best match
            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]

            if best_similarity >= threshold:
                match = self.response_database[best_idx].copy()
                match["similarity"] = float(best_similarity)
                return match

            return None

        except Exception as e:
            print(f"Vector matching error: {e}")
            return None

    def add_response(self, query: str, response: str, intent: str = "unknown"):
        """Add a new query-response pair to the database"""
        new_item = {
            "query": query,
            "response": response,
            "intent": intent,
            "keywords": query.lower().split()
        }

        self.response_database.append(new_item)

        # Refit vectorizer with new data
        self._fit_vectorizer()
import sqlite3
from typing import Dict, Optional, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class VectorMatcher:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path
        self.vectorizer = TfidfVectorizer(max_features=1000, lowercase=True)
        self.query_vectors = None
        self.responses = []
        self.similarity_threshold = 0.3
        self._load_training_data()
    
    def _load_training_data(self):
        """Load training data for similarity matching"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Try to get training data from database
            c.execute("""
                SELECT query, response, intent FROM chatbot_training_data 
                WHERE is_validated = 1
            """)
            
            training_data = c.fetchall()
            conn.close()
            
            if training_data:
                queries = [item[0] for item in training_data]
                self.responses = [
                    {
                        'query': item[0],
                        'response': item[1],
                        'intent': item[2]
                    } for item in training_data
                ]
                
                # Create TF-IDF vectors
                self.query_vectors = self.vectorizer.fit_transform(queries)
            else:
                self._create_fallback_data()
                
        except Exception as e:
            print(f"Error loading training data: {e}")
            self._create_fallback_data()
    
    def _create_fallback_data(self):
        """Create fallback similarity data"""
        fallback_data = [
            {
                'query': 'show me top products',
                'response': 'I can show you your top selling products. Let me analyze your sales data.',
                'intent': 'top_selling_products'
            },
            {
                'query': 'low stock products',
                'response': 'I can help you identify products that are running low on stock.',
                'intent': 'low_stock_alerts'
            },
            {
                'query': 'revenue report',
                'response': 'I can generate a revenue report based on your sales data.',
                'intent': 'revenue_report'
            },
            {
                'query': 'profit analysis',
                'response': 'I can analyze your profit margins and financial performance.',
                'intent': 'profit_summary'
            },
            {
                'query': 'inventory performance',
                'response': 'I can analyze your inventory turnover and product performance.',
                'intent': 'inventory_performance'
            }
        ]
        
        self.responses = fallback_data
        queries = [item['query'] for item in fallback_data]
        self.query_vectors = self.vectorizer.fit_transform(queries)
    
    def get_best_match(self, query: str) -> Optional[Dict]:
        """Find the best matching response for a query"""
        if not self.query_vectors or not self.responses:
            return None
        
        try:
            # Transform the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.query_vectors)[0]
            
            # Find the best match
            best_match_index = np.argmax(similarities)
            best_similarity = similarities[best_match_index]
            
            # Check if similarity meets threshold
            if best_similarity >= self.similarity_threshold:
                response = self.responses[best_match_index].copy()
                response['similarity'] = best_similarity
                return response
            
            return None
            
        except Exception as e:
            print(f"Error finding best match: {e}")
            return None
    
    def add_training_example(self, query: str, response: str, intent: str):
        """Add a new training example"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("""
                INSERT INTO chatbot_training_data (query, response, intent, is_validated)
                VALUES (?, ?, ?, 1)
            """, (query, response, intent))
            
            conn.commit()
            conn.close()
            
            # Reload training data
            self._load_training_data()
            
        except Exception as e:
            print(f"Error adding training example: {e}")
