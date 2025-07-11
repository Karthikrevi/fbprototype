
# Import the new smart bot
import sys
import os

# Add chatbot directory to path
chatbot_path = os.path.join(os.path.dirname(__file__), 'chatbot')
if chatbot_path not in sys.path:
    sys.path.append(chatbot_path)

try:
    from chatbot.main import smart_bot
    
    class InventoryBot:
        """Legacy wrapper for backward compatibility"""
        def __init__(self):
            self.smart_bot = smart_bot
        
        def process_query(self, query, vendor_email):
            """Process query using the smart bot"""
            try:
                result = self.smart_bot.process_query(query, vendor_email)
                return result.get('response', 'I encountered an error processing your request.')
            except Exception as e:
                return f"Sorry, I encountered an error: {str(e)}"
    
    # Create bot instance
    inventory_bot = InventoryBot()
    
except ImportError as e:
    print(f"Warning: Could not import smart bot, falling back to basic bot: {e}")
    
    # Fallback to basic bot if smart bot fails to import
    import sqlite3
    from datetime import datetime

    class InventoryBot:
        def __init__(self):
            self.db_path = 'erp.db'
        
        def process_query(self, query, vendor_email):
            return "I'm currently being upgraded with AI capabilities. Please try again in a moment."
    
    inventory_bot = InventoryBot()
