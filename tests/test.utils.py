# tests/test_utils.py

"""
Tests for utility functions (currency converter, ML predictions, etc.).
"""

from app.currency_converter import convert_currency
from app.ml_utils import analyze_spending_behavior

def test_currency_conversion():
    result = convert_currency(100, 'USD', 'INR')
    assert isinstance(result, (float, int))
    assert result > 0

def test_spending_insight():
    expenses = [
        {'amount': 500, 'category': 'Food'},
        {'amount': 800, 'category': 'Travel'}
    ]
    result = analyze_spending_behavior(expenses)
    assert 'insight' in result.lower()
