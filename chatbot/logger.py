import json
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class ConversationLogger:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path
        self.session_context = {}
        self._ensure_schema()

    def _ensure_schema(self):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("PRAGMA table_info(chatbot_queries)")
            cols = [row[1] for row in c.fetchall()]
            if 'vendor_email' not in cols:
                c.execute("ALTER TABLE chatbot_queries ADD COLUMN vendor_email TEXT")
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Logger schema check: {e}")

    def start_session(self, vendor_email: str) -> str:
        session_id = f"{vendor_email}:{uuid.uuid4()}"

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO chatbot_conversations (session_id, vendor_email, total_queries)
                VALUES (?, ?, 0)
            """, (session_id, vendor_email))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error starting session: {e}")

        self.session_context[session_id] = {
            'vendor_email': vendor_email,
            'last_intent': None,
            'context_data': {},
            'start_time': datetime.now()
        }

        return session_id

    def _validate_session_owner(self, session_id: str, vendor_email: str) -> bool:
        if session_id in self.session_context:
            return self.session_context[session_id].get('vendor_email') == vendor_email
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT vendor_email FROM chatbot_conversations WHERE session_id = ?", (session_id,))
            result = c.fetchone()
            conn.close()
            return result and result[0] == vendor_email
        except Exception:
            return False

    def log_interaction(self, session_id: str, query: str, intent: str,
                        confidence: float, response: str,
                        additional_context: Dict = None) -> Optional[int]:
        try:
            vendor_email = None
            if additional_context:
                vendor_email = additional_context.get('vendor_email')

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute("""
                INSERT INTO chatbot_queries
                (session_id, query, intent, confidence, response, context_data, vendor_email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, query, intent, confidence, response,
                  json.dumps(additional_context) if additional_context else None,
                  vendor_email))

            log_id = c.lastrowid

            c.execute("""
                UPDATE chatbot_conversations
                SET total_queries = total_queries + 1
                WHERE session_id = ?
            """, (session_id,))

            conn.commit()
            conn.close()

            if session_id in self.session_context:
                self.session_context[session_id]['last_intent'] = intent
                if additional_context:
                    self.session_context[session_id]['context_data'].update(additional_context)

            return log_id

        except Exception as e:
            print(f"Error logging interaction: {e}")
            return None

    def update_feedback(self, log_id: int, feedback: int, vendor_email: str = None):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            if vendor_email:
                c.execute("""
                    UPDATE chatbot_queries
                    SET feedback = ?
                    WHERE id = ? AND vendor_email = ?
                """, (feedback, log_id, vendor_email))
            else:
                c.execute("""
                    UPDATE chatbot_queries
                    SET feedback = ?
                    WHERE id = ?
                """, (feedback, log_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating feedback: {e}")

    def resolve_contextual_query(self, session_id: str, query: str) -> str:
        if session_id not in self.session_context:
            return query

        context = self.session_context[session_id]
        query_lower = query.lower()

        if any(word in query_lower for word in ['more', 'details', 'show me', 'tell me more']):
            last_intent = context.get('last_intent')
            if last_intent == 'top_selling_products':
                return 'show me detailed top selling products analysis'
            elif last_intent == 'low_stock_alerts':
                return 'show me detailed low stock analysis'
            elif last_intent == 'revenue_report':
                return 'show me detailed revenue analysis'

        return query

    def get_session_history(self, session_id: str, vendor_email: str = None) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            if vendor_email:
                c.execute("""
                    SELECT query, intent, confidence, response, timestamp, feedback
                    FROM chatbot_queries
                    WHERE session_id = ? AND vendor_email = ?
                    ORDER BY timestamp ASC
                """, (session_id, vendor_email))
            else:
                c.execute("""
                    SELECT query, intent, confidence, response, timestamp, feedback
                    FROM chatbot_queries
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                """, (session_id,))

            results = c.fetchall()
            conn.close()

            return [{
                'query': row[0], 'intent': row[1], 'confidence': row[2],
                'response': row[3], 'timestamp': row[4], 'feedback': row[5]
            } for row in results]

        except Exception as e:
            print(f"Error getting session history: {e}")
            return []

    def get_analytics_data(self, vendor_email: str = None) -> Dict:
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            vendor_filter = ""
            params = ()
            if vendor_email:
                vendor_filter = "WHERE cq.vendor_email = ?"
                params = (vendor_email,)

            c.execute(f"""
                SELECT COUNT(*) as total_queries,
                       AVG(cq.confidence) as avg_confidence,
                       SUM(CASE WHEN cq.feedback = 1 THEN 1 ELSE 0 END) as positive_feedback,
                       SUM(CASE WHEN cq.feedback = 0 THEN 1 ELSE 0 END) as negative_feedback
                FROM chatbot_queries cq
                {vendor_filter}
            """, params)

            stats = c.fetchone()

            c.execute(f"""
                SELECT cq.intent, COUNT(*) as count
                FROM chatbot_queries cq
                {vendor_filter}
                GROUP BY cq.intent
                ORDER BY count DESC
                LIMIT 10
            """, params)

            intent_dist = c.fetchall()
            conn.close()

            return {
                'total_queries': stats[0] or 0,
                'avg_confidence': round(stats[1] or 0, 2),
                'positive_feedback': stats[2] or 0,
                'negative_feedback': stats[3] or 0,
                'intent_distribution': [{'intent': r[0], 'count': r[1]} for r in intent_dist]
            }
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}

    def end_session(self, session_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                UPDATE chatbot_conversations
                SET end_time = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (session_id,))
            conn.commit()
            conn.close()

            if session_id in self.session_context:
                del self.session_context[session_id]
        except Exception as e:
            print(f"Error ending session: {e}")
