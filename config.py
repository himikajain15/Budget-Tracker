# config.py

import os

class Config:
    """Base configuration for Flask app."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///budget_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
