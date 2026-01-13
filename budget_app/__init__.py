# app/__init__.py
# This file initializes the Flask application, its extensions, and registers blueprints

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize Flask extensions (not bound to the app yet)
db = SQLAlchemy()                # For ORM-based database management
login_manager = LoginManager()   # For managing user sessions and authentication
migrate = Migrate()              # For handling database migrations

def create_app():
    """
    Application factory function. Creates and configures the Flask app.
    Initializes SQLAlchemy, Flask-Login, and Flask-Migrate.
    """
    app = Flask(__name__)  # Create the Flask app instance

    # --------------------------- Configuration ---------------------------
    import os
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'  # Used for sessions & CSRF protection
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///budget.db'  # SQLite DB path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Upload folder config for profile pictures
    app.config['UPLOAD_FOLDER'] = 'static/profile_pics'

    # --------------------------- Initialize Extensions ---------------------------
    db.init_app(app)              # Bind SQLAlchemy to app
    login_manager.init_app(app)  # Bind LoginManager to app
    migrate.init_app(app, db)    # Bind Flask-Migrate to app

    # Set the default login view for @login_required
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Import models here to avoid circular imports
    from .models import User

    # --------------------------- User Loader for Flask-Login ---------------------------
    @login_manager.user_loader
    def load_user(user_id):
        """
        Loads the user by their ID for Flask-Login.
        """

        return User.query.get(int(user_id))

    # --------------------------- Register Blueprints ---------------------------
    from .routes import main as main_blueprint  # Import the main routes
    app.register_blueprint(main_blueprint)      # Register the blueprint

    return app  # Return the configured Flask app
