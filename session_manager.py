
from flask import session, request
from datetime import datetime, timedelta
import json

class SessionManager:
    """Enhanced session management"""
    
    @staticmethod
    def store_user_info(user_type, user_data):
        """Store user information in session"""
        session[f"{user_type}_id"] = user_data.get('id')
        session[f"{user_type}_email"] = user_data.get('email')
        session[f"{user_type}_name"] = user_data.get('name')
        session[f"{user_type}_login_time"] = datetime.now().isoformat()
        
        # Store additional user-specific data
        if user_type == 'vendor':
            session["vendor"] = user_data.get('email')
            session["vendor_category"] = user_data.get('category')
            session["vendor_city"] = user_data.get('city')
        elif user_type == 'user':
            session["user"] = user_data.get('email')
        elif user_type == 'ngo':
            session["ngo"] = user_data.get('email')
            session["ngo_type"] = user_data.get('organization_type')
    
    @staticmethod
    def clear_user_session(user_type):
        """Clear user session data"""
        keys_to_remove = [
            f"{user_type}_id", f"{user_type}_email", f"{user_type}_name", 
            f"{user_type}_login_time", user_type
        ]
        
        # Add specific keys based on user type
        if user_type == 'vendor':
            keys_to_remove.extend(["vendor_category", "vendor_city"])
        elif user_type == 'ngo':
            keys_to_remove.extend(["ngo_type", "ngo_signature_key"])
        
        for key in keys_to_remove:
            session.pop(key, None)
    
    @staticmethod
    def get_current_user_info():
        """Get current user information from session"""
        user_types = ['vendor', 'user', 'ngo', 'vet', 'handler', 'isolation']
        
        for user_type in user_types:
            if f"{user_type}_id" in session:
                return {
                    'type': user_type,
                    'id': session.get(f"{user_type}_id"),
                    'email': session.get(f"{user_type}_email"),
                    'name': session.get(f"{user_type}_name"),
                    'login_time': session.get(f"{user_type}_login_time")
                }
        return None
    
    @staticmethod
    def is_session_expired(max_hours=24):
        """Check if session is expired"""
        user_info = SessionManager.get_current_user_info()
        if not user_info or not user_info.get('login_time'):
            return True
        
        login_time = datetime.fromisoformat(user_info['login_time'])
        return datetime.now() - login_time > timedelta(hours=max_hours)
    
    @staticmethod
    def refresh_session():
        """Refresh session timestamp"""
        user_info = SessionManager.get_current_user_info()
        if user_info:
            session[f"{user_info['type']}_login_time"] = datetime.now().isoformat()
    
    @staticmethod
    def log_session_activity(action):
        """Log session activity"""
        user_info = SessionManager.get_current_user_info()
        if user_info:
            from database_utils import log_user_activity
            log_user_activity(
                user_info['email'], 
                action, 
                f"IP: {request.remote_addr}, User-Agent: {request.user_agent.string[:100]}"
            )
