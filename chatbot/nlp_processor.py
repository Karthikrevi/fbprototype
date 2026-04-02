
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
                r'need.*restock', r'should.*reorder', r'low.*stock', r'out.*stock',
                r'inventory.*low', r'need.*order', r'stock.*running.*low',
                r'do i need to restock', r'do i need to reorder', r'restock anything',
                r'reorder anything', r'running out of', r'running low on',
                r'items running low', r'any items low', r'what.*restock',
                r'what.*reorder', r'need to buy more', r'replenish',
                r'need more stock', r'stock levels', r'stock check',
                r'what should i order', r'place.*order', r'items.*need.*ordering'
            ],
            'profit_per_item': [
                r'profit.*per.*item', r'average.*profit', r'profit.*margin.*product',
                r'making.*per.*item', r'profit.*each', r'margin.*per.*unit'
            ],
            'inventory_turnover': [
                r'turnover.*stock', r'how.*often.*turning', r'inventory.*turnover',
                r'stock.*rotation', r'inventory.*velocity'
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
            'clearance_strategy': [
                r'clearance.*strategy', r'how.*clear.*stock', r'liquidation',
                r'get.*rid.*of.*inventory', r'move.*slow.*stock'
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
        for intent, patterns in self.business_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return intent
        
        # Check for specific analytics requests
        if any(word in query for word in ['turnover', 'ratio']):
            return 'inventory_turnover'
        elif any(word in query for word in ['eoq', 'economic', 'optimal']):
            return 'ideal_order_quantity'
        elif any(word in query for word in ['safety', 'buffer', 'minimum']):
            return 'safety_stock_check'
        elif any(word in query for word in ['dead', 'stagnant', 'slow']):
            return 'dead_stock_analysis'
        elif any(word in query for word in ['margin', 'profit']):
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
