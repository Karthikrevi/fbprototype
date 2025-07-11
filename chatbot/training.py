import schedule
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
from .classifier import IntentClassifier
from .vector_matcher import VectorMatcher

class TrainingManager:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path
        self.classifier = IntentClassifier()
        self.vector_matcher = VectorMatcher()

    def initial_training(self) -> Dict:
        """Perform initial training of the model"""
        print("Starting initial training...")

        try:
            result = self.classifier.train()

            if result.get('success'):
                print(f"Initial training completed. Accuracy: {result.get('accuracy', 0):.2f}")
                return {
                    'success': True,
                    'accuracy': result.get('accuracy'),
                    'message': 'Initial training completed successfully'
                }
            else:
                print(f"Initial training failed: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Training failed')
                }

        except Exception as e:
            print(f"Training error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def retrain_from_feedback(self, days: int = 30) -> Dict:
        """Retrain model using feedback data from the last N days"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get feedback data from last N days
        c.execute("""
            SELECT query, intent, feedback 
            FROM chatbot_queries 
            WHERE timestamp >= date('now', '-{} days') 
            AND feedback IS NOT NULL
        """.format(days))

        feedback_data = c.fetchall()
        conn.close()

        if len(feedback_data) < 10:  # Need minimum data for retraining
            return {
                'success': False,
                'error': f'Insufficient feedback data. Need at least 10 examples, got {len(feedback_data)}'
            }

        # Process feedback data
        positive_examples = []
        negative_examples = []

        for query, intent, feedback in feedback_data:
            if feedback == 1:  # Positive feedback
                positive_examples.append((query, intent))
            elif feedback == 0:  # Negative feedback
                negative_examples.append((query, intent))

        # For negative examples, we might want to relabel them or use them differently
        # For now, we'll just use positive examples for retraining

        if len(positive_examples) < 5:
            return {
                'success': False,
                'error': 'Insufficient positive feedback for retraining'
            }

        try:
            # Retrain classifier (this would involve updating training data)
            result = self.classifier.train()

            return {
                'success': True,
                'positive_examples': len(positive_examples),
                'negative_examples': len(negative_examples),
                'accuracy': result.get('accuracy', 0)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def schedule_retraining(self):
        """Schedule automatic retraining"""
        # Schedule weekly retraining
        schedule.every().sunday.at("02:00").do(self.retrain_from_feedback, days=7)

        # Schedule monthly comprehensive retraining
        schedule.every().month.do(self.retrain_from_feedback, days=30)

    def run_scheduled_tasks(self):
        """Run scheduled training tasks (should be called in a background thread)"""
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour

    def add_training_example(self, query: str, intent: str, response: str = None):
        """Add a new training example to the database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO chatbot_training_data (query, intent, response)
            VALUES (?, ?, ?)
        """, (query, intent, response))

        conn.commit()
        conn.close()

    def validate_training_data(self) -> Dict:
        """Validate and clean training data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get unvalidated training data
        c.execute("""
            SELECT id, query, intent, response 
            FROM chatbot_training_data 
            WHERE is_validated = 0
        """)

        unvalidated = c.fetchall()
        validated_count = 0

        for data_id, query, intent, response in unvalidated:
            # Simple validation rules
            if len(query.strip()) > 5 and intent.strip():
                c.execute("""
                    UPDATE chatbot_training_data 
                    SET is_validated = 1 
                    WHERE id = ?
                """, (data_id,))
                validated_count += 1

        conn.commit()
        conn.close()

        return {
            'total_unvalidated': len(unvalidated),
            'validated': validated_count,
            'success': True
        }