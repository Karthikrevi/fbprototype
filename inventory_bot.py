
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

# Try to import the smart bot
smart_bot_available = False
try:
    from chatbot.main import smart_bot
    smart_bot_available = True
    print("✅ Smart bot loaded successfully!")
except ImportError as e:
    print(f"⚠️ Smart bot import failed: {e}")
    print("🔄 Falling back to basic bot with enhanced functionality...")

class InventoryBot:
    """Enhanced inventory bot with personality and smart functionality"""
    
    def __init__(self):
        self.db_path = 'erp.db'
        self.has_smart_bot = smart_bot_available

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
📈 **Advanced Analytics:** Inventory turnover, dead stock analysis
🎯 **Performance Reports:** Monthly summaries, profit margins

Just ask me things like:
• "Show me my top selling products"
• "Which products are low in stock?"
• "What's my revenue this month?"
• "How's my inventory performing?"
• "What products need attention?"

What would you like to know? 🐾"""
        
        # Not a casual conversation - return None to let business logic handle it
        return None

    def process_query(self, query, vendor_email):
        """Process query using smart bot or enhanced fallback"""
        # First, check for casual conversation
        casual_response = self.handle_casual_conversation(query)
        if casual_response:
            return casual_response

        # Try to use smart bot if available
        if self.has_smart_bot:
            try:
                result = smart_bot.process_query(query, vendor_email)
                return result.get('response', 'I encountered an error processing your request.')
            except Exception as e:
                print(f"Smart bot error: {e}")
                # Fall back to enhanced basic bot
                return self.enhanced_basic_processing(query, vendor_email)
        else:
            # Use enhanced basic bot
            return self.enhanced_basic_processing(query, vendor_email)

    def enhanced_basic_processing(self, query, vendor_email):
        """Enhanced basic processing with more business intelligence"""
        query_lower = query.lower()
        vendor_id = self.get_vendor_id(vendor_email)

        if not vendor_id:
            return "Sorry, I couldn't find your vendor account. Please make sure you're logged in correctly."

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Top selling products
            if any(word in query_lower for word in ['top', 'best', 'selling', 'popular', 'performers']):
                c.execute("""
                    SELECT p.name, SUM(sl.quantity) as total_sold, SUM(sl.total_amount) as revenue
                    FROM sales_log sl
                    JOIN products p ON sl.product_id = p.id
                    WHERE sl.vendor_id = ? AND sl.sale_date >= date('now', '-30 days')
                    GROUP BY p.id, p.name
                    ORDER BY total_sold DESC
                    LIMIT 5
                """, (vendor_id,))

                results = c.fetchall()
                if results:
                    response = "🏆 **Top Selling Products (Last 30 Days):**\n"
                    for i, (name, sold, revenue) in enumerate(results, 1):
                        response += f"{i}. **{name}** - {sold} units sold (₹{revenue:.2f})\n"
                    conn.close()
                    return response
                else:
                    conn.close()
                    return "No sales data found for the last 30 days. Start making some sales! 🚀"

            # Low stock alerts
            elif any(word in query_lower for word in ['low', 'stock', 'inventory', 'restock', 'alert']):
                c.execute("""
                    SELECT name, quantity, sale_price
                    FROM products 
                    WHERE vendor_id = ? AND quantity < 10
                    ORDER BY quantity ASC
                    LIMIT 10
                """, (vendor_id,))

                results = c.fetchall()
                if results:
                    response = "⚠️ **Low Stock Alert:**\n"
                    for name, qty, price in results:
                        urgency = "🔴 URGENT" if qty < 3 else "🟡 LOW"
                        response += f"• {urgency} **{name}** - Only {qty} left (₹{price} each)\n"
                    response += "\n💡 Consider restocking these items soon!"
                    conn.close()
                    return response
                else:
                    conn.close()
                    return "✅ Great news! All products have adequate stock levels! 🎉"

            # Revenue and sales reports
            elif any(word in query_lower for word in ['revenue', 'sales', 'money', 'profit', 'earnings', 'income']):
                c.execute("""
                    SELECT COUNT(*) as orders, 
                           SUM(total_amount) as revenue, 
                           SUM(quantity) as units,
                           AVG(total_amount) as avg_order
                    FROM sales_log 
                    WHERE vendor_id = ? AND sale_date >= date('now', '-30 days')
                """, (vendor_id,))

                result = c.fetchone()
                orders, revenue, units, avg_order = result if result else (0, 0, 0, 0)

                # Get expenses for profit calculation
                c.execute("""
                    SELECT SUM(amount) as expenses
                    FROM expenses 
                    WHERE vendor_id = ? AND date >= date('now', '-30 days')
                """, (vendor_id,))
                
                expenses_result = c.fetchone()
                expenses = expenses_result[0] if expenses_result and expenses_result[0] else 0
                profit = (revenue or 0) - expenses

                conn.close()
                return f"""📊 **Business Performance (Last 30 Days):**
• **Total Orders:** {orders or 0}
• **Total Revenue:** ₹{revenue or 0:.2f}
• **Units Sold:** {units or 0}
• **Average Order Value:** ₹{avg_order or 0:.2f}
• **Total Expenses:** ₹{expenses:.2f}
• **Net Profit:** ₹{profit:.2f}

{'🎉 Great performance!' if profit > 0 else '📈 Focus on increasing sales or reducing costs.'}"""

            # Inventory performance analysis
            elif any(word in query_lower for word in ['performance', 'analysis', 'analytics', 'insights', 'how am i doing']):
                # Get product performance data
                c.execute("""
                    SELECT p.name, p.quantity, p.buy_price, p.sale_price,
                           COALESCE(SUM(sl.quantity), 0) as sold_30_days,
                           COALESCE(SUM(sl.total_amount), 0) as revenue_30_days
                    FROM products p
                    LEFT JOIN sales_log sl ON p.id = sl.product_id 
                        AND sl.sale_date >= date('now', '-30 days')
                    WHERE p.vendor_id = ?
                    GROUP BY p.id, p.name, p.quantity, p.buy_price, p.sale_price
                    ORDER BY sold_30_days DESC
                """, (vendor_id,))

                results = c.fetchall()
                if results:
                    fast_moving = []
                    slow_moving = []
                    dead_stock = []
                    
                    for row in results:
                        name, stock, buy_price, sale_price, sold, revenue = row
                        if sold > 5:  # Fast moving
                            fast_moving.append((name, sold, revenue))
                        elif sold > 0:  # Slow moving
                            slow_moving.append((name, sold, stock))
                        else:  # Dead stock
                            dead_stock.append((name, stock, buy_price * stock))
                    
                    response = "📈 **Inventory Performance Analysis:**\n\n"
                    
                    if fast_moving:
                        response += "🚀 **Fast-Moving Products:**\n"
                        for name, sold, revenue in fast_moving[:3]:
                            response += f"• **{name}** - {sold} units (₹{revenue:.2f})\n"
                        response += "\n"
                    
                    if slow_moving:
                        response += "🐌 **Slow-Moving Products:**\n"
                        for name, sold, stock in slow_moving[:3]:
                            response += f"• **{name}** - {sold} sold, {stock} remaining\n"
                        response += "\n"
                    
                    if dead_stock:
                        response += "⚠️ **Dead Stock (No Sales):**\n"
                        for name, stock, value in dead_stock[:3]:
                            response += f"• **{name}** - {stock} units (₹{value:.2f} tied up)\n"
                        response += "\n💡 Consider promotions or discounts for dead stock!"
                    
                    conn.close()
                    return response
                else:
                    conn.close()
                    return "No inventory data available for analysis."

            # Expense tracking
            elif any(word in query_lower for word in ['expense', 'cost', 'spending', 'outgoing']):
                c.execute("""
                    SELECT category, SUM(amount) as total, COUNT(*) as count
                    FROM expenses 
                    WHERE vendor_id = ? AND date >= date('now', '-30 days')
                    GROUP BY category
                    ORDER BY total DESC
                """, (vendor_id,))

                results = c.fetchall()
                if results:
                    total_expenses = sum(row[1] for row in results)
                    response = f"💸 **Expense Breakdown (Last 30 Days):**\n"
                    response += f"**Total Expenses:** ₹{total_expenses:.2f}\n\n"
                    
                    for category, amount, count in results:
                        percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                        response += f"• **{category}:** ₹{amount:.2f} ({percentage:.1f}%) - {count} transactions\n"
                    
                    conn.close()
                    return response
                else:
                    conn.close()
                    return "No expense data found for the last 30 days."

            # General business questions
            elif any(word in query_lower for word in ['business', 'doing well', 'month', 'summary', 'overview']):
                # Get comprehensive business overview
                c.execute("""
                    SELECT COUNT(*) as orders, SUM(total_amount) as revenue
                    FROM sales_log 
                    WHERE vendor_id = ? AND sale_date >= date('now', '-30 days')
                """, (vendor_id,))
                
                sales_data = c.fetchone()
                orders, revenue = sales_data if sales_data else (0, 0)
                
                c.execute("""
                    SELECT COUNT(*) as total_products, 
                           SUM(CASE WHEN quantity < 10 THEN 1 ELSE 0 END) as low_stock_count
                    FROM products WHERE vendor_id = ?
                """, (vendor_id,))
                
                inventory_data = c.fetchone()
                total_products, low_stock_count = inventory_data if inventory_data else (0, 0)
                
                conn.close()
                
                business_health = "🎉 Excellent" if revenue > 50000 else "📈 Good" if revenue > 20000 else "🔧 Needs Attention"
                
                return f"""🏢 **Business Overview (Last 30 Days):**

📊 **Sales Performance:**
• Orders: {orders or 0}
• Revenue: ₹{revenue or 0:.2f}
• Business Health: {business_health}

📦 **Inventory Status:**
• Total Products: {total_products or 0}
• Low Stock Items: {low_stock_count or 0}
• Inventory Health: {'✅ Good' if low_stock_count < 5 else '⚠️ Needs Attention'}

💡 **Quick Insights:**
{'• Great sales performance this month!' if revenue > 30000 else '• Focus on marketing and promotions'}
{'• Inventory levels are healthy' if low_stock_count < 3 else '• Consider restocking low inventory items'}"""

            # Default helpful response
            else:
                conn.close()
                return f"""Woof! I'm {BOT_NAME}, your business assistant! 🐕

I can help you with:
🏆 **"Show me my top products"** - Best sellers
📊 **"What's my revenue?"** - Sales & profit analysis  
⚠️ **"Which products are low in stock?"** - Inventory alerts
📈 **"How's my business doing?"** - Performance overview
💸 **"What are my expenses?"** - Cost breakdown
🔍 **"Analyze my inventory"** - Performance insights

What would you like to know about your business? 🐾"""

        except Exception as e:
            print(f"Database error: {e}")
            return f"Sorry, I encountered a database error: {str(e)}. Please try again or contact support."

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

# Create bot instance
inventory_bot = InventoryBot()
