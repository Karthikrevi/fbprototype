
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .database import ChatbotDatabase

class ConversationLogger:
    def __init__(self, db_path: str = 'erp.db'):
        self.db = ChatbotDatabase(db_path)
        self.active_sessions = {}  # In-memory session storage
        self.session_timeout = 30  # minutes
    
    def start_session(self, vendor_email: str) -> str:
        """Start a new conversation session"""
        session_id = str(uuid.uuid4())
        
        self.active_sessions[session_id] = {
            'vendor_email': vendor_email,
            'start_time': datetime.now(),
            'last_activity': datetime.now(),
            'context': {},
            'conversation_history': []
        }
        
        return session_id
    
    def log_interaction(self, session_id: str, query: str, intent: str, 
                       confidence: float, response: str, 
                       additional_context: Dict = None) -> int:
        """Log a conversation interaction"""
        session = self.active_sessions.get(session_id)
        
        if not session:
            # Create new session if not found
            vendor_email = additional_context.get('vendor_email', 'unknown')
            session_id = self.start_session(vendor_email)
            session = self.active_sessions[session_id]
        
        # Update session activity
        session['last_activity'] = datetime.now()
        
        # Add to conversation history
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'intent': intent,
            'confidence': confidence,
            'response': response
        }
        session['conversation_history'].append(interaction)
        
        # Update context based on intent
        self._update_context(session, intent, query, additional_context or {})
        
        # Log to database
        log_id = self.db.log_interaction(
            vendor_email=session['vendor_email'],
            query=query,
            intent=intent,
            confidence=confidence,
            response=response,
            session_id=session_id,
            context_data=session['context']
        )
        
        return log_id
    
    def _update_context(self, session: Dict, intent: str, query: str, additional_context: Dict):
        """Update conversation context"""
        context = session['context']
        
        # Update last intent and query
        context['last_intent'] = intent
        context['last_query'] = query
        context['interaction_count'] = context.get('interaction_count', 0) + 1
        
        # Intent-specific context updates
        if intent == 'revenue_report':
            context['last_topic'] = 'revenue'
            # Extract time period if mentioned
            time_period = self._extract_time_period(query)
            if time_period:
                context['time_period'] = time_period
        
        elif intent == 'top_selling_products':
            context['last_topic'] = 'products'
            context['product_focus'] = 'top_selling'
        
        elif intent == 'low_stock_alerts':
            context['last_topic'] = 'inventory'
            context['inventory_focus'] = 'low_stock'
        
        elif intent == 'profit_summary':
            context['last_topic'] = 'profit'
        
        elif intent == 'inventory_performance':
            context['last_topic'] = 'inventory'
            context['inventory_focus'] = 'performance'
        
        elif intent == 'expense_analysis':
            context['last_topic'] = 'expenses'
        
        # Update with additional context
        context.update(additional_context)
        
        # Keep context size manageable
        if len(context) > 20:
            # Remove oldest non-essential keys
            essential_keys = ['last_intent', 'last_topic', 'interaction_count', 'time_period']
            old_keys = [k for k in context.keys() if k not in essential_keys]
            for key in old_keys[:5]:  # Remove up to 5 old keys
                del context[key]
    
    def _extract_time_period(self, query: str) -> Optional[str]:
        """Extract time period from query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['today', 'this day']):
            return 'today'
        elif any(word in query_lower for word in ['yesterday', 'last day']):
            return 'yesterday'
        elif any(word in query_lower for word in ['this week', 'week']):
            return 'this_week'
        elif any(word in query_lower for word in ['last week', 'previous week']):
            return 'last_week'
        elif any(word in query_lower for word in ['this month', 'month']):
            return 'this_month'
        elif any(word in query_lower for word in ['last month', 'previous month']):
            return 'last_month'
        elif any(word in query_lower for word in ['this year', 'year']):
            return 'this_year'
        elif any(word in query_lower for word in ['last year', 'previous year']):
            return 'last_year'
        
        return None
    
    def get_session_context(self, session_id: str) -> Dict:
        """Get current session context"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
        
        # Clean up expired sessions
        self._cleanup_expired_sessions()
        
        return session.get('context', {})
    
    def resolve_contextual_query(self, session_id: str, query: str) -> str:
        """Resolve queries that depend on context"""
        context = self.get_session_context(session_id)
        query_lower = query.lower()
        
        # Handle follow-up questions
        if any(phrase in query_lower for phrase in ['how about', 'what about', 'and for']):
            last_topic = context.get('last_topic')
            
            if last_topic == 'revenue':
                if 'last week' in query_lower:
                    return 'show me revenue for last week'
                elif 'last month' in query_lower:
                    return 'show me revenue for last month'
            
            elif last_topic == 'products':
                if 'this month' in query_lower:
                    return 'show me top selling products this month'
                elif 'last month' in query_lower:
                    return 'show me top selling products last month'
        
        # Handle relative time references
        if any(phrase in query_lower for phrase in ['last time', 'previous', 'before']):
            last_intent = context.get('last_intent')
            if last_intent:
                time_period = context.get('time_period', 'this_month')
                return f"show me {last_intent.replace('_', ' ')} for {time_period}"
        
        return query
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if (current_time - session['last_activity']).total_seconds() > (self.session_timeout * 60):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
    
    def update_feedback(self, log_id: int, feedback: int):
        """Update feedback for a logged interaction"""
        self.db.update_feedback(log_id, feedback)
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return []
        
        history = session.get('conversation_history', [])
        return history[-limit:]  # Return last N interactions
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
        
        history = session.get('conversation_history', [])
        context = session.get('context', {})
        
        return {
            'total_interactions': len(history),
            'session_duration': (datetime.now() - session['start_time']).total_seconds() / 60,
            'last_activity': session['last_activity'].isoformat(),
            'context_size': len(context),
            'main_topics': list(set([item.get('intent', '') for item in history]))
        }
