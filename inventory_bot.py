# Import the new smart bot
import sys
import os
import sqlite3
import random
from datetime import datetime

# Add chatbot directory to path
chatbot_path = os.path.join(os.path.dirname(__file__), 'chatbot')
if chatbot_path not in sys.path:
    sys.path.append(chatbot_path)

# Bot personality constants (same as in main chatbot)
BOT_NAME = "Furry"
BOT_PERSONALITY = {
    'intro': "Hi! I'm Furry, your friendly vendor assistant! 🐕 I help you manage inventory, track sales, and analyze your business data. What can I fetch for you today?",
    'fallback': "Woof! I'm still learning that trick. Could you ask me about your inventory, sales, or business analytics instead? 🐾",
    'greeting_keywords': ['hi', 'hello', 'hey', 'yo', 'namaste', 'hola', 'howdy', 'sup', 'good morning', 'good afternoon', 'good evening'],
    'casual_responses': [
        "Hey there! 🐕",
        "Woof! How can I help you today?",
        "Hi! I'm here to fetch your data! 🐾",
        "Hello! Ready to dig into your business insights?",
        "Hey! Your loyal inventory assistant is here! 🦴"
    ],
    'how_are_you_responses': [
        "I'm paws-itively great today! 🐕",
        "Feeling fetch-tastic! How about you?",
        "I'm doing paw-some! Ready to help with your business! 🐾",
        "Tail-wagging good! What can I analyze for you?",
        "I'm having a ruff-ly good day! 🦴"
    ],
    'thank_you_responses': [
        "You're welcome! 🐕",
        "Happy to help! That's what good dogs do! 🐾",
        "Woof! Anytime! 🦴",
        "My pleasure! Got any more questions for me?",
        "You're paw-some! Glad I could help! 🐕"
    ],
    'name_responses': [
        f"I'm {BOT_NAME}, your friendly vendor helper bot! 🐕",
        f"Woof! I'm {BOT_NAME}, here to help you manage your business! 🐾",
        f"My name is {BOT_NAME}! I'm your loyal inventory assistant! 🦴",
        f"I'm {BOT_NAME}, your paw-some business analytics companion! 🐕"
    ]
}

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
                print(f"Smart bot error: {e}")
                return f"Sorry, I encountered an error: {str(e)}"

    # Create bot instance
    inventory_bot = InventoryBot()

except ImportError as e:
    print(f"Warning: Could not import smart bot, falling back to basic bot: {e}")

    # Fallback to basic bot if smart bot fails to import
    class InventoryBot:
        def __init__(self):
            self.db_path = 'erp.db'

        def handle_casual_conversation(self, user_input):
            """Handle casual conversation and greetings"""
            user_input_lower = user_input.lower().strip()
            
            # Handle greetings
            if any(greeting in user_input_lower for greeting in BOT_PERSONALITY['greeting_keywords']):
                return random.choice(BOT_PERSONALITY['casual_responses'])
            
            # Handle name questions
            if any(phrase in user_input_lower for phrase in ['what\'s your name', 'who are you', 'your name', 'what are you']):
                return random.choice(BOT_PERSONALITY['name_responses'])
            
            # Handle "how are you" questions
            if any(phrase in user_input_lower for phrase in ['how are you', 'how\'s it going', 'how you doing', 'what\'s up']):
                return random.choice(BOT_PERSONALITY['how_are_you_responses'])
            
            # Handle thank you
            if any(phrase in user_input_lower for phrase in ['thank you', 'thanks', 'thank u', 'thx', 'appreciate it']):
                return random.choice(BOT_PERSONALITY['thank_you_responses'])
            
            # Handle introduction request
            if any(phrase in user_input_lower for phrase in ['introduce yourself', 'tell me about yourself', 'what do you do']):
                return BOT_PERSONALITY['intro']
            
            # Handle help requests
            if any(phrase in user_input_lower for phrase in ['help', 'what can you do', 'commands', 'options']):
                return f"""Woof! I'm {BOT_NAME}, and I can help you with:
🐕 **Inventory Management:** Check stock levels, low stock alerts
📊 **Sales Analytics:** Top selling products, revenue reports
💰 **Business Insights:** Profit analysis, expense tracking

Just ask me things like:
• "Show me my top selling products"
• "Which products are low in stock?"
• "What's my revenue this month?"

What would you like to know? 🐾"""
            
            # Not a casual conversation - return None to let business logic handle it
            return None

        def get_vendor_id(self, vendor_email):
            """Get vendor ID from email"""
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT id FROM vendors WHERE email = ?", (vendor_email,))
                result = c.fetchone()
                conn.close()
                return result[0] if result else None
            except Exception as e:
                print(f"Database error: {e}")
                return None

        def process_query(self, query, vendor_email):
            """Basic fallback query processing"""
            # First, check for casual conversation
            casual_response = self.handle_casual_conversation(query)
            if casual_response:
                return casual_response

            query_lower = query.lower()
            vendor_id = self.get_vendor_id(vendor_email)

            if not vendor_id:
                return "Sorry, I couldn't find your vendor account."

            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                if any(word in query_lower for word in ['top', 'best', 'selling', 'popular']):
                    c.execute("""
                        SELECT p.name, SUM(sl.quantity) as total_sold
                        FROM sales_log sl
                        JOIN products p ON sl.product_id = p.id
                        WHERE sl.vendor_id = ? AND sl.sale_date >= date('now', '-30 days')
                        GROUP BY p.id, p.name
                        ORDER BY total_sold DESC
                        LIMIT 5
                    """, (vendor_id,))

                    results = c.fetchall()
                    if results:
                        response = "🏆 Top Selling Products (Last 30 Days):\n"
                        for i, (name, sold) in enumerate(results, 1):
                            response += f"{i}. {name} - {sold} units\n"
                        conn.close()
                        return response
                    else:
                        conn.close()
                        return "No sales data found for the last 30 days."

                elif any(word in query_lower for word in ['low', 'stock', 'inventory']):
                    c.execute("""
                        SELECT name, quantity
                        FROM products 
                        WHERE vendor_id = ? AND quantity < 10
                        ORDER BY quantity ASC
                        LIMIT 10
                    """, (vendor_id,))

                    results = c.fetchall()
                    if results:
                        response = "⚠️ Low Stock Alert:\n"
                        for name, qty in results:
                            response += f"• {name} - Only {qty} left\n"
                        conn.close()
                        return response
                    else:
                        conn.close()
                        return "✅ All products have adequate stock levels!"

                elif any(word in query_lower for word in ['revenue', 'sales', 'money', 'profit']):
                    c.execute("""
                        SELECT COUNT(*) as orders, SUM(total_amount) as revenue, SUM(quantity) as units
                        FROM sales_log 
                        WHERE vendor_id = ? AND sale_date >= date('now', '-30 days')
                    """, (vendor_id,))

                    result = c.fetchone()
                    orders, revenue, units = result if result else (0, 0, 0)

                    conn.close()
                    return f"""📊 Sales Summary (Last 30 Days):
• Total Orders: {orders or 0}
• Total Revenue: ₹{revenue or 0:.2f}
• Units Sold: {units or 0}"""

                else:
                    conn.close()
                    return f"""Woof! I'm {BOT_NAME}, and I can help you with:
🐕 **Top selling products** ("show me top products")
🐾 **Low stock alerts** ("which products are low in stock")  
📊 **Sales and revenue reports** ("what's my revenue")

What would you like to fetch for you? 🦴"""

            except Exception as e:
                return f"Sorry, I encountered a database error: {str(e)}"

    inventory_bot = InventoryBot()