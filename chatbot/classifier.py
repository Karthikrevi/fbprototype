import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from typing import Tuple, List, Dict
import re

class IntentClassifier:
    def __init__(self, model_path: str = 'chatbot/models/intent_classifier.pkl'):
        self.model_path = model_path
        self.pipeline = None
        self.confidence_threshold = 0.6 # Add confidence threshold
        self.nlp = None # Add nlp
        
        # Load trained model if it exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True) # Create directory for the model
        self.load_model()

    def load_model(self):
        """Load trained model if it exists"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                print(f"Model loaded from {self.model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.pipeline = None
        else:
            print("No model found. Training required.")
            self.pipeline = None

    def save_model(self):
        """Save trained model"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.pipeline, f)
        print(f"Model saved to {self.model_path}")

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for training/prediction"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def get_training_data(self) -> Tuple[List[str], List[str]]:
        """Get training data for intent classification"""

        # Training data with various ways users might ask questions
        training_data = [
            # Top selling products
            ("show me top products", "top_selling_products"),
            ("what are my best selling items", "top_selling_products"),
            ("top selling products", "top_selling_products"),
            ("best performers", "top_selling_products"),
            ("which products sell the most", "top_selling_products"),
            ("most popular products", "top_selling_products"),
            ("bestsellers", "top_selling_products"),
            ("top moving products", "top_selling_products"),
            ("fast moving products", "top_selling_products"),
            ("high demand products", "top_selling_products"),

            # Low stock alerts
            ("low stock products", "low_stock_alerts"),
            ("which products are running low", "low_stock_alerts"),
            ("show me low inventory", "low_stock_alerts"),
            ("products that need reordering", "low_stock_alerts"),
            ("stock alerts", "low_stock_alerts"),
            ("inventory warnings", "low_stock_alerts"),
            ("items with low quantity", "low_stock_alerts"),
            ("products to reorder", "low_stock_alerts"),
            ("stock levels", "low_stock_alerts"),
            ("inventory status", "low_stock_alerts"),

            # Revenue and sales
            ("show me revenue", "revenue_report"),
            ("what are my sales", "revenue_report"),
            ("sales summary", "revenue_report"),
            ("total revenue", "revenue_report"),
            ("monthly sales", "revenue_report"),
            ("how much did I sell", "revenue_report"),
            ("sales report", "revenue_report"),
            ("revenue analysis", "revenue_report"),
            ("sales performance", "revenue_report"),
            ("earnings", "revenue_report"),

            # Profit analysis
            ("profit margin", "profit_summary"),
            ("how much profit", "profit_summary"),
            ("profit analysis", "profit_summary"),
            ("profitability", "profit_summary"),
            ("gross profit", "profit_summary"),
            ("net profit", "profit_summary"),
            ("profit report", "profit_summary"),
            ("profit and loss", "profit_summary"),

            # Inventory performance
            ("inventory analysis", "inventory_performance"),
            ("inventory performance", "inventory_performance"),
            ("stock analysis", "inventory_performance"),
            ("turnover rate", "inventory_performance"),
            ("inventory turnover", "inventory_performance"),
            ("stock performance", "inventory_performance"),
            ("inventory metrics", "inventory_performance"),
            ("stock velocity", "inventory_performance"),

            # Expenses
            ("show expenses", "expense_analysis"),
            ("expense report", "expense_analysis"),
            ("business expenses", "expense_analysis"),
            ("cost analysis", "expense_analysis"),
            ("spending report", "expense_analysis"),
            ("operational costs", "expense_analysis"),
            ("expense summary", "expense_summary"),

            # Unknown/general queries
            ("hello", "unknown"),
            ("hi", "unknown"),
            ("help", "unknown"),
            ("what can you do", "unknown"),
            ("thanks", "unknown"),
            ("thank you", "unknown"),
        ]

        queries = [self.preprocess_text(query) for query, _ in training_data]
        intents = [intent for _, intent in training_data]

        return queries, intents

    def train(self) -> Dict:
        """Train the intent classifier"""
        queries, intents = self.get_training_data()

        if len(queries) == 0:
            return {"success": False, "error": "No training data available"}

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            queries, intents, test_size=0.2, random_state=42, stratify=intents
        )

        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
            ('classifier', LogisticRegression(random_state=42, max_iter=1000))
        ])

        # Train model
        self.pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Save model
        self.save_model()

        return {
            "success": True,
            "accuracy": accuracy,
            "training_samples": len(queries),
            "test_samples": len(X_test)
        }

    def predict(self, query: str) -> Tuple[str, float]:
        """Predict intent for a query"""
        if not self.pipeline:
            return "unknown", 0.0

        processed_query = self.preprocess_text(query)

        try:
            # Get prediction and probability
            intent = self.pipeline.predict([processed_query])[0]
            probabilities = self.pipeline.predict_proba([processed_query])[0]
            confidence = max(probabilities)

            return intent, confidence
        except Exception as e:
            print(f"Prediction error: {e}")
            return "unknown", 0.0

    def add_training_example(self, query: str, intent: str):
        """Add a new training example (for future retraining)"""
        # This would typically be saved to database for future training
        pass
    
    def retrain_with_feedback(self, feedback_data: List[Dict], original_training_data: List[Tuple[str, str]]) -> Dict:
        """Retrain model incorporating feedback data"""
        # Convert feedback to training samples
        additional_samples = []
        
        for feedback in feedback_data:
            if feedback['feedback'] == 1:  # Positive feedback
                additional_samples.append((feedback['query'], feedback['intent']))
            elif feedback['feedback'] == 0 and feedback['confidence'] > 0.5:
                # Negative feedback on confident predictions - might be wrong intent
                # For now, just reduce confidence in similar predictions
                pass
        
        # Combine with original training data
        # Retrain
        queries, intents = self.get_training_data()
        for query, intent in additional_samples:
             queries.append(self.preprocess_text(query))
             intents.append(intent)
        
        
        if len(queries) == 0:
            return {"success": False, "error": "No training data available"}

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            queries, intents, test_size=0.2, random_state=42, stratify=intents
        )

        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
            ('classifier', LogisticRegression(random_state=42, max_iter=1000))
        ])

        # Train model
        self.pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Save model
        self.save_model()

        return {
            "success": True,
            "accuracy": accuracy,
            "training_samples": len(queries),
            "test_samples": len(X_test)
        }