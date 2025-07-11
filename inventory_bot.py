# Import the new smart bot
import sys
import os
import sqlite3
from datetime import datetime

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
                    return """I can help you with:
• Top selling products ("show me top products")
• Low stock alerts ("which products are low in stock")
• Sales and revenue reports ("what's my revenue")

What would you like to know?"""

            except Exception as e:
                return f"Sorry, I encountered a database error: {str(e)}"

    inventory_bot = InventoryBot()