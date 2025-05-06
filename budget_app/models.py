from . import db
from flask_login import UserMixin
from datetime import datetime

# --------------------------- USER MODEL ---------------------------

class User(UserMixin, db.Model):
    """
    User model representing a registered user of the Budget Tracker.
    Inherits from UserMixin to work with Flask-Login.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(200), nullable=False)
    profile_picture = db.Column(db.String(150), nullable=True, default='default.jpg')

    # One-to-many relationships
    incomes = db.relationship('Income', backref='user', lazy=True)
    expenses = db.relationship('Expense', backref='user', lazy=True)
    recurring_transactions = db.relationship('RecurringTransaction', backref='user', lazy=True)

    # Group expense relationships
    groups_created = db.relationship('Group', backref='creator', lazy=True)
    group_memberships = db.relationship('GroupMember', backref='user', lazy=True)
    expenses_paid = db.relationship('SharedExpense', backref='payer', lazy=True)
    shares = db.relationship('ExpenseShare', backref='user', lazy=True)

    # Optional one-to-one profile relationship
    profile = db.relationship('UserProfile', backref='user', uselist=False)

# --------------------------- INCOME MODEL ---------------------------

class Income(db.Model):
    """
    Model to represent income records.
    """
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    date = db.Column(db.Date, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20), default='none')  # daily, weekly, monthly, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --------------------------- EXPENSE MODEL ---------------------------

class Expense(db.Model):
    """
    Model to represent expense records.
    """
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_recurring = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20), default='none')  # daily, weekly, monthly, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --------------------------- CATEGORY MODEL ---------------------------

class Category(db.Model):
    """
    Optional model to store predefined expense/income categories.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# --------------------------- RECURRING TRANSACTION MODEL ---------------------------

class RecurringTransaction(db.Model):
    """
    Model to track recurring incomes or expenses with frequency and next due date.
    """
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    interval = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly, etc.
    next_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --------------------------- USER PROFILE MODEL ---------------------------

class UserProfile(db.Model):
    """
    Optional model for extended user profile settings.
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    currency = db.Column(db.String(10), default='USD')  # Currency preference
    bio = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --------------------------- GROUP EXPENSE SYSTEM ---------------------------

class Group(db.Model):
    """
    Model representing an expense sharing group (like in Splitwise).
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Reference to creator's user ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    members = db.relationship('GroupMember', backref='group', cascade="all, delete", lazy=True)
    expenses = db.relationship('SharedExpense', backref='group', cascade="all, delete", lazy=True)

class GroupMember(db.Model):
    """
    Join table to manage users in a group.
    """
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class SharedExpense(db.Model):
    """
    Model to store shared group expenses.
    """
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to individual shares
    shares = db.relationship('ExpenseShare', backref='shared_expense', cascade="all, delete", lazy=True)

class ExpenseShare(db.Model):
    """
    Model representing how a shared expense is split among group members.
    """
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('shared_expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_owed = db.Column(db.Float, nullable=False)
