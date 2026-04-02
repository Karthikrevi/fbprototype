import os
import sys
import sqlite3
import random
from typing import Dict, Tuple, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Bot personality constants
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
    from .database import ChatbotDatabase
    from .classifier import IntentClassifier
    from .vector_matcher import VectorMatcher
    from .training import TrainingManager
    from .logger import ConversationLogger
    from .analytics_engine import AdvancedAnalyticsEngine
    from .nlp_processor import BusinessQueryProcessor
except ImportError:
    # Fallback for direct execution
    from database import ChatbotDatabase
    from classifier import IntentClassifier
    from vector_matcher import VectorMatcher
    from training import TrainingManager
    from logger import ConversationLogger
    from analytics_engine import AdvancedAnalyticsEngine
    from nlp_processor import BusinessQueryProcessor

class SmartInventoryBot:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path

        # Initialize components
        self.db = ChatbotDatabase(db_path)
        self.classifier = IntentClassifier()
        self.vector_matcher = VectorMatcher()
        self.logger = ConversationLogger(db_path)
        self.training_manager = TrainingManager(db_path)
        self.analytics_engine = AdvancedAnalyticsEngine(db_path)
        self.nlp_processor = BusinessQueryProcessor()

        # Intent to function mapping
        self.intent_handlers = {
            'top_selling_products': self.get_top_products,
            'low_stock_alerts': self.get_low_stock_products,
            'revenue_report': self.get_sales_summary,
            'profit_summary': self.get_profit_analysis,
            'inventory_performance': self.get_inventory_analytics,
            'expense_analysis': self.get_expense_summary,
            # Advanced business intents
            'monthly_performance': self.handle_monthly_performance,
            'inventory_turnover': self.handle_inventory_turnover,
            'safety_stock_check': self.handle_safety_stock,
            'ideal_order_quantity': self.handle_eoq,
            'product_margin': self.handle_product_margin,
            'dead_stock_analysis': self.handle_dead_stock,
            'best_selling_product': self.handle_best_sellers,
            'restock_needed': self.get_low_stock_products,
            'sales_problems': self.handle_sales_analysis,
            'general_business': self.handle_general_business
        }

        # Initialize if needed
        self._initialize_if_needed()

    def _is_word_match(self, text: str, keyword: str) -> bool:
        """Check if keyword appears as a whole word in text"""
        import re
        return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text))

    def handle_casual_conversation(self, user_input: str) -> str:
        """Handle casual conversation and greetings"""
        user_input_lower = user_input.lower().strip()
        
        business_keywords = ['stock', 'restock', 'inventory', 'product', 'sell', 'revenue',
                             'profit', 'order', 'reorder', 'expense', 'analytics', 'report',
                             'performance', 'turnover', 'dead', 'margin', 'sales', 'running low',
                             'running out', 'need to']
        if any(kw in user_input_lower for kw in business_keywords):
            return None
        
        if any(self._is_word_match(user_input_lower, greeting) for greeting in BOT_PERSONALITY['greeting_keywords']):
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
📈 **Performance Reports:** Monthly summaries, inventory turnover

Just ask me things like:
• "Show me my top selling products"
• "Which products are low in stock?"
• "What's my revenue this month?"
• "Analyze my inventory performance"

What would you like to know? 🐾"""
        
        # Not a casual conversation - return None to let business logic handle it
        return None

    def _initialize_if_needed(self):
        """Initialize the bot if it's the first run"""
        # Check if we have a trained model
        if not self.classifier.pipeline:
            print("No trained model found. Running initial training...")
            result = self.training_manager.initial_training()
            if not result.get('success'):
                print("Warning: Initial training failed. Bot will use fallback responses.")

    def process_query(self, query: str, vendor_email: str, session_id: str = None) -> Dict:
        """Process a user query with ML intelligence"""
        # Start session if needed
        if not session_id:
            session_id = self.logger.start_session(vendor_email)

        # First, check for casual conversation
        casual_response = self.handle_casual_conversation(query)
        if casual_response:
            # Log the casual interaction
            log_id = self.logger.log_interaction(
                session_id=session_id,
                query=query,
                intent='casual_conversation',
                confidence=1.0,
                response=casual_response,
                additional_context={'vendor_email': vendor_email}
            )
            
            return {
                'response': casual_response,
                'intent': 'casual_conversation',
                'confidence': 1.0,
                'session_id': session_id,
                'log_id': log_id,
                'data': {}
            }

        # Resolve contextual queries
        resolved_query = self.logger.resolve_contextual_query(session_id, query)
        if resolved_query != query:
            query = resolved_query

        # Process with NLP for business context
        nlp_result = self.nlp_processor.process_business_query(query)
        business_intent = nlp_result.get('intent')
        business_confidence = nlp_result.get('confidence', 0.0)
        
        # Classify intent with traditional ML
        ml_intent, ml_confidence = self.classifier.predict(query)
        
        # Choose best intent based on confidence
        if business_confidence > ml_confidence and business_intent != 'general_business':
            intent = business_intent
            confidence = business_confidence
        else:
            intent = ml_intent
            confidence = ml_confidence

        response = ""
        response_data = {}

        # Handle high-confidence predictions
        if confidence >= 0.6 and intent in self.intent_handlers:
            try:
                response_data = self.intent_handlers[intent](vendor_email)
                response = self._format_response(intent, response_data)
            except Exception as e:
                response = f"I encountered an error processing your request: {str(e)}"
                intent = "error"
                confidence = 0.0

        # Fallback to similarity matching for unknown or low-confidence intents
        elif intent == 'unknown' or confidence < 0.6:
            similar_match = self.vector_matcher.get_best_match(query)

            if similar_match:
                response = similar_match['response']
                intent = similar_match.get('intent', 'similarity_match')
                confidence = similar_match['similarity']
            else:
                response = self._get_fallback_response(query)
                intent = 'fallback'
                confidence = 0.1

        # Log the interaction
        log_id = self.logger.log_interaction(
            session_id=session_id,
            query=query,
            intent=intent,
            confidence=confidence,
            response=response,
            additional_context={'vendor_email': vendor_email}
        )

        return {
            'response': response,
            'intent': intent,
            'confidence': confidence,
            'session_id': session_id,
            'log_id': log_id,
            'data': response_data
        }

    def _format_response(self, intent: str, data: Dict) -> str:
        """Format response based on intent and data"""
        if intent == 'top_selling_products':
            if data.get('products'):
                response = "🏆 **Top Selling Products (Last 30 Days)**\n"
                for i, product in enumerate(data['products'], 1):
                    response += f"{i}. {product['name']} - {product['units_sold']} units (₹{product['revenue']})\n"
                return response
            else:
                return "No sales data found for the last 30 days."

        elif intent == 'low_stock_alerts':
            if data.get('products'):
                response = "⚠️ **Low Stock Alert**\n"
                for product in data['products']:
                    response += f"• {product['name']} - Only {product['stock']} left\n"
                return response
            else:
                return "✅ All products have adequate stock levels!"

        elif intent == 'revenue_report':
            summary = data.get('summary', {})
            return f"""📊 **Sales Summary (Last 30 Days)**
• Total Orders: {summary.get('total_orders', 0)}
• Total Revenue: ₹{summary.get('total_revenue', 0)}
• Units Sold: {summary.get('total_units', 0)}
• Average Order Value: ₹{summary.get('avg_order_value', 0)}"""

        elif intent == 'profit_summary':
            profit_data = data.get('profit', {})
            return f"""💰 **Profit Analysis**
• Total Revenue: ₹{profit_data.get('revenue', 0)}
• Total Costs: ₹{profit_data.get('costs', 0)}
• Gross Profit: ₹{profit_data.get('gross_profit', 0)}
• Profit Margin: {profit_data.get('margin_percent', 0)}%"""

        elif intent == 'inventory_performance':
            analytics = data.get('analytics', [])
            if analytics:
                fast_moving = [p for p in analytics if p.get('performance') == 'Fast-moving']
                stagnant = [p for p in analytics if p.get('performance') == 'Stagnant']

                response = "📈 **Inventory Performance Analysis**\n"
                response += f"Fast-moving products: {len(fast_moving)}\n"
                response += f"Stagnant products: {len(stagnant)}\n\n"

                if fast_moving:
                    response += "🚀 **Top Performers:**\n"
                    for product in fast_moving[:3]:
                        response += f"• {product['name']} (Turnover: {product.get('turnover_rate', 0)}x)\n"

                if stagnant:
                    response += "\n🐌 **Needs Attention:**\n"
                    for product in stagnant[:3]:
                        response += f"• {product['name']} ({product.get('stock', 0)} units stagnant)\n"

                return response
            else:
                return "No inventory data available for analysis."

        elif intent == 'expense_analysis':
            expenses = data.get('expenses', {})
            return f"""💸 **Expense Analysis (Last 30 Days)**
• Total Expenses: ₹{expenses.get('total', 0)}
• Average Daily Expense: ₹{expenses.get('daily_average', 0)}
• Top Category: {expenses.get('top_category', 'N/A')}"""

        elif intent == 'monthly_performance':
            return data.get('summary_text', 'Monthly performance data not available.')

        elif intent == 'inventory_turnover':
            if 'turnover_ratio' in data:
                return f"""📊 **Inventory Turnover Analysis**
• Turnover Ratio: {data['turnover_ratio']}x per year
• Cost of Goods Sold: ₹{data['cogs']}
• Average Inventory Value: ₹{data['avg_inventory_value']}
• Assessment: {data['interpretation']}

💡 Higher turnover means faster inventory movement and better cash flow."""
            else:
                return "Unable to calculate inventory turnover ratio."

        elif intent == 'dead_stock_analysis':
            dead_stock_data = data.get('dead_stock_items', [])
            if dead_stock_data:
                response = f"🚨 **Dead Stock Alert** ({data.get('total_items', 0)} items)\n"
                response += f"💰 Total Capital Tied: ₹{data.get('total_tied_capital', 0)}\n\n"
                
                for item in dead_stock_data[:5]:  # Show top 5
                    response += f"• **{item['product_name']}**\n"
                    response += f"  Stock: {item['quantity']} units (₹{item['tied_capital']})\n"
                    response += f"  Action: {item['recommended_action']}\n\n"
                
                return response
            else:
                return "✅ No dead stock found! All products are moving well."

        elif intent == 'best_selling_product':
            top_performers = data.get('top_by_volume', [])
            if top_performers:
                response = "🏆 **Best Selling Products (by Volume)**\n"
                for i, product in enumerate(top_performers, 1):
                    response += f"{i}. {product['name']} - {product['volume']} units (₹{product['revenue']})\n"
                return response
            else:
                return "No sales data available for analysis."

        elif intent == 'product_margin':
            cost_analysis = data.get('cost_analysis', [])
            if cost_analysis:
                response = "💰 **Product Margin Analysis**\n"
                for product in cost_analysis[:5]:  # Show top 5
                    response += f"• **{product['product_name']}**\n"
                    response += f"  Margin: {product['margin_percent']}% ({product['margin_status']})\n"
                    response += f"  Recommendation: {product['recommendation']}\n\n"
                return response
            else:
                return "No product margin data available."

        elif intent == 'sales_problems':
            sales_data = data.get('sales_summary', {}).get('summary', {})
            dead_stock = data.get('dead_stock', {})
            
            response = "🔍 **Sales Analysis**\n\n"
            response += f"📊 **Current Performance:**\n"
            response += f"• Orders: {sales_data.get('total_orders', 0)}\n"
            response += f"• Revenue: ₹{sales_data.get('total_revenue', 0)}\n\n"
            
            if dead_stock.get('total_items', 0) > 0:
                response += f"⚠️ **Issues Found:**\n"
                response += f"• {dead_stock['total_items']} products with slow movement\n"
                response += f"• ₹{dead_stock.get('total_tied_capital', 0)} in tied capital\n\n"
                response += "💡 **Recommendations:**\n"
                response += "• Focus marketing on slow-moving items\n"
                response += "• Consider clearance sales or bundles\n"
                response += "• Analyze pricing strategy"
            else:
                response += "✅ **Good News:** No major issues detected!"
            
            return response

        elif intent == 'restock_needed':
            if data.get('products'):
                response = "⚠️ **Products Needing Restock**\n"
                for product in data['products']:
                    response += f"• {product['name']} - Only {product['stock']} left\n"
                return response
            else:
                return "✅ All products have adequate stock levels! No restocking needed."

        elif intent in ['safety_stock_check', 'ideal_order_quantity', 'general_business']:
            return data.get('message', 'Analysis completed.')

        return "I processed your request but couldn't format the response properly."

    def _get_fallback_response(self, query: str) -> str:
        """Generate a fallback response for unknown queries"""
        query_lower = query.lower()

        # Check for specific keywords and provide helpful suggestions
        if any(word in query_lower for word in ['help', 'what can you do']):
            return f"""Woof! I'm {BOT_NAME}, and I can help you with:
🐕 **Business Analytics:**
• Sales summaries and revenue analysis
• Top selling products
• Low stock alerts and reorder recommendations
• Inventory performance analysis
• Profit margin insights
• Expense tracking

🐾 **Try asking:**
• "Show me my top selling products"
• "Which products are low in stock?"
• "What's my revenue this month?"
• "Analyze my inventory performance"
• "What are my expenses?"

What would you like to fetch for you? 🦴"""

        else:
            return BOT_PERSONALITY['fallback']

    # Data retrieval methods (same as original but enhanced)
    def get_vendor_id(self, vendor_email: str) -> Optional[int]:
        """Get vendor ID from email"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM vendors WHERE email = ?", (vendor_email,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def get_top_products(self, vendor_email: str, limit: int = 5) -> Dict:
        """Get top selling products"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'products': []}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT p.name, SUM(sl.quantity) as total_sold, SUM(sl.total_amount) as revenue
            FROM sales_log sl
            JOIN products p ON sl.product_id = p.id
            WHERE sl.vendor_id = ? AND sl.sale_date >= date('now', '-30 days')
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT ?
        """, (vendor_id, limit))

        results = c.fetchall()
        conn.close()

        products = [{'name': row[0], 'units_sold': row[1], 'revenue': round(row[2], 2)} for row in results]
        return {'products': products}

    def get_low_stock_products(self, vendor_email: str) -> Dict:
        """Get products with low stock"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'products': []}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT name, quantity, buy_price, sale_price
            FROM products 
            WHERE vendor_id = ? AND quantity < 10
            ORDER BY quantity ASC
        """, (vendor_id,))

        results = c.fetchall()
        conn.close()

        products = [{'name': row[0], 'stock': row[1], 'buy_price': row[2], 'sale_price': row[3]} for row in results]
        return {'products': products}

    def get_sales_summary(self, vendor_email: str, days: int = 30) -> Dict:
        """Get sales summary for the vendor"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'summary': {}}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT COUNT(*) as total_orders,
                   SUM(total_amount) as total_revenue,
                   SUM(quantity) as total_units,
                   AVG(total_amount) as avg_order_value
            FROM sales_log 
            WHERE vendor_id = ? AND sale_date >= date('now', '-{} days')
        """.format(days), (vendor_id,))

        result = c.fetchone()
        conn.close()

        summary = {
            'total_orders': result[0] or 0,
            'total_revenue': round(result[1] or 0, 2),
            'total_units': result[2] or 0,
            'avg_order_value': round(result[3] or 0, 2)
        }

        return {'summary': summary}

    def get_profit_analysis(self, vendor_email: str) -> Dict:
        """Get profit analysis"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'profit': {}}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get revenue
        c.execute("SELECT SUM(total_amount) FROM sales_log WHERE vendor_id = ?", (vendor_id,))
        revenue = c.fetchone()[0] or 0

        # Get expenses
        c.execute("SELECT SUM(amount) FROM expenses WHERE vendor_id = ?", (vendor_id,))
        expenses = c.fetchone()[0] or 0

        conn.close()

        gross_profit = revenue - expenses
        margin_percent = (gross_profit / revenue * 100) if revenue > 0 else 0

        profit = {
            'revenue': round(revenue, 2),
            'costs': round(expenses, 2),
            'gross_profit': round(gross_profit, 2),
            'margin_percent': round(margin_percent, 2)
        }

        return {'profit': profit}

    def get_inventory_analytics(self, vendor_email: str) -> Dict:
        """Get comprehensive inventory analytics"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'analytics': []}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get products with sales data
        c.execute("""
            SELECT p.name, p.quantity, p.buy_price, p.sale_price,
                   COALESCE(SUM(sl.quantity), 0) as total_sold_30_days,
                   COALESCE(SUM(sl.total_amount), 0) as revenue_30_days
            FROM products p
            LEFT JOIN sales_log sl ON p.id = sl.product_id 
                AND sl.sale_date >= date('now', '-30 days')
            WHERE p.vendor_id = ?
            GROUP BY p.id, p.name, p.quantity, p.buy_price, p.sale_price
        """, (vendor_id,))

        results = c.fetchall()
        conn.close()

        analytics = []
        for row in results:
            name, stock, buy_price, sale_price, units_sold, revenue = row

            # Calculate metrics
            turnover_rate = units_sold / max(stock, 1) if stock > 0 else 0

            # Classify performance
            if turnover_rate >= 2.0:
                performance = "Fast-moving"
            elif turnover_rate >= 0.5:
                performance = "Moderate"
            elif turnover_rate > 0:
                performance = "Slow-moving"
            else:
                performance = "Stagnant"

            analytics.append({
                'name': name,
                'stock': stock,
                'units_sold_30_days': units_sold,
                'revenue_30_days': round(revenue, 2),
                'turnover_rate': round(turnover_rate, 2),
                'performance': performance
            })

        return {'analytics': analytics}

    def get_expense_summary(self, vendor_email: str, days: int = 30) -> Dict:
        """Get expense summary"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'expenses': {}}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT SUM(amount), AVG(amount), category
            FROM expenses 
            WHERE vendor_id = ? AND date >= date('now', '-{} days')
            GROUP BY category
            ORDER BY SUM(amount) DESC
            LIMIT 1
        """.format(days), (vendor_id,))

        top_category = c.fetchone()

        c.execute("""
            SELECT SUM(amount), COUNT(*)
            FROM expenses 
            WHERE vendor_id = ? AND date >= date('now', '-{} days')
        """.format(days), (vendor_id,))

        total_data = c.fetchone()
        conn.close()

        total_expenses = total_data[0] or 0
        daily_average = total_expenses / days if days > 0 else 0

        expenses = {
            'total': round(total_expenses, 2),
            'daily_average': round(daily_average, 2),
            'top_category': top_category[2] if top_category else 'N/A'
        }

        return {'expenses': expenses}

    # Advanced Analytics Handlers
    def handle_monthly_performance(self, vendor_email: str) -> Dict:
        """Handle monthly performance queries"""
        return self.analytics_engine.generate_monthly_performance_summary(vendor_email)

    def handle_inventory_turnover(self, vendor_email: str) -> Dict:
        """Handle inventory turnover queries"""
        return self.analytics_engine.calculate_inventory_turnover_ratio(vendor_email)

    def handle_safety_stock(self, vendor_email: str) -> Dict:
        """Handle safety stock queries - for now return general info"""
        return {
            'message': 'To check safety stock for a specific product, ask: "Do I have enough safety stock for [product name]?"',
            'general_recommendation': 'Safety stock helps prevent stockouts during demand spikes or supply delays.'
        }

    def handle_eoq(self, vendor_email: str) -> Dict:
        """Handle EOQ queries - for now return general info"""
        return {
            'message': 'To calculate optimal order quantity for a specific product, ask: "What\'s the ideal order quantity for [product name]?"',
            'general_info': 'Economic Order Quantity (EOQ) helps minimize total inventory costs by balancing ordering and holding costs.'
        }

    def handle_product_margin(self, vendor_email: str) -> Dict:
        """Handle product margin analysis"""
        return self.analytics_engine.analyze_cost_to_sale_ratio(vendor_email)

    def handle_dead_stock(self, vendor_email: str) -> Dict:
        """Handle dead stock analysis"""
        return self.analytics_engine.detect_dead_stock(vendor_email)

    def handle_best_sellers(self, vendor_email: str) -> Dict:
        """Handle best selling products queries"""
        return self.analytics_engine.get_top_performers_advanced(vendor_email)

    def handle_sales_analysis(self, vendor_email: str) -> Dict:
        """Handle sales problem analysis"""
        # Get comprehensive sales data
        sales_summary = self.get_sales_summary(vendor_email)
        dead_stock = self.analytics_engine.detect_dead_stock(vendor_email)
        top_performers = self.analytics_engine.get_top_performers_advanced(vendor_email)
        
        return {
            'sales_summary': sales_summary,
            'dead_stock': dead_stock,
            'top_performers': top_performers,
            'analysis_type': 'sales_problems'
        }

    def handle_general_business(self, vendor_email: str) -> Dict:
        """Handle general business queries"""
        return {
            'message': 'I can help you with various business insights. Try asking about specific areas like sales performance, inventory management, or profit analysis.'
        }

    def submit_feedback(self, log_id: int, feedback: int) -> bool:
        """Submit feedback for an interaction"""
        try:
            self.logger.update_feedback(log_id, feedback)
            return True
        except Exception as e:
            print(f"Error submitting feedback: {e}")
            return False

    def get_analytics_dashboard(self) -> Dict:
        """Get analytics data for dashboard"""
        return self.db.get_analytics_data()

    def retrain_model(self) -> Dict:
        """Manually trigger model retraining"""
        return self.training_manager.retrain_from_feedback(days=30)

# Create global bot instance
smart_bot = SmartInventoryBot()