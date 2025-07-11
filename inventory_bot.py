
import sqlite3
import json
from datetime import datetime, timedelta
import re

class InventoryBot:
    def __init__(self):
        self.db_path = 'erp.db'
        self.supported_queries = [
            'sales', 'inventory', 'stock', 'product', 'revenue', 'profit', 'turnover',
            'fast moving', 'slow moving', 'low stock', 'reorder', 'best selling',
            'worst performing', 'analytics', 'performance', 'margin', 'top', 'best',
            'popular', 'moving', 'sold', 'selling', 'performers', 'items', 'successful'
        ]
    
    def is_query_supported(self, query):
        """Check if the query is related to inventory/sales analytics"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.supported_queries)
    
    def get_vendor_id(self, vendor_email):
        """Get vendor ID from email"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM vendors WHERE email = ?", (vendor_email,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_sales_summary(self, vendor_id, days=30):
        """Get sales summary for the vendor"""
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
        
        return {
            'total_orders': result[0] or 0,
            'total_revenue': round(result[1] or 0, 2),
            'total_units': result[2] or 0,
            'avg_order_value': round(result[3] or 0, 2)
        }
    
    def get_top_products(self, vendor_id, limit=5):
        """Get top selling products"""
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
        
        return [{'name': row[0], 'units_sold': row[1], 'revenue': round(row[2], 2)} for row in results]
    
    def get_low_stock_products(self, vendor_id):
        """Get products with low stock"""
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
        
        return [{'name': row[0], 'stock': row[1], 'buy_price': row[2], 'sale_price': row[3]} for row in results]
    
    def get_inventory_analytics(self, vendor_id):
        """Get comprehensive inventory analytics"""
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
            gross_margin = ((sale_price - buy_price) / sale_price * 100) if sale_price > 0 else 0
            
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
                'gross_margin_percent': round(gross_margin, 2),
                'performance': performance
            })
        
        return analytics
    
    def process_query(self, query, vendor_email):
        """Process user query and return appropriate response"""
        if not self.is_query_supported(query):
            return "Sorry, I can't help with this. I can only assist with inventory and sales analytics questions."
        
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return "Sorry, I couldn't find your vendor account."
        
        query_lower = query.lower()
        
        try:
            # Sales summary queries
            if any(word in query_lower for word in ['sales summary', 'total sales', 'revenue']):
                summary = self.get_sales_summary(vendor_id)
                return f"""📊 **Sales Summary (Last 30 Days)**
• Total Orders: {summary['total_orders']}
• Total Revenue: ₹{summary['total_revenue']}
• Units Sold: {summary['total_units']}
• Average Order Value: ₹{summary['avg_order_value']}"""
            
            # Top products queries - expanded to include more variations
            elif any(phrase in query_lower for phrase in [
                'top products', 'best selling', 'popular', 'top selling', 'best products',
                'top moving', 'fast moving', 'most sold', 'highest selling', 'best performers',
                'top performers', 'most popular', 'bestsellers', 'top items', 'best items',
                'which products sell', 'what sells best', 'most successful products'
            ]):
                top_products = self.get_top_products(vendor_id)
                if top_products:
                    response = "🏆 **Top Selling Products (Last 30 Days)**\n"
                    for i, product in enumerate(top_products, 1):
                        response += f"{i}. {product['name']} - {product['units_sold']} units (₹{product['revenue']})\n"
                    return response
                else:
                    return "No sales data found for the last 30 days."
            
            # Low stock queries
            elif any(phrase in query_lower for phrase in [
                'low stock', 'reorder', 'stock alert', 'running low', 'out of stock',
                'need to reorder', 'stock levels', 'inventory alert', 'almost empty'
            ]):
                low_stock = self.get_low_stock_products(vendor_id)
                if low_stock:
                    response = "⚠️ **Low Stock Alert**\n"
                    for product in low_stock:
                        response += f"• {product['name']} - Only {product['stock']} left\n"
                    return response
                else:
                    return "✅ All products have adequate stock levels!"
            
            # Performance analysis
            elif any(phrase in query_lower for phrase in [
                'performance', 'analytics', 'turnover', 'inventory performance', 
                'product performance', 'how are products doing', 'product analysis',
                'which products are fast', 'which products are slow', 'stagnant products'
            ]):
                analytics = self.get_inventory_analytics(vendor_id)
                if analytics:
                    fast_moving = [p for p in analytics if p['performance'] == 'Fast-moving']
                    stagnant = [p for p in analytics if p['performance'] == 'Stagnant']
                    
                    response = "📈 **Inventory Performance Analysis**\n"
                    response += f"Fast-moving products: {len(fast_moving)}\n"
                    response += f"Stagnant products: {len(stagnant)}\n\n"
                    
                    if fast_moving:
                        response += "🚀 **Top Performers:**\n"
                        for product in fast_moving[:3]:
                            response += f"• {product['name']} (Turnover: {product['turnover_rate']}x)\n"
                    
                    if stagnant:
                        response += "\n🐌 **Needs Attention:**\n"
                        for product in stagnant[:3]:
                            response += f"• {product['name']} ({product['stock']} units stagnant)\n"
                    
                    return response
                else:
                    return "No products found for analysis."
            
            # Profit margin queries
            elif any(word in query_lower for word in ['profit', 'margin', 'profitability']):
                analytics = self.get_inventory_analytics(vendor_id)
                if analytics:
                    profitable = sorted([p for p in analytics if p['gross_margin_percent'] > 0], 
                                      key=lambda x: x['gross_margin_percent'], reverse=True)
                    
                    response = "💰 **Profitability Analysis**\n"
                    if profitable:
                        response += "**Most Profitable Products:**\n"
                        for product in profitable[:5]:
                            response += f"• {product['name']} - {product['gross_margin_percent']}% margin\n"
                    else:
                        response += "No profitable products found."
                    
                    return response
                else:
                    return "No products found for profitability analysis."
            
            else:
                return """I can help you with:
• Sales summary and revenue
• Top selling products
• Low stock alerts
• Inventory performance analysis
• Profit margin analysis

Try asking:
• "Show me my top moving products"
• "Which products are my best sellers?"
• "What's my sales summary?"
• "Which products are low in stock?"
• "Show me my inventory performance"
• "What are my most profitable products?"
"""
        
        except Exception as e:
            return "Sorry, I encountered an error while analyzing your data. Please try again."

# Create bot instance
inventory_bot = InventoryBot()
