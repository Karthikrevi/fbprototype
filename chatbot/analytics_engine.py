
import sqlite3
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class AdvancedAnalyticsEngine:
    def __init__(self, db_path: str = 'erp.db'):
        self.db_path = db_path

    def get_vendor_id(self, vendor_email: str) -> Optional[int]:
        """Get vendor ID from email"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM vendors WHERE email = ?", (vendor_email,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def calculate_inventory_turnover_ratio(self, vendor_email: str, days: int = 365) -> Dict:
        """Calculate Inventory Turnover Ratio = COGS / Average Inventory"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Calculate COGS (Cost of Goods Sold)
        c.execute("""
            SELECT SUM(sl.quantity * p.buy_price) as cogs
            FROM sales_log sl
            JOIN products p ON sl.product_id = p.id
            WHERE sl.vendor_id = ? AND sl.sale_date >= date('now', '-{} days')
        """.format(days), (vendor_id,))
        
        cogs_result = c.fetchone()
        cogs = cogs_result[0] or 0

        # Calculate Average Inventory Value
        c.execute("""
            SELECT AVG(p.quantity * p.buy_price) as avg_inventory
            FROM products p
            WHERE p.vendor_id = ?
        """, (vendor_id,))
        
        avg_inventory_result = c.fetchone()
        avg_inventory = avg_inventory_result[0] or 1

        conn.close()

        turnover_ratio = cogs / avg_inventory if avg_inventory > 0 else 0
        
        return {
            'turnover_ratio': round(turnover_ratio, 2),
            'cogs': round(cogs, 2),
            'avg_inventory_value': round(avg_inventory, 2),
            'interpretation': self._interpret_turnover_ratio(turnover_ratio)
        }

    def calculate_stock_cover_duration(self, vendor_email: str, product_name: str = None) -> Dict:
        """Calculate Stock Cover Duration = Inventory / Daily Sales Avg"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if product_name:
            # Calculate for specific product
            c.execute("""
                SELECT p.quantity, 
                       COALESCE(AVG(daily_sales.daily_qty), 0) as avg_daily_sales
                FROM products p
                LEFT JOIN (
                    SELECT product_id, sale_date, SUM(quantity) as daily_qty
                    FROM sales_log 
                    WHERE vendor_id = ? AND sale_date >= date('now', '-30 days')
                    GROUP BY product_id, sale_date
                ) daily_sales ON p.id = daily_sales.product_id
                WHERE p.vendor_id = ? AND p.name LIKE ?
                GROUP BY p.id, p.quantity
            """, (vendor_id, vendor_id, f"%{product_name}%"))
            
            results = c.fetchall()
            cover_data = []
            
            for current_stock, avg_daily_sales in results:
                days_cover = current_stock / avg_daily_sales if avg_daily_sales > 0 else float('inf')
                cover_data.append({
                    'current_stock': current_stock,
                    'avg_daily_sales': round(avg_daily_sales, 2),
                    'days_cover': round(days_cover, 1) if days_cover != float('inf') else 'Infinite'
                })
        else:
            # Calculate for all products
            c.execute("""
                SELECT p.name, p.quantity, 
                       COALESCE(AVG(daily_sales.daily_qty), 0) as avg_daily_sales
                FROM products p
                LEFT JOIN (
                    SELECT product_id, sale_date, SUM(quantity) as daily_qty
                    FROM sales_log 
                    WHERE vendor_id = ? AND sale_date >= date('now', '-30 days')
                    GROUP BY product_id, sale_date
                ) daily_sales ON p.id = daily_sales.product_id
                WHERE p.vendor_id = ?
                GROUP BY p.id, p.name, p.quantity
                ORDER BY p.quantity ASC
            """, (vendor_id, vendor_id))
            
            results = c.fetchall()
            cover_data = []
            
            for name, current_stock, avg_daily_sales in results:
                days_cover = current_stock / avg_daily_sales if avg_daily_sales > 0 else float('inf')
                cover_data.append({
                    'product_name': name,
                    'current_stock': current_stock,
                    'avg_daily_sales': round(avg_daily_sales, 2),
                    'days_cover': round(days_cover, 1) if days_cover != float('inf') else 'Infinite'
                })

        conn.close()
        return {'stock_cover_data': cover_data}

    def calculate_economic_order_quantity(self, vendor_email: str, product_name: str) -> Dict:
        """Calculate EOQ = sqrt((2 * D * S) / H)"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get annual demand (D), ordering cost (S), holding cost (H)
        c.execute("""
            SELECT p.buy_price, 
                   COALESCE(SUM(sl.quantity), 0) as annual_demand
            FROM products p
            LEFT JOIN sales_log sl ON p.id = sl.product_id 
                AND sl.sale_date >= date('now', '-365 days')
            WHERE p.vendor_id = ? AND p.name LIKE ?
            GROUP BY p.id, p.buy_price
        """, (vendor_id, f"%{product_name}%"))
        
        result = c.fetchone()
        conn.close()

        if not result:
            return {'error': 'Product not found'}

        buy_price, annual_demand = result
        
        # Estimate costs (can be configured per vendor)
        ordering_cost = 100  # Estimated cost per order
        holding_cost_rate = 0.20  # 20% of item cost per year
        holding_cost = buy_price * holding_cost_rate

        if annual_demand > 0 and holding_cost > 0:
            eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        else:
            eoq = 0

        return {
            'eoq': round(eoq, 0),
            'annual_demand': annual_demand,
            'ordering_cost': ordering_cost,
            'holding_cost': round(holding_cost, 2),
            'recommendation': f"Optimal order quantity: {round(eoq, 0)} units"
        }

    def calculate_safety_stock(self, vendor_email: str, product_name: str) -> Dict:
        """Calculate Safety Stock = (Max Daily Usage × Max Lead Time) – (Avg Daily Usage × Avg Lead Time)"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Calculate daily usage statistics
        c.execute("""
            SELECT AVG(daily_usage.daily_qty) as avg_daily_usage,
                   MAX(daily_usage.daily_qty) as max_daily_usage
            FROM (
                SELECT sale_date, SUM(quantity) as daily_qty
                FROM sales_log sl
                JOIN products p ON sl.product_id = p.id
                WHERE sl.vendor_id = ? AND p.name LIKE ? 
                    AND sl.sale_date >= date('now', '-60 days')
                GROUP BY sale_date
            ) daily_usage
        """, (vendor_id, f"%{product_name}%"))
        
        result = c.fetchone()
        conn.close()

        if not result:
            return {'error': 'No sales data found for product'}

        avg_daily_usage, max_daily_usage = result
        avg_daily_usage = avg_daily_usage or 0
        max_daily_usage = max_daily_usage or 0

        # Estimated lead times (can be configured per product)
        avg_lead_time = 7  # 7 days average
        max_lead_time = 14  # 14 days maximum

        safety_stock = (max_daily_usage * max_lead_time) - (avg_daily_usage * avg_lead_time)
        safety_stock = max(0, safety_stock)  # Cannot be negative

        return {
            'safety_stock': round(safety_stock, 0),
            'avg_daily_usage': round(avg_daily_usage, 2),
            'max_daily_usage': round(max_daily_usage, 2),
            'avg_lead_time': avg_lead_time,
            'max_lead_time': max_lead_time,
            'recommendation': f"Maintain {round(safety_stock, 0)} units as safety stock"
        }

    def calculate_fill_rate(self, vendor_email: str, days: int = 30) -> Dict:
        """Calculate Fill Rate = (Orders Fulfilled / Total Orders) × 100"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get total orders and fulfilled orders
        c.execute("""
            SELECT COUNT(*) as total_orders,
                   SUM(CASE WHEN quantity > 0 THEN 1 ELSE 0 END) as fulfilled_orders
            FROM sales_log
            WHERE vendor_id = ? AND sale_date >= date('now', '-{} days')
        """.format(days), (vendor_id,))
        
        result = c.fetchone()
        conn.close()

        total_orders, fulfilled_orders = result
        fill_rate = (fulfilled_orders / total_orders * 100) if total_orders > 0 else 0

        return {
            'fill_rate': round(fill_rate, 2),
            'total_orders': total_orders,
            'fulfilled_orders': fulfilled_orders,
            'period_days': days,
            'status': 'Excellent' if fill_rate >= 95 else 'Good' if fill_rate >= 85 else 'Needs Improvement'
        }

    def detect_dead_stock(self, vendor_email: str, stagnation_days: int = 90) -> Dict:
        """Detect products with no sales in specified period"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT p.name, p.quantity, p.buy_price, p.sale_price,
                   (p.quantity * p.buy_price) as tied_capital,
                   COALESCE(MAX(sl.sale_date), 'Never') as last_sale
            FROM products p
            LEFT JOIN sales_log sl ON p.id = sl.product_id
            WHERE p.vendor_id = ? 
                AND p.quantity > 0
                AND (sl.sale_date IS NULL OR sl.sale_date < date('now', '-{} days'))
            GROUP BY p.id, p.name, p.quantity, p.buy_price, p.sale_price
            ORDER BY tied_capital DESC
        """.format(stagnation_days), (vendor_id,))
        
        results = c.fetchall()
        conn.close()

        dead_stock = []
        total_tied_capital = 0

        for name, quantity, buy_price, sale_price, tied_capital, last_sale in results:
            dead_stock.append({
                'product_name': name,
                'quantity': quantity,
                'buy_price': buy_price,
                'sale_price': sale_price,
                'tied_capital': round(tied_capital, 2),
                'last_sale': last_sale,
                'recommended_action': self._get_clearance_strategy(quantity, buy_price, sale_price)
            })
            total_tied_capital += tied_capital

        return {
            'dead_stock_items': dead_stock,
            'total_items': len(dead_stock),
            'total_tied_capital': round(total_tied_capital, 2),
            'stagnation_period_days': stagnation_days
        }

    def get_top_performers_advanced(self, vendor_email: str, days: int = 30) -> Dict:
        """Get top 3 products by volume, revenue, and margin"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Top by volume
        c.execute("""
            SELECT p.name, SUM(sl.quantity) as total_volume,
                   SUM(sl.total_amount) as revenue,
                   SUM(sl.quantity * p.buy_price) as cost,
                   (SUM(sl.total_amount) - SUM(sl.quantity * p.buy_price)) as profit,
                   ((SUM(sl.total_amount) - SUM(sl.quantity * p.buy_price)) / SUM(sl.total_amount) * 100) as margin_percent
            FROM sales_log sl
            JOIN products p ON sl.product_id = p.id
            WHERE sl.vendor_id = ? AND sl.sale_date >= date('now', '-{} days')
            GROUP BY p.id, p.name
            ORDER BY total_volume DESC
            LIMIT 3
        """.format(days), (vendor_id,))
        
        top_by_volume = c.fetchall()

        # Top by revenue
        c.execute("""
            SELECT p.name, SUM(sl.quantity) as total_volume,
                   SUM(sl.total_amount) as revenue,
                   SUM(sl.quantity * p.buy_price) as cost,
                   (SUM(sl.total_amount) - SUM(sl.quantity * p.buy_price)) as profit,
                   ((SUM(sl.total_amount) - SUM(sl.quantity * p.buy_price)) / SUM(sl.total_amount) * 100) as margin_percent
            FROM sales_log sl
            JOIN products p ON sl.product_id = p.id
            WHERE sl.vendor_id = ? AND sl.sale_date >= date('now', '-{} days')
            GROUP BY p.id, p.name
            ORDER BY revenue DESC
            LIMIT 3
        """.format(days), (vendor_id,))
        
        top_by_revenue = c.fetchall()

        # Top by margin
        c.execute("""
            SELECT p.name, SUM(sl.quantity) as total_volume,
                   SUM(sl.total_amount) as revenue,
                   SUM(sl.quantity * p.buy_price) as cost,
                   (SUM(sl.total_amount) - SUM(sl.quantity * p.buy_price)) as profit,
                   ((SUM(sl.total_amount) - SUM(sl.quantity * p.buy_price)) / SUM(sl.total_amount) * 100) as margin_percent
            FROM sales_log sl
            JOIN products p ON sl.product_id = p.id
            WHERE sl.vendor_id = ? AND sl.sale_date >= date('now', '-{} days')
            GROUP BY p.id, p.name
            HAVING SUM(sl.total_amount) > 0
            ORDER BY margin_percent DESC
            LIMIT 3
        """.format(days), (vendor_id,))
        
        top_by_margin = c.fetchall()

        conn.close()

        def format_product_data(results):
            return [{
                'name': row[0],
                'volume': row[1],
                'revenue': round(row[2], 2),
                'cost': round(row[3], 2),
                'profit': round(row[4], 2),
                'margin_percent': round(row[5], 2)
            } for row in results]

        return {
            'top_by_volume': format_product_data(top_by_volume),
            'top_by_revenue': format_product_data(top_by_revenue),
            'top_by_margin': format_product_data(top_by_margin),
            'period_days': days
        }

    def analyze_cost_to_sale_ratio(self, vendor_email: str) -> Dict:
        """Analyze cost-to-sale ratio across products"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT p.name, p.buy_price, p.sale_price,
                   (p.buy_price / p.sale_price * 100) as cost_ratio,
                   ((p.sale_price - p.buy_price) / p.sale_price * 100) as margin_percent,
                   COALESCE(SUM(sl.quantity), 0) as total_sold
            FROM products p
            LEFT JOIN sales_log sl ON p.id = sl.product_id 
                AND sl.sale_date >= date('now', '-30 days')
            WHERE p.vendor_id = ?
            GROUP BY p.id, p.name, p.buy_price, p.sale_price
            ORDER BY margin_percent DESC
        """, (vendor_id,))
        
        results = c.fetchall()
        conn.close()

        analysis = []
        for name, buy_price, sale_price, cost_ratio, margin_percent, total_sold in results:
            status = 'Excellent' if margin_percent >= 50 else 'Good' if margin_percent >= 30 else 'Fair' if margin_percent >= 20 else 'Poor'
            
            analysis.append({
                'product_name': name,
                'buy_price': buy_price,
                'sale_price': sale_price,
                'cost_ratio': round(cost_ratio, 2),
                'margin_percent': round(margin_percent, 2),
                'total_sold_30_days': total_sold,
                'margin_status': status,
                'recommendation': self._get_pricing_recommendation(margin_percent, total_sold)
            })

        return {'cost_analysis': analysis}

    def generate_monthly_performance_summary(self, vendor_email: str, month_offset: int = 0) -> Dict:
        """Generate natural language monthly performance summary"""
        vendor_id = self.get_vendor_id(vendor_email)
        if not vendor_id:
            return {'error': 'Vendor not found'}

        # Calculate target month
        target_date = datetime.now() - timedelta(days=30 * month_offset)
        month_name = target_date.strftime('%B %Y')

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get month data
        c.execute("""
            SELECT COUNT(*) as total_orders,
                   SUM(total_amount) as revenue,
                   SUM(quantity) as units_sold,
                   AVG(total_amount) as avg_order_value
            FROM sales_log
            WHERE vendor_id = ? 
                AND sale_date >= date('now', 'start of month', '-{} months')
                AND sale_date < date('now', 'start of month', '-{} months', '+1 month')
        """.format(month_offset, month_offset), (vendor_id,))
        
        month_data = c.fetchone()

        # Get expenses for the month
        c.execute("""
            SELECT SUM(amount) as total_expenses
            FROM expenses
            WHERE vendor_id = ?
                AND date >= date('now', 'start of month', '-{} months')
                AND date < date('now', 'start of month', '-{} months', '+1 month')
        """.format(month_offset, month_offset), (vendor_id,))
        
        expenses_data = c.fetchone()

        conn.close()

        total_orders, revenue, units_sold, avg_order_value = month_data
        total_expenses = expenses_data[0] or 0

        # Generate summary
        net_profit = (revenue or 0) - total_expenses
        profit_margin = (net_profit / revenue * 100) if revenue and revenue > 0 else 0

        summary = f"""📊 **Performance Summary for {month_name}**

**Sales Performance:**
• Total Orders: {total_orders or 0}
• Revenue: ₹{revenue or 0:,.2f}
• Units Sold: {units_sold or 0}
• Average Order Value: ₹{avg_order_value or 0:.2f}

**Financial Health:**
• Total Expenses: ₹{total_expenses:,.2f}
• Net Profit: ₹{net_profit:,.2f}
• Profit Margin: {profit_margin:.1f}%

**Assessment:** {self._assess_monthly_performance(total_orders or 0, revenue or 0, profit_margin)}"""

        return {
            'summary_text': summary,
            'month': month_name,
            'metrics': {
                'total_orders': total_orders or 0,
                'revenue': revenue or 0,
                'units_sold': units_sold or 0,
                'avg_order_value': avg_order_value or 0,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
                'profit_margin': profit_margin
            }
        }

    # Helper methods
    def _interpret_turnover_ratio(self, ratio: float) -> str:
        if ratio >= 12:
            return "Excellent - Very fast inventory movement"
        elif ratio >= 6:
            return "Good - Healthy inventory turnover"
        elif ratio >= 3:
            return "Average - Consider optimizing stock levels"
        else:
            return "Poor - Inventory moving too slowly"

    def _get_clearance_strategy(self, quantity: int, buy_price: float, sale_price: float) -> str:
        margin = ((sale_price - buy_price) / sale_price * 100)
        if quantity > 50:
            return "Bundle deals or bulk discounts"
        elif margin > 30:
            return "15-20% discount to move inventory"
        else:
            return "Consider liquidation or return to supplier"

    def _get_pricing_recommendation(self, margin_percent: float, sales_volume: int) -> str:
        if margin_percent < 20 and sales_volume > 10:
            return "Increase price - High demand, low margin"
        elif margin_percent > 50 and sales_volume < 5:
            return "Consider reducing price to boost sales"
        elif margin_percent >= 30 and sales_volume >= 10:
            return "Optimal pricing - Maintain current strategy"
        else:
            return "Monitor closely and adjust based on market response"

    def _assess_monthly_performance(self, orders: int, revenue: float, profit_margin: float) -> str:
        if orders >= 100 and revenue >= 50000 and profit_margin >= 20:
            return "Outstanding performance! 🎉"
        elif orders >= 50 and revenue >= 25000 and profit_margin >= 15:
            return "Good performance with room for growth 📈"
        elif orders >= 20 and revenue >= 10000 and profit_margin >= 10:
            return "Steady performance, focus on optimization 🔧"
        else:
            return "Needs attention - Consider marketing or pricing strategies 🚨"
