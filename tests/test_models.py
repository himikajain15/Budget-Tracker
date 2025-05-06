# tests/test_models.py

"""
Unit tests for the database models (User, Income, Expense).
"""

import pytest
from budget_app import create_app, db
from budget_app.models import User, Income, Expense

@pytest.fixture
def app_context():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for testing
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_user_creation(app_context):
    # Test creation of a new user
    user = User(username='testuser', email='test@example.com')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()

    # Fetch user and assert values
    saved_user = User.query.filter_by(username='testuser').first()
    assert saved_user is not None
    assert saved_user.email == 'test@example.com'
    assert saved_user.check_password('password')

def test_income_entry(app_context):
    # Add income entry
    income = Income(amount=1000, source='Job', user_id=1)
    db.session.add(income)
    db.session.commit()

    saved_income = Income.query.first()
    assert saved_income.amount == 1000
    assert saved_income.source == 'Job'

def test_expense_entry(app_context):
    # Add expense entry
    expense = Expense(amount=200, category='Food', user_id=1)
    db.session.add(expense)
    db.session.commit()

    saved_expense = Expense.query.first()
    assert saved_expense.amount == 200
    assert saved_expense.category == 'Food'
