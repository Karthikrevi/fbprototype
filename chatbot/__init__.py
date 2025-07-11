
"""
FurrButler Chatbot Module

Advanced AI-powered inventory and business analytics chatbot
"""

try:
    # Initialize core components
    from .database import ChatbotDatabase
    from .classifier import IntentClassifier
    from .vector_matcher import VectorMatcher
    from .training import TrainingManager
    from .logger import ConversationLogger
    from .analytics_engine import AdvancedAnalyticsEngine
    from .nlp_processor import BusinessQueryProcessor
    
    # Initialize main bot (only import if needed to avoid circular imports)
    __all__ = [
        'ChatbotDatabase',
        'IntentClassifier', 
        'VectorMatcher',
        'TrainingManager',
        'ConversationLogger',
        'AdvancedAnalyticsEngine',
        'BusinessQueryProcessor'
    ]
    
except ImportError as e:
    print(f"Warning: Could not import all chatbot components: {e}")
    __all__ = []
