# recurring_expenses.py
# Handles logic for recurring incomes and expenses (e.g., monthly rent, salary)

from datetime import datetime, timedelta
from ..models import RecurringTransaction, Income, Expense
from .. import db

def process_recurring_entries(user_id):
    """
    Process recurring entries for a specific user and add them if due.

    Args:
        user_id (int): ID of the user whose recurring entries will be processed.
    """
    today = datetime.utcnow()
    
    # Get all recurring transactions for the user
    recurring_entries = RecurringTransaction.query.filter_by(user_id=user_id).all()

    for entry in recurring_entries:
        # Check if it's time to add the next entry
        if entry.next_date <= today:
            if entry.type == 'income':
                new_entry = Income(
                    amount=entry.amount,
                    source=entry.category or 'Recurring Income',
                    date=today.date(),
                    is_recurring=True,
                    frequency=entry.interval,
                    user_id=user_id
                )
            else:
                new_entry = Expense(
                    amount=entry.amount,
                    category=entry.category or 'Recurring Expense',
                    date=today,
                    is_recurring=True,
                    frequency=entry.interval,
                    user_id=user_id
                )
            db.session.add(new_entry)

            # Update the next due date based on the frequency
            if entry.interval == 'daily':
                entry.next_date += timedelta(days=1)
            elif entry.interval == 'weekly':
                entry.next_date += timedelta(weeks=1)
            elif entry.interval == 'monthly':
                entry.next_date = add_month(entry.next_date)

    db.session.commit()


def add_month(date):
    """
    Add one calendar month to the given date.

    Args:
        date (datetime.date): The current date.

    Returns:
        datetime.date: Date incremented by one month.
    """
    if date.month == 12:
        return date.replace(year=date.year + 1, month=1)
    else:
        return date.replace(month=date.month + 1)
