
#!/usr/bin/env python3
"""
Test script for Furry's conversational abilities
"""

import sys
import os

# Add chatbot directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inventory_bot import inventory_bot

def test_conversations():
    """Test various conversational inputs"""
    test_cases = [
        "yo",
        "hi there",
        "what's your name?",
        "how are you?",
        "thank you",
        "help",
        "what can you do?",
        "show me my top sales",
        "xyz random text"
    ]
    
    print("🐕 Testing Furry's Conversational Abilities")
    print("=" * 50)
    
    for test_input in test_cases:
        try:
            response = inventory_bot.process_query(test_input, "test@vendor.com")
            print(f"Input: '{test_input}'")
            print(f"Furry: {response}")
            print("-" * 30)
        except Exception as e:
            print(f"Error testing '{test_input}': {e}")
            print("-" * 30)

if __name__ == "__main__":
    test_conversations()
