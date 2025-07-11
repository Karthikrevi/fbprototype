import json
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ConversationLogger:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path
        self.active_sessions = {}

    def start_session(self, vendor_email: str) -> str:
        """Start a new conversation session"""
        session_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO chatbot_conversations (session_id, vendor_email, total_queries)
            VALUES (?, ?, ?)
        """, (session_id, vendor_email, 0))

        conn.commit()
        conn.close()

        self.active_sessions[session_id] = {
            'vendor_email': vendor_email,
            'start_time': datetime.now(),
            'query_count': 0,
            'context': []
        }

        return session_id

    def log_interaction(self, session_id: str, query: str, intent: str, 
                       confidence: float, response: str, 
                       additional_context: Dict = None) -> int:
        """Log a chatbot interaction"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        context_json = json.dumps(additional_context) if additional_context else None

        c.execute("""
            INSERT INTO chatbot_queries 
            (session_id, query, intent, confidence, response, context_data)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, query, intent, confidence, response, context_json))

        log_id = c.lastrowid

        # Update session query count
        c.execute("""
            UPDATE chatbot_conversations 
            SET total_queries = total_queries + 1 
            WHERE session_id = ?
        """, (session_id,))

        conn.commit()
        conn.close()

        # Update active session
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['query_count'] += 1
            self.active_sessions[session_id]['context'].append({
                'query': query,
                'intent': intent,
                'timestamp': datetime.now().isoformat()
            })

        return log_id

    def update_feedback(self, log_id: int, feedback: int):
        """Update feedback for a logged interaction"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            UPDATE chatbot_queries 
            SET feedback = ? 
            WHERE id = ?
        """, (feedback, log_id))

        conn.commit()
        conn.close()

    def get_session_context(self, session_id: str) -> List[Dict]:
        """Get conversation context for a session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]['context']

        # Fallback to database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT query, intent, timestamp 
            FROM chatbot_queries 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (session_id,))

        context = []
        for row in c.fetchall():
            context.append({
                'query': row[0],
                'intent': row[1],
                'timestamp': row[2]
            })

        conn.close()
        return context

    def resolve_contextual_query(self, session_id: str, query: str) -> str:
        """Resolve pronouns and contextual references in queries"""
        context = self.get_session_context(session_id)

        if not context:
            return query

        query_lower = query.lower()

        # Simple pronoun resolution
        if any(word in query_lower for word in ['them', 'those', 'these', 'it']):
            last_intent = context[0].get('intent') if context else None

            if last_intent == 'top_selling_products':
                query = query.replace('them', 'top selling products')
                query = query.replace('those', 'top selling products')
                query = query.replace('these', 'top selling products')
            elif last_intent == 'low_stock_alerts':
                query = query.replace('them', 'low stock products')
                query = query.replace('those', 'low stock products')
                query = query.replace('these', 'low stock products')

        return query

    def end_session(self, session_id: str):
        """End a conversation session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            UPDATE chatbot_conversations 
            SET end_time = CURRENT_TIMESTAMP 
            WHERE session_id = ?
        """, (session_id,))

        conn.commit()
        conn.close()