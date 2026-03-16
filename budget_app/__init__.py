from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy import inspect, text

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

    # Ensure tables exist for fresh deployments where migrations haven't been run.
    with app.app_context():
        db.create_all()
        _ensure_runtime_columns()

    return app


def _ensure_runtime_columns():
    inspector = inspect(db.engine)
    required_columns = {
        'user': {
            'is_guest': "ALTER TABLE \"user\" ADD COLUMN is_guest BOOLEAN DEFAULT FALSE NOT NULL",
            'invite_token': "ALTER TABLE \"user\" ADD COLUMN invite_token VARCHAR(64)"
        },
        'income': {
            'currency_code': "ALTER TABLE income ADD COLUMN currency_code VARCHAR(3) DEFAULT 'USD' NOT NULL"
        },
        'expense': {
            'currency_code': "ALTER TABLE expense ADD COLUMN currency_code VARCHAR(3) DEFAULT 'USD' NOT NULL"
        },
        'shared_expense': {
            'currency_code': "ALTER TABLE shared_expense ADD COLUMN currency_code VARCHAR(3) DEFAULT 'USD' NOT NULL",
            'split_method': "ALTER TABLE shared_expense ADD COLUMN split_method VARCHAR(20) DEFAULT 'equal' NOT NULL"
        },
    }

    for table_name, columns in required_columns.items():
        if not inspector.has_table(table_name):
            continue

        existing_columns = {column['name'] for column in inspector.get_columns(table_name)}
        for column_name, statement in columns.items():
            if column_name not in existing_columns:
                db.session.execute(text(statement))
                db.session.commit()
