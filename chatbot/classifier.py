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
        """Load trained model if it exists, otherwise train from scratch"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.pipeline = pickle.load(f)
                print(f"Model loaded from {self.model_path}")
            except Exception as e:
                print(f"Error loading model: {e}. Retraining...")
                self._train_fresh()
        else:
            print("No model found. Training from scratch...")
            self._train_fresh()

    def _train_fresh(self):
        """Train a fresh model using all training data"""
        queries, intents = self.get_training_data()
        texts = [self.preprocess_text(q) for q in queries]

        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=2000, ngram_range=(1, 3))),
            ('classifier', LogisticRegression(random_state=42, max_iter=1000, C=5.0))
        ])

        self.pipeline.fit(texts, intents)
        self.save_model()
        print(f"Model trained with {len(texts)} samples")

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
            ("what sells the most", "top_selling_products"),
            ("show best sellers", "top_selling_products"),
            ("my top items", "top_selling_products"),
            ("highest selling products", "top_selling_products"),
            ("what products are doing well", "top_selling_products"),
            ("show me my top selling products", "top_selling_products"),
            ("what are my top sellers", "top_selling_products"),
            ("which items are popular", "top_selling_products"),
            ("what products have highest sales", "top_selling_products"),
            ("top 5 products by sales", "top_selling_products"),

            # Low stock alerts / restock
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
            ("do i need to restock anything", "low_stock_alerts"),
            ("do i need to reorder", "low_stock_alerts"),
            ("should i restock", "low_stock_alerts"),
            ("what needs restocking", "low_stock_alerts"),
            ("any items running low", "low_stock_alerts"),
            ("am i running out of anything", "low_stock_alerts"),
            ("what products need reordering", "low_stock_alerts"),
            ("show me low stock alerts", "low_stock_alerts"),
            ("what items are out of stock", "low_stock_alerts"),
            ("which items need to be reordered", "low_stock_alerts"),
            ("restock alerts", "low_stock_alerts"),
            ("restock recommendations", "low_stock_alerts"),
            ("what should i restock", "low_stock_alerts"),
            ("what should i reorder", "low_stock_alerts"),
            ("need to restock", "low_stock_alerts"),
            ("need to reorder", "low_stock_alerts"),
            ("items out of stock", "low_stock_alerts"),
            ("products out of stock", "low_stock_alerts"),
            ("running low on stock", "low_stock_alerts"),
            ("low inventory items", "low_stock_alerts"),
            ("what is low in stock", "low_stock_alerts"),
            ("check stock levels", "low_stock_alerts"),
            ("which products are low", "low_stock_alerts"),

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
            ("give me a revenue report", "revenue_report"),
            ("monthly sales report", "revenue_report"),
            ("what is my total revenue", "revenue_report"),
            ("how are my sales doing", "revenue_report"),
            ("show sales data", "revenue_report"),
            ("revenue this month", "revenue_report"),
            ("how much revenue did i make", "revenue_report"),
            ("what is my revenue", "revenue_report"),
            ("sales figures", "revenue_report"),
            ("show me sales numbers", "revenue_report"),

            # Profit analysis
            ("profit margin", "profit_summary"),
            ("how much profit", "profit_summary"),
            ("profit analysis", "profit_summary"),
            ("profitability", "profit_summary"),
            ("gross profit", "profit_summary"),
            ("net profit", "profit_summary"),
            ("profit report", "profit_summary"),
            ("profit and loss", "profit_summary"),
            ("what is my profit", "profit_summary"),
            ("show me profit summary", "profit_summary"),
            ("what is my profit margin", "profit_summary"),
            ("how profitable am i", "profit_summary"),
            ("am i making profit", "profit_summary"),
            ("profit breakdown", "profit_summary"),
            ("what is my profit summary", "profit_summary"),
            ("show profit analysis", "profit_summary"),
            ("how much money am i making", "profit_summary"),
            ("what are my margins", "profit_summary"),

            # Inventory performance
            ("inventory analysis", "inventory_performance"),
            ("inventory performance", "inventory_performance"),
            ("stock analysis", "inventory_performance"),
            ("turnover rate", "inventory_performance"),
            ("inventory turnover", "inventory_performance"),
            ("stock performance", "inventory_performance"),
            ("inventory metrics", "inventory_performance"),
            ("stock velocity", "inventory_performance"),
            ("show inventory performance", "inventory_performance"),
            ("how is my inventory performing", "inventory_performance"),
            ("analyze my inventory", "inventory_performance"),
            ("inventory health", "inventory_performance"),
            ("how is my stock doing", "inventory_performance"),
            ("inventory overview", "inventory_performance"),
            ("stock movement analysis", "inventory_performance"),
            ("inventory efficiency", "inventory_performance"),

            # Expenses
            ("show expenses", "expense_analysis"),
            ("expense report", "expense_analysis"),
            ("business expenses", "expense_analysis"),
            ("cost analysis", "expense_analysis"),
            ("spending report", "expense_analysis"),
            ("operational costs", "expense_analysis"),
            ("expense summary", "expense_analysis"),
            ("what are my expenses", "expense_analysis"),
            ("how much am i spending", "expense_analysis"),
            ("show me my costs", "expense_analysis"),
            ("expense breakdown", "expense_analysis"),
            ("where is my money going", "expense_analysis"),
            ("cost breakdown", "expense_analysis"),
            ("total expenses", "expense_analysis"),
            ("show spending", "expense_analysis"),

            # Dead stock
            ("dead stock", "dead_stock_analysis"),
            ("show me dead stock", "dead_stock_analysis"),
            ("stagnant inventory", "dead_stock_analysis"),
            ("products not selling", "dead_stock_analysis"),
            ("slow moving items", "dead_stock_analysis"),
            ("items not moving", "dead_stock_analysis"),
            ("what is not selling", "dead_stock_analysis"),
            ("inventory not moving", "dead_stock_analysis"),
            ("stuck inventory", "dead_stock_analysis"),
            ("unsold products", "dead_stock_analysis"),

            # Inventory turnover
            ("inventory turnover ratio", "inventory_turnover"),
            ("what is my turnover ratio", "inventory_turnover"),
            ("how fast is my inventory turning", "inventory_turnover"),
            ("stock rotation rate", "inventory_turnover"),
            ("what is my inventory turnover ratio", "inventory_turnover"),
            ("inventory velocity", "inventory_turnover"),
            ("how quickly does stock move", "inventory_turnover"),
            ("turnover analysis", "inventory_turnover"),

            # EOQ
            ("calculate eoq", "ideal_order_quantity"),
            ("economic order quantity", "ideal_order_quantity"),
            ("ideal order quantity", "ideal_order_quantity"),
            ("optimal order quantity", "ideal_order_quantity"),
            ("how much should i order", "ideal_order_quantity"),
            ("calculate eoq for my products", "ideal_order_quantity"),
            ("what is the best quantity to order", "ideal_order_quantity"),
            ("order quantity calculation", "ideal_order_quantity"),

            # Monthly performance
            ("monthly performance", "monthly_performance"),
            ("how did i do this month", "monthly_performance"),
            ("this month summary", "monthly_performance"),
            ("monthly summary", "monthly_performance"),
            ("how am i doing this month", "monthly_performance"),
            ("performance this month", "monthly_performance"),
            ("monthly business report", "monthly_performance"),
            ("month end report", "monthly_performance"),

            # Product margins
            ("product margins", "product_margin"),
            ("margin analysis", "product_margin"),
            ("profit margin per product", "product_margin"),
            ("which products are most profitable", "product_margin"),
            ("product profitability", "product_margin"),
            ("margin breakdown", "product_margin"),
            ("show product margins", "product_margin"),
            ("product cost analysis", "product_margin"),

            # Reorder Point (ROP)
            ("what is my reorder point", "reorder_point"),
            ("calculate reorder point", "reorder_point"),
            ("when should i reorder", "reorder_point"),
            ("at what level should i reorder", "reorder_point"),
            ("reorder point analysis", "reorder_point"),
            ("show reorder points", "reorder_point"),
            ("when to place a new order", "reorder_point"),
            ("rop analysis", "reorder_point"),
            ("reorder threshold", "reorder_point"),
            ("at what stock level should i reorder", "reorder_point"),
            ("what is the reorder level for my products", "reorder_point"),
            ("calculate rop for my inventory", "reorder_point"),
            ("trigger point for reordering", "reorder_point"),
            ("when does my stock hit reorder point", "reorder_point"),

            # Safety stock
            ("calculate safety stock", "safety_stock_check"),
            ("what is my safety stock", "safety_stock_check"),
            ("do i have enough safety stock", "safety_stock_check"),
            ("buffer stock analysis", "safety_stock_check"),
            ("minimum stock level", "safety_stock_check"),
            ("safety inventory level", "safety_stock_check"),
            ("how much buffer stock do i need", "safety_stock_check"),
            ("safety stock calculation", "safety_stock_check"),
            ("what should my safety stock be", "safety_stock_check"),
            ("how much extra stock should i keep", "safety_stock_check"),
            ("calculate buffer inventory", "safety_stock_check"),
            ("safety stock for my products", "safety_stock_check"),

            # Days Sales of Inventory (DSI)
            ("days sales of inventory", "days_sales_inventory"),
            ("how many days to sell my inventory", "days_sales_inventory"),
            ("calculate dsi", "days_sales_inventory"),
            ("average days to sell stock", "days_sales_inventory"),
            ("how long does it take to sell my inventory", "days_sales_inventory"),
            ("inventory days", "days_sales_inventory"),
            ("days of inventory remaining", "days_sales_inventory"),
            ("how quickly am i selling inventory", "days_sales_inventory"),
            ("dsi analysis", "days_sales_inventory"),
            ("what is my dsi", "days_sales_inventory"),
            ("inventory sell through days", "days_sales_inventory"),
            ("how fast is inventory selling", "days_sales_inventory"),

            # GMROI
            ("calculate gmroi", "gmroi"),
            ("gross margin return on investment", "gmroi"),
            ("what is my gmroi", "gmroi"),
            ("return on inventory investment", "gmroi"),
            ("how much do i earn per dollar of inventory", "gmroi"),
            ("inventory roi", "gmroi"),
            ("profitability per inventory dollar", "gmroi"),
            ("gmroi analysis", "gmroi"),
            ("inventory return analysis", "gmroi"),
            ("gross margin on inventory", "gmroi"),
            ("what is my return on inventory", "gmroi"),
            ("how profitable is my inventory investment", "gmroi"),

            # ABC Analysis
            ("abc analysis", "abc_analysis"),
            ("abc classification", "abc_analysis"),
            ("categorize my inventory", "abc_analysis"),
            ("classify my products", "abc_analysis"),
            ("product classification by value", "abc_analysis"),
            ("inventory categorization", "abc_analysis"),
            ("which are my a b c items", "abc_analysis"),
            ("show abc inventory categories", "abc_analysis"),
            ("pareto analysis of inventory", "abc_analysis"),
            ("which products are most important", "abc_analysis"),
            ("high value vs low value products", "abc_analysis"),
            ("product priority classification", "abc_analysis"),
            ("categorize products by sales value", "abc_analysis"),
            ("show me my a category items", "abc_analysis"),

            # Fill Rate
            ("what is my fill rate", "fill_rate"),
            ("order fulfillment rate", "fill_rate"),
            ("how many orders am i fulfilling", "fill_rate"),
            ("fulfillment percentage", "fill_rate"),
            ("order completion rate", "fill_rate"),
            ("calculate fill rate", "fill_rate"),
            ("customer order fill rate", "fill_rate"),
            ("shipped orders percentage", "fill_rate"),
            ("how well am i fulfilling orders", "fill_rate"),
            ("what percentage of orders are shipped", "fill_rate"),

            # Inventory to Sales Ratio
            ("inventory to sales ratio", "inventory_to_sales_ratio"),
            ("stock to sales ratio", "inventory_to_sales_ratio"),
            ("how much inventory per sale", "inventory_to_sales_ratio"),
            ("inventory vs sales ratio", "inventory_to_sales_ratio"),
            ("calculate inventory to sales ratio", "inventory_to_sales_ratio"),
            ("inventory compared to sales", "inventory_to_sales_ratio"),
            ("how does my inventory compare to sales", "inventory_to_sales_ratio"),
            ("inventory sales balance", "inventory_to_sales_ratio"),
            ("am i overstocked relative to sales", "inventory_to_sales_ratio"),
            ("stock vs revenue ratio", "inventory_to_sales_ratio"),

            # Stock cover / duration
            ("how long will my stock last", "stock_cover"),
            ("stock cover duration", "stock_cover"),
            ("days of stock cover", "stock_cover"),
            ("when will my stock run out", "stock_cover"),
            ("how many days of stock do i have", "stock_cover"),
            ("inventory duration analysis", "stock_cover"),
            ("stock coverage", "stock_cover"),
            ("how long until i run out", "stock_cover"),
            ("stock lasting days", "stock_cover"),
            ("will my stock last this month", "stock_cover"),

            # Clearance strategy
            ("clearance strategy", "clearance_strategy"),
            ("how to clear slow stock", "clearance_strategy"),
            ("liquidation strategy", "clearance_strategy"),
            ("how to get rid of excess inventory", "clearance_strategy"),
            ("move slow moving stock", "clearance_strategy"),
            ("how to sell off old inventory", "clearance_strategy"),
            ("clearance sale recommendations", "clearance_strategy"),
            ("what to do with unsold inventory", "clearance_strategy"),
            ("stock clearance plan", "clearance_strategy"),
            ("how to reduce excess stock", "clearance_strategy"),

            # Sales problems
            ("what is dragging my sales", "sales_problems"),
            ("why are my sales down", "sales_problems"),
            ("sales problems", "sales_problems"),
            ("why is revenue dropping", "sales_problems"),
            ("sales issues", "sales_problems"),
            ("what is wrong with my sales", "sales_problems"),
            ("poor sales analysis", "sales_problems"),
            ("sales declining", "sales_problems"),
            ("why am i not selling", "sales_problems"),
            ("diagnose sales problems", "sales_problems"),

            # General business
            ("how is my business doing", "general_business"),
            ("business overview", "general_business"),
            ("business summary", "general_business"),
            ("give me a business report", "general_business"),
            ("overall business health", "general_business"),

            # Best selling product
            ("best selling product", "best_selling_product"),
            ("top selling product", "best_selling_product"),
            ("what is my best seller", "best_selling_product"),
            ("number one product", "best_selling_product"),
            ("most popular product", "best_selling_product"),
            ("highest selling product", "best_selling_product"),
            ("what product sells the best", "best_selling_product"),

            # Restock needed
            ("what needs restocking now", "restock_needed"),
            ("restock recommendations", "restock_needed"),
            ("items that need reordering", "restock_needed"),
            ("which items to restock", "restock_needed"),
            ("give me a restock list", "restock_needed"),
            ("restock checklist", "restock_needed"),

            # Profit per item
            ("profit per item", "profit_per_item"),
            ("average profit per unit", "profit_per_item"),
            ("profit margin per product", "profit_per_item"),
            ("how much am i making per item", "profit_per_item"),
            ("profit on each product", "profit_per_item"),
            ("margin per unit", "profit_per_item"),

            # Product demand
            ("is this product still in demand", "product_demand"),
            ("demand for my products", "product_demand"),
            ("which products are in demand", "product_demand"),
            ("market demand analysis", "product_demand"),
            ("product popularity", "product_demand"),

            # Unknown/general queries
            ("hello", "unknown"),
            ("hi there", "unknown"),
            ("help me", "unknown"),
            ("what can you do", "unknown"),
            ("thanks a lot", "unknown"),
            ("thank you very much", "unknown"),
            ("good morning", "unknown"),
            ("how are you", "unknown"),
            ("who are you", "unknown"),
            ("goodbye", "unknown"),
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
