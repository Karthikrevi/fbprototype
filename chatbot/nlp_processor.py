
import re
from typing import Dict, List, Tuple, Optional

class BusinessQueryProcessor:
    def __init__(self):
        # Define business intent patterns
        self.business_patterns = {
            'monthly_performance': [
                r'how.*doing.*month', r'am i doing well', r'monthly performance',
                r'how.*performed.*month', r'this month.*results', r'month.*summary'
            ],
            'sales_problems': [
                r'what.*dragging.*sales', r'sales.*down', r'poor sales', r'low sales',
                r'why.*sales.*low', r'sales.*problem', r'revenue.*drop'
            ],
            'restock_needed': [
                r'need.*restock', r'low.*stock(?!.*clear|.*slow)', r'out.*stock(?!.*clear)',
                r'inventory.*low', r'stock.*running.*low',
                r'do i need to restock', r'do i need to reorder', r'restock anything',
                r'reorder anything', r'running out of', r'running low on',
                r'items running low', r'any items low', r'what.*restock',
                r'need to buy more', r'replenish',
                r'need more stock', r'stock levels(?!.*ratio)', r'stock check(?!.*clear)',
                r'items.*need.*ordering'
            ],
            'profit_per_item': [
                r'profit.*per.*item', r'average.*profit', r'profit.*margin.*product',
                r'making.*per.*item', r'profit.*each', r'margin.*per.*unit'
            ],
            'inventory_turnover': [
                r'turnover.*stock', r'how.*often.*turning', r'inventory.*turnover',
                r'stock.*rotation', r'inventory.*velocity', r'inventory.*turning',
                r'how.*fast.*inventory', r'turnover.*ratio', r'stock.*turnover'
            ],
            'safety_stock_check': [
                r'enough.*safety.*stock', r'safety.*stock.*for', r'buffer.*stock',
                r'minimum.*stock.*level', r'safety.*inventory'
            ],
            'ideal_order_quantity': [
                r'ideal.*order.*quantity', r'optimal.*order', r'eoq', r'how.*much.*order',
                r'economic.*order', r'best.*quantity.*order'
            ],
            'product_margin': [
                r'profit.*margin.*on', r'margin.*for', r'profitability.*of',
                r'how.*profitable.*is', r'profit.*on'
            ],
            'product_demand': [
                r'is.*still.*in.*demand', r'demand.*for', r'popular.*still',
                r'selling.*well', r'market.*demand'
            ],
            'best_selling_product': [
                r'best.*selling.*product', r'top.*selling', r'most.*popular',
                r'bestseller', r'highest.*sales'
            ],
            'dead_stock_analysis': [
                r'dead.*stock', r'stagnant.*inventory', r'slow.*moving',
                r'not.*selling', r'inventory.*not.*moving'
            ],
            'expense_analysis': [
                r'expense', r'spending', r'cost.*breakdown', r'what.*am.*i.*spending',
                r'operational.*cost', r'outgoing', r'where.*money.*going'
            ],
            'clearance_strategy': [
                r'clearance.*strategy', r'how.*clear.*stock', r'liquidation',
                r'get.*rid.*of.*inventory', r'move.*slow.*stock',
                r'clear.*slow.*stock', r'clear.*old.*stock', r'sell.*off.*stock',
                r'reduce.*excess.*stock', r'dispose.*stock'
            ],
            'reorder_point': [
                r'reorder.*point', r'when.*should.*reorder', r'when.*to.*reorder',
                r'at.*what.*level.*reorder', r'reorder.*level', r'rop\b',
                r'when.*place.*order', r'trigger.*point.*reorder', r'reorder.*threshold'
            ],
            'days_sales_inventory': [
                r'days.*sales.*inventory', r'dsi\b', r'how.*many.*days.*sell',
                r'days.*to.*sell.*inventory', r'inventory.*days', r'how.*long.*sell.*stock',
                r'average.*days.*sell', r'days.*of.*inventory'
            ],
            'gmroi': [
                r'gmroi', r'gross.*margin.*return', r'return.*on.*inventory.*investment',
                r'profit.*per.*inventory.*dollar', r'inventory.*roi', r'roi.*inventory',
                r'return.*inventory', r'how.*much.*earn.*per.*dollar.*inventory'
            ],
            'abc_analysis': [
                r'abc.*analysis', r'abc.*classification', r'categorize.*inventory',
                r'classify.*products', r'product.*classification', r'inventory.*categories',
                r'a.*b.*c.*items', r'high.*value.*items', r'pareto.*inventory',
                r'which.*products.*most.*important'
            ],
            'inventory_to_sales_ratio': [
                r'inventory.*to.*sales.*ratio', r'inventory.*sales.*ratio',
                r'stock.*to.*sales', r'how.*much.*inventory.*per.*sale',
                r'inventory.*vs.*sales', r'inventory.*compared.*sales'
            ],
            'fill_rate': [
                r'fill.*rate', r'order.*fulfillment.*rate', r'fulfillment.*percentage',
                r'how.*many.*orders.*fulfilled', r'order.*completion.*rate',
                r'customer.*order.*fill', r'shipped.*orders.*percentage'
            ],
            'stock_cover': [
                r'stock.*cover', r'how.*long.*stock.*last', r'days.*of.*cover',
                r'how.*many.*days.*stock', r'inventory.*duration', r'stock.*duration',
                r'when.*will.*stock.*run.*out', r'stock.*will.*last'
            ]
        }

        # Product-related keywords
        self.product_keywords = [
            'collar', 'leash', 'food', 'treat', 'toy', 'shampoo', 'flea', 'tick',
            'bed', 'bowl', 'carrier', 'medicine', 'supplement', 'brush', 'nail'
        ]

        # Time-related keywords
        self.time_keywords = {
            'today': 1, 'yesterday': 1, 'week': 7, 'month': 30, 'quarter': 90,
            'year': 365, 'january': 'jan', 'february': 'feb', 'march': 'mar',
            'april': 'apr', 'may': 'may', 'june': 'jun', 'july': 'jul',
            'august': 'aug', 'september': 'sep', 'october': 'oct',
            'november': 'nov', 'december': 'dec'
        }

    def process_business_query(self, query: str) -> Dict:
        """Process business query and extract intent, entities, and context"""
        query_lower = query.lower()
        
        # Extract intent
        intent = self._extract_business_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query_lower)
        
        # Generate structured query
        structured_query = self._generate_structured_query(intent, entities, query_lower)
        
        return {
            'original_query': query,
            'intent': intent,
            'entities': entities,
            'structured_query': structured_query,
            'confidence': self._calculate_confidence(intent, entities)
        }

    def _extract_business_intent(self, query: str) -> str:
        """Extract business intent from query"""
        priority_intents = ['clearance_strategy', 'reorder_point', 'days_sales_inventory',
                            'gmroi', 'abc_analysis', 'fill_rate', 'inventory_to_sales_ratio',
                            'stock_cover', 'inventory_turnover', 'safety_stock_check',
                            'ideal_order_quantity', 'dead_stock_analysis', 'sales_problems',
                            'profit_per_item', 'product_margin', 'product_demand',
                            'best_selling_product', 'monthly_performance', 'restock_needed']
        
        for intent in priority_intents:
            patterns = self.business_patterns.get(intent, [])
            for pattern in patterns:
                if re.search(pattern, query):
                    return intent
        
        if 'reorder point' in query or 'rop' in query.split():
            return 'reorder_point'
        elif 'gmroi' in query or 'gross margin return' in query:
            return 'gmroi'
        elif 'abc' in query.split() and ('analysis' in query or 'classif' in query or 'categor' in query):
            return 'abc_analysis'
        elif 'dsi' in query.split() or 'days sales of inventory' in query:
            return 'days_sales_inventory'
        elif 'fill rate' in query or 'fulfillment rate' in query:
            return 'fill_rate'
        elif 'inventory to sales' in query or 'stock to sales' in query:
            return 'inventory_to_sales_ratio'
        elif 'clearance' in query or 'liquidat' in query or ('clear' in query and 'stock' in query):
            return 'clearance_strategy'
        elif any(word in query for word in ['turnover']) and 'ratio' in query:
            return 'inventory_turnover'
        elif any(word in query for word in ['eoq', 'economic order']):
            return 'ideal_order_quantity'
        elif any(word in query for word in ['safety stock', 'buffer stock']):
            return 'safety_stock_check'
        elif any(word in query for word in ['dead stock', 'stagnant']):
            return 'dead_stock_analysis'
        elif 'margin' in query and 'product' in query:
            return 'product_margin'
        elif any(word in query for word in ['performance', 'summary']):
            return 'monthly_performance'
        
        return 'general_business'

    def _extract_entities(self, query: str) -> Dict:
        """Extract entities like products, time periods, etc."""
        entities = {
            'products': [],
            'time_period': None,
            'metrics': [],
            'month': None
        }

        # Extract products
        for keyword in self.product_keywords:
            if keyword in query:
                entities['products'].append(keyword)

        # Extract time periods
        for time_word, period in self.time_keywords.items():
            if time_word in query:
                if isinstance(period, int):
                    entities['time_period'] = period
                else:
                    entities['month'] = period

        # Extract metrics
        metric_keywords = ['revenue', 'profit', 'margin', 'turnover', 'volume', 'sales']
        for metric in metric_keywords:
            if metric in query:
                entities['metrics'].append(metric)

        return entities

    def _generate_structured_query(self, intent: str, entities: Dict, query: str) -> str:
        """Generate a structured query for the analytics engine"""
        if intent == 'monthly_performance':
            if entities.get('month'):
                return f"Generate monthly performance summary for {entities['month']}"
            else:
                return "Generate monthly performance summary for current month"
        
        elif intent == 'inventory_turnover':
            if entities.get('products'):
                return f"Calculate inventory turnover ratio for {', '.join(entities['products'])}"
            else:
                return "Calculate overall inventory turnover ratio"
        
        elif intent == 'safety_stock_check':
            if entities.get('products'):
                return f"Check safety stock levels for {entities['products'][0]}"
            else:
                return "Check safety stock levels for all products"
        
        elif intent == 'ideal_order_quantity':
            if entities.get('products'):
                return f"Calculate EOQ for {entities['products'][0]}"
            else:
                return "Show EOQ recommendations for top products"
        
        elif intent == 'product_margin':
            if entities.get('products'):
                return f"Show profit margin for {entities['products'][0]}"
            else:
                return "Show profit margins for all products"
        
        elif intent == 'dead_stock_analysis':
            return "Identify dead stock and clearance opportunities"
        
        elif intent == 'best_selling_product':
            period = entities.get('time_period', 30)
            return f"Show top selling products for last {period} days"
        
        elif intent == 'restock_needed':
            return "Show products that need restocking"
        
        else:
            return query

    def _calculate_confidence(self, intent: str, entities: Dict) -> float:
        """Calculate confidence score for the extracted intent"""
        base_confidence = 0.7 if intent != 'general_business' else 0.3
        
        # Boost confidence if entities are found
        if entities.get('products'):
            base_confidence += 0.1
        if entities.get('time_period') or entities.get('month'):
            base_confidence += 0.1
        if entities.get('metrics'):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

    def suggest_clarification(self, intent: str, entities: Dict) -> Optional[str]:
        """Suggest clarification questions for ambiguous queries"""
        if intent == 'product_margin' and not entities.get('products'):
            return "Which specific product would you like to check the profit margin for?"
        
        elif intent == 'safety_stock_check' and not entities.get('products'):
            return "Which product would you like me to check the safety stock for?"
        
        elif intent == 'ideal_order_quantity' and not entities.get('products'):
            return "Which product would you like me to calculate the optimal order quantity for?"
        
        elif intent == 'monthly_performance' and not entities.get('month'):
            return "Which month would you like to analyze? Current month or a specific month?"
        
        return None
