# test_db.py

from budget_app import create_app, db
from budget_app.models import User  # Make sure your User model is correctly imported

app = create_app()

with app.app_context():
    # Test if we can access the database
    user = User.query.first()  # Try querying the User table
    if user:
        print(user.username)  # Print the first user's username if any are found
    else:
        print("No users found")
