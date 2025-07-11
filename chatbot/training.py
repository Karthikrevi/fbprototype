
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List
from .database import ChatbotDatabase
from .classifier import IntentClassifier
from .vector_matcher import VectorMatcher

class TrainingManager:
    def __init__(self, db_path: str = 'erp.db'):
        self.db = ChatbotDatabase(db_path)
        self.classifier = IntentClassifier()
        self.vector_matcher = VectorMatcher()
        
        # Setup automatic retraining schedule
        self.setup_training_schedule()
    
    def initial_training(self) -> Dict:
        """Perform initial training with default data"""
        print("Starting initial training...")
        
        # Add default training samples
        self._add_default_training_data()
        
        # Get training data
        training_data = self.db.get_training_data()
        
        if len(training_data) < 5:
            print("Not enough training data for initial training.")
            return {'success': False, 'error': 'Insufficient training data'}
        
        # Train classifier
        result = self.classifier.train(training_data)
        
        # Save performance metrics
        if result.get('success'):
            self._save_performance_metrics(result)
        
        print(f"Initial training completed. Accuracy: {result.get('accuracy', 0):.2f}")
        return result
    
    def _add_default_training_data(self):
        """Add comprehensive default training samples"""
        default_samples = [
            # Top selling products
            ("what are my best selling products", "top_selling_products"),
            ("show me top performers", "top_selling_products"),
            ("which products sell the most", "top_selling_products"),
            ("most popular items", "top_selling_products"),
            ("best sellers this month", "top_selling_products"),
            ("top moving products", "top_selling_products"),
            ("what sells best", "top_selling_products"),
            ("highest selling items", "top_selling_products"),
            
            # Low stock alerts
            ("what items are low in stock", "low_stock_alerts"),
            ("running low on inventory", "low_stock_alerts"),
            ("which products need reordering", "low_stock_alerts"),
            ("stock alerts", "low_stock_alerts"),
            ("items to reorder", "low_stock_alerts"),
            ("out of stock products", "low_stock_alerts"),
            ("low inventory warning", "low_stock_alerts"),
            ("products running out", "low_stock_alerts"),
            
            # Revenue reports
            ("what's my total revenue", "revenue_report"),
            ("show me sales report", "revenue_report"),
            ("how much did I earn", "revenue_report"),
            ("monthly revenue", "revenue_report"),
            ("sales summary", "revenue_report"),
            ("total earnings", "revenue_report"),
            ("revenue this month", "revenue_report"),
            ("sales performance", "revenue_report"),
            
            # Profit analysis
            ("what's my profit margin", "profit_summary"),
            ("am I making profit", "profit_summary"),
            ("profit analysis", "profit_summary"),
            ("how profitable am I", "profit_summary"),
            ("margin analysis", "profit_summary"),
            ("profit summary", "profit_summary"),
            ("profitability report", "profit_summary"),
            ("net profit", "profit_summary"),
            
            # Inventory performance
            ("inventory performance", "inventory_performance"),
            ("product analytics", "inventory_performance"),
            ("turnover analysis", "inventory_performance"),
            ("inventory insights", "inventory_performance"),
            ("product performance", "inventory_performance"),
            ("inventory metrics", "inventory_performance"),
            ("stock analysis", "inventory_performance"),
            ("inventory reports", "inventory_performance"),
            
            # Expense analysis
            ("what are my expenses", "expense_analysis"),
            ("show me costs", "expense_analysis"),
            ("expense report", "expense_analysis"),
            ("spending analysis", "expense_analysis"),
            ("cost breakdown", "expense_analysis"),
            ("expense summary", "expense_analysis"),
            ("business costs", "expense_analysis"),
            ("operational expenses", "expense_analysis")
        ]
        
        for query, intent in default_samples:
            self.db.add_training_sample(query, intent, 'default')
    
    def retrain_from_feedback(self, days: int = 7) -> Dict:
        """Retrain classifier based on recent feedback"""
        print(f"Retraining from feedback data (last {days} days)...")
        
        # Get feedback data
        feedback_data = self.db.get_feedback_data(days)
        
        if len(feedback_data) < 5:
            print("Not enough feedback data for retraining.")
            return {'success': False, 'error': 'Insufficient feedback data'}
        
        # Get original training data
        original_training_data = self.db.get_training_data()
        
        # Retrain classifier
        result = self.classifier.retrain_with_feedback(feedback_data, original_training_data)
        
        # Save performance metrics
        if result.get('success'):
            self._save_performance_metrics(result)
        
        print(f"Retraining completed. New accuracy: {result.get('accuracy', 0):.2f}")
        return result
    
    def update_vector_database(self):
        """Update vector database with recent positive interactions"""
        print("Updating vector database...")
        
        # Get recent positive interactions
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT query, response, intent
            FROM bot_logs
            WHERE feedback = 1 AND datetime(timestamp) >= datetime('now', '-30 days')
        ''')
        
        positive_logs = []
        for row in c.fetchall():
            positive_logs.append({
                'query': row[0],
                'response': row[1],
                'intent': row[2]
            })
        
        conn.close()
        
        # Update vector matcher
        self.vector_matcher.update_from_logs(positive_logs)
        
        print(f"Vector database updated with {len(positive_logs)} positive interactions")
    
    def _save_performance_metrics(self, results: Dict):
        """Save model performance metrics"""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO model_performance (model_type, accuracy, f1_score, training_samples)
            VALUES (?, ?, ?, ?)
        ''', ('intent_classifier', results.get('accuracy', 0), 
              results.get('f1_score', 0), results.get('training_samples', 0)))
        
        conn.commit()
        conn.close()
    
    def setup_training_schedule(self):
        """Setup automatic retraining schedule"""
        # Schedule weekly retraining
        schedule.every().monday.at("02:00").do(self.scheduled_retrain)
        
        # Schedule daily vector database updates
        schedule.every().day.at("01:00").do(self.update_vector_database)
    
    def scheduled_retrain(self):
        """Scheduled retraining function"""
        try:
            print("Running scheduled retraining...")
            result = self.retrain_from_feedback(days=7)
            
            if result.get('success'):
                print(f"Scheduled retraining successful. Accuracy: {result.get('accuracy', 0):.2f}")
            else:
                print(f"Scheduled retraining failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error during scheduled retraining: {e}")
    
    def run_scheduler(self):
        """Run the training scheduler (call this in a background thread)"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_training_stats(self) -> Dict:
        """Get training statistics"""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        # Get latest performance
        c.execute('''
            SELECT accuracy, f1_score, training_samples, timestamp
            FROM model_performance
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        latest_performance = c.fetchone()
        
        # Get training data count
        c.execute('SELECT COUNT(*) FROM training_data WHERE validated = 1')
        training_samples = c.fetchone()[0]
        
        # Get feedback count
        c.execute('SELECT COUNT(*) FROM bot_logs WHERE feedback IS NOT NULL')
        feedback_count = c.fetchone()[0]
        
        conn.close()
        
        stats = {
            'training_samples': training_samples,
            'feedback_count': feedback_count,
            'vector_stats': self.vector_matcher.get_stats()
        }
        
        if latest_performance:
            stats.update({
                'latest_accuracy': latest_performance[0],
                'latest_f1_score': latest_performance[1],
                'last_training_samples': latest_performance[2],
                'last_training_time': latest_performance[3]
            })
        
        return stats
