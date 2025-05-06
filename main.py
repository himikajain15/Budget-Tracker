from budget_app import create_app
from budget_app.models import db

# Initialize the app
app = create_app()

# This will recreate the database schema
with app.app_context():
    db.create_all()

print("Database tables created successfully.")
