
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from typing import List, Tuple, Dict
import re
import os
import spacy
from datetime import datetime

class IntentClassifier:
    def __init__(self, model_path: str = 'chatbot/models'):
        self.model_path = model_path
        self.pipeline = None
        self.confidence_threshold = 0.6
        self.nlp = None
        
        # Create models directory
        os.makedirs(model_path, exist_ok=True)
        
        # Load spaCy model if available
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Load existing model if available
        self.load_model()
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for classification"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Use spaCy for lemmatization if available
        if self.nlp:
            doc = self.nlp(text)
            text = ' '.join([token.lemma_ for token in doc if not token.is_stop])
        
        return text
    
    def create_training_pipeline(self):
        """Create the ML pipeline"""
        return Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words='english'
            )),
            ('classifier', LogisticRegression(
                random_state=42,
                max_iter=1000,
                class_weight='balanced'
            ))
        ])
    
    def train(self, training_data: List[Tuple[str, str]]) -> Dict:
        """Train the intent classifier"""
        if len(training_data) < 5:
            print("Insufficient training data. Need at least 5 samples.")
            return {'success': False, 'error': 'Insufficient training data'}
        
        # Preprocess data
        X = [self.preprocess_text(query) for query, _ in training_data]
        y = [intent for _, intent in training_data]
        
        # Check if we have enough samples for each class
        from collections import Counter
        class_counts = Counter(y)
        if min(class_counts.values()) < 2:
            print("Some intents have less than 2 samples. Adding synthetic examples.")
            X, y = self._augment_training_data(X, y, class_counts)
        
        # Split data
        if len(X) > 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = X, X, y, y
        
        # Create and train pipeline
        self.pipeline = self.create_training_pipeline()
        self.pipeline.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Save model
        self.save_model()
        
        return {
            'success': True,
            'accuracy': accuracy,
            'f1_score': f1,
            'training_samples': len(training_data),
            'classification_report': classification_report(y_test, y_pred)
        }
    
    def _augment_training_data(self, X: List[str], y: List[str], class_counts: Dict) -> Tuple[List[str], List[str]]:
        """Augment training data for classes with few samples"""
        from collections import defaultdict
        
        # Group samples by class
        class_samples = defaultdict(list)
        for query, intent in zip(X, y):
            class_samples[intent].append(query)
        
        augmented_X, augmented_y = [], []
        
        for intent, queries in class_samples.items():
            augmented_X.extend(queries)
            augmented_y.extend([intent] * len(queries))
            
            # If class has only 1 sample, create variations
            if len(queries) == 1:
                base_query = queries[0]
                variations = self._create_query_variations(base_query)
                augmented_X.extend(variations)
                augmented_y.extend([intent] * len(variations))
        
        return augmented_X, augmented_y
    
    def _create_query_variations(self, query: str) -> List[str]:
        """Create variations of a query for data augmentation"""
        variations = []
        words = query.split()
        
        # Add simple variations
        if len(words) > 1:
            # Reverse word order for some phrases
            variations.append(' '.join(reversed(words)))
            
            # Remove some words
            if len(words) > 2:
                variations.append(' '.join(words[:-1]))
                variations.append(' '.join(words[1:]))
        
        # Add question variations
        if not query.endswith('?'):
            variations.append(query + '?')
        
        # Add common prefixes
        prefixes = ['show me', 'what are', 'tell me about', 'give me']
        for prefix in prefixes:
            if not query.startswith(prefix):
                variations.append(f"{prefix} {query}")
        
        return variations[:3]  # Limit to 3 variations
    
    def predict(self, query: str) -> Tuple[str, float]:
        """Predict intent for a query"""
        if not self.pipeline:
            return 'unknown', 0.0
        
        processed_query = self.preprocess_text(query)
        
        # Get prediction probabilities
        probabilities = self.pipeline.predict_proba([processed_query])[0]
        classes = self.pipeline.classes_
        
        # Get the best prediction
        best_idx = np.argmax(probabilities)
        best_intent = classes[best_idx]
        confidence = probabilities[best_idx]
        
        # Apply confidence threshold
        if confidence < self.confidence_threshold:
            return 'unknown', confidence
        
        return best_intent, confidence
    
    def get_intent_probabilities(self, query: str) -> Dict[str, float]:
        """Get probabilities for all intents"""
        if not self.pipeline:
            return {}
        
        processed_query = self.preprocess_text(query)
        probabilities = self.pipeline.predict_proba([processed_query])[0]
        classes = self.pipeline.classes_
        
        return dict(zip(classes, probabilities))
    
    def save_model(self):
        """Save the trained model"""
        if self.pipeline:
            model_file = os.path.join(self.model_path, 'intent_classifier.pkl')
            with open(model_file, 'wb') as f:
                pickle.dump(self.pipeline, f)
            print(f"Model saved to {model_file}")
    
    def load_model(self):
        """Load a previously trained model"""
        model_file = os.path.join(self.model_path, 'intent_classifier.pkl')
        if os.path.exists(model_file):
            try:
                with open(model_file, 'rb') as f:
                    self.pipeline = pickle.load(f)
                print(f"Model loaded from {model_file}")
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
                return False
        return False
    
    def retrain_with_feedback(self, feedback_data: List[Dict], original_training_data: List[Tuple[str, str]]) -> Dict:
        """Retrain model incorporating feedback data"""
        # Convert feedback to training samples
        additional_samples = []
        
        for feedback in feedback_data:
            if feedback['feedback'] == 1:  # Positive feedback
                additional_samples.append((feedback['query'], feedback['intent']))
            elif feedback['feedback'] == 0 and feedback['confidence'] > 0.5:
                # Negative feedback on confident predictions - might be wrong intent
                # For now, just reduce confidence in similar predictions
                pass
        
        # Combine with original training data
        all_training_data = original_training_data + additional_samples
        
        # Retrain
        return self.train(all_training_data)
