import sqlite3
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ChatbotDatabase:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path
        self.init_chatbot_tables()

    def init_chatbot_tables(self):
        """Initialize chatbot-specific tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Conversation logs table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                vendor_email TEXT NOT NULL,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                total_queries INTEGER DEFAULT 0
            )
        ''')

        # Query logs table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                query TEXT NOT NULL,
                intent TEXT,
                confidence REAL,
                response TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                feedback INTEGER DEFAULT NULL,
                context_data TEXT
            )
        ''')

        # Training data table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                intent TEXT NOT NULL,
                response TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_validated BOOLEAN DEFAULT 0
            )
        ''')

        # Analytics table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                additional_data TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def get_analytics_data(self) -> Dict:
        """Get analytics data for dashboard"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Total queries
        c.execute("SELECT COUNT(*) FROM chatbot_queries")
        total_queries = c.fetchone()[0]

        # Average confidence
        c.execute("SELECT AVG(confidence) FROM chatbot_queries WHERE confidence IS NOT NULL")
        avg_confidence = c.fetchone()[0] or 0

        # Intent distribution
        c.execute("""
            SELECT intent, COUNT(*) as count 
            FROM chatbot_queries 
            WHERE intent IS NOT NULL 
            GROUP BY intent 
            ORDER BY count DESC
        """)
        intent_distribution = c.fetchall()

        # Feedback stats
        c.execute("SELECT feedback, COUNT(*) FROM chatbot_queries WHERE feedback IS NOT NULL GROUP BY feedback")
        feedback_stats = c.fetchall()

        # Recent queries
        c.execute("""
            SELECT query, intent, confidence, response, timestamp 
            FROM chatbot_queries 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        recent_queries = c.fetchall()

        conn.close()

        return {
            'total_queries': total_queries,
            'avg_confidence': round(avg_confidence, 2),
            'intent_distribution': intent_distribution,
            'feedback_stats': feedback_stats,
            'recent_queries': recent_queries
        }