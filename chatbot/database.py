
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class ChatbotDatabase:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Initialize chatbot-specific tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Bot interaction logs
        c.execute('''
            CREATE TABLE IF NOT EXISTS bot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_email TEXT NOT NULL,
                query TEXT NOT NULL,
                intent TEXT,
                confidence REAL,
                response TEXT,
                feedback INTEGER,  -- 1 for helpful, 0 for not helpful, NULL for no feedback
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                context_data TEXT  -- JSON string for conversation context
            )
        ''')
        
        # Training data for intent classification
        c.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                intent TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'manual',  -- 'manual', 'feedback', 'auto'
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                validated BOOLEAN DEFAULT 1
            )
        ''')
        
        # Intent definitions and metadata
        c.execute('''
            CREATE TABLE IF NOT EXISTS intent_definitions (
                intent TEXT PRIMARY KEY,
                description TEXT,
                function_name TEXT,
                examples TEXT,  -- JSON array of example queries
                active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Model performance tracking
        c.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_type TEXT,
                accuracy REAL,
                f1_score REAL,
                training_samples INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                model_path TEXT
            )
        ''')
        
        # Insert default intents if not exist
        self._insert_default_intents(c)
        
        conn.commit()
        conn.close()
    
    def _insert_default_intents(self, cursor):
        """Insert default intent definitions"""
        default_intents = [
            ('top_selling_products', 'Get top selling products', 'get_top_products', 
             json.dumps(['top selling products', 'best sellers', 'most sold items', 'popular products'])),
            ('low_stock_alerts', 'Check low stock items', 'get_low_stock_products',
             json.dumps(['low stock', 'running low', 'out of stock', 'reorder alerts'])),
            ('revenue_report', 'Revenue and sales summary', 'get_sales_summary',
             json.dumps(['revenue', 'sales report', 'total sales', 'earnings'])),
            ('profit_summary', 'Profit and margin analysis', 'get_profit_analysis',
             json.dumps(['profit', 'margins', 'profitability', 'earnings'])),
            ('inventory_performance', 'Inventory analytics', 'get_inventory_analytics',
             json.dumps(['inventory performance', 'product analytics', 'turnover analysis'])),
            ('expense_analysis', 'Expense tracking and analysis', 'get_expense_summary',
             json.dumps(['expenses', 'costs', 'spending', 'expense report']))
        ]
        
        for intent, desc, func, examples in default_intents:
            cursor.execute('''
                INSERT OR IGNORE INTO intent_definitions (intent, description, function_name, examples)
                VALUES (?, ?, ?, ?)
            ''', (intent, desc, func, examples))
    
    def log_interaction(self, vendor_email: str, query: str, intent: str, 
                       confidence: float, response: str, session_id: str = None,
                       context_data: Dict = None) -> int:
        """Log a bot interaction"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO bot_logs (vendor_email, query, intent, confidence, response, session_id, context_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (vendor_email, query, intent, confidence, response, session_id, 
              json.dumps(context_data) if context_data else None))
        
        log_id = c.lastrowid
        conn.commit()
        conn.close()
        return log_id
    
    def update_feedback(self, log_id: int, feedback: int):
        """Update feedback for a logged interaction"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('UPDATE bot_logs SET feedback = ? WHERE id = ?', (feedback, log_id))
        conn.commit()
        conn.close()
    
    def get_training_data(self) -> List[Tuple[str, str]]:
        """Get all training data for model training"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT query, intent FROM training_data WHERE validated = 1')
        data = c.fetchall()
        conn.close()
        return data
    
    def add_training_sample(self, query: str, intent: str, source: str = 'manual'):
        """Add a new training sample"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO training_data (query, intent, source)
            VALUES (?, ?, ?)
        ''', (query, intent, source))
        
        conn.commit()
        conn.close()
    
    def get_intent_definitions(self) -> Dict[str, Dict]:
        """Get all intent definitions"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM intent_definitions WHERE active = 1')
        intents = {}
        for row in c.fetchall():
            intents[row[0]] = {
                'description': row[1],
                'function_name': row[2],
                'examples': json.loads(row[3]) if row[3] else [],
                'active': row[4]
            }
        
        conn.close()
        return intents
    
    def get_feedback_data(self, days: int = 30) -> List[Dict]:
        """Get feedback data for retraining"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT query, intent, feedback, confidence
            FROM bot_logs 
            WHERE feedback IS NOT NULL 
            AND datetime(timestamp) >= datetime('now', '-{} days')
        '''.format(days))
        
        feedback_data = []
        for row in c.fetchall():
            feedback_data.append({
                'query': row[0],
                'intent': row[1],
                'feedback': row[2],
                'confidence': row[3]
            })
        
        conn.close()
        return feedback_data
    
    def get_analytics_data(self) -> Dict:
        """Get analytics data for dashboard"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Top queries
        c.execute('''
            SELECT query, COUNT(*) as count
            FROM bot_logs
            WHERE datetime(timestamp) >= datetime('now', '-30 days')
            GROUP BY query
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_queries = c.fetchall()
        
        # Intent distribution
        c.execute('''
            SELECT intent, COUNT(*) as count
            FROM bot_logs
            WHERE datetime(timestamp) >= datetime('now', '-30 days')
            GROUP BY intent
            ORDER BY count DESC
        ''')
        intent_distribution = c.fetchall()
        
        # Low confidence queries
        c.execute('''
            SELECT query, intent, confidence
            FROM bot_logs
            WHERE confidence < 0.7 AND datetime(timestamp) >= datetime('now', '-7 days')
            ORDER BY confidence ASC
            LIMIT 10
        ''')
        low_confidence = c.fetchall()
        
        # Feedback stats
        c.execute('''
            SELECT 
                AVG(CASE WHEN feedback = 1 THEN 1.0 ELSE 0.0 END) as satisfaction_rate,
                COUNT(*) as total_feedback
            FROM bot_logs
            WHERE feedback IS NOT NULL AND datetime(timestamp) >= datetime('now', '-30 days')
        ''')
        feedback_stats = c.fetchone()
        
        conn.close()
        
        return {
            'top_queries': top_queries,
            'intent_distribution': intent_distribution,
            'low_confidence': low_confidence,
            'satisfaction_rate': feedback_stats[0] if feedback_stats[0] else 0,
            'total_feedback': feedback_stats[1] if feedback_stats[1] else 0
        }
