from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def _database_uri():
    import os

    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            return database_url.replace('postgres://', 'postgresql://', 1)
        return database_url

    if os.environ.get('VERCEL'):
        return 'sqlite:////tmp/budget.db'

    return 'sqlite:///budget.db'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = __import__('os').environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = _database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/profile_pics'

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
