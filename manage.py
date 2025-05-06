# Importing necessary modules and functions
from budget_app import create_app, db  # Import the Flask app and db instance from the app module
from flask_script import Manager  # Manager to handle command-line tasks such as running the app or handling migrations
from flask_migrate import Migrate, MigrateCommand  # Migrate for handling database migrations
from budget_app.models import User, Expense, Income  # Import your models (User, Expense, Income) for database migrations

# Initialize the Flask application using the create_app function
# This will configure the app and set up the database and other extensions
app = create_app()

# Initialize Migrate for handling database migrations
migrate = Migrate(app, db)

# Initialize Flask-Script Manager to manage the application from the command line
manager = Manager(app)

# Add the 'db' command to the manager, which allows us to run database migration commands
# Examples: `python manage.py db init`, `python manage.py db migrate`, `python manage.py db upgrade`
manager.add_command('db', MigrateCommand)

# This block ensures that the script is only executed when run directly (not when imported as a module)
if __name__ == "__main__":
    manager.run()  # Run the manager, which will start the app and allow command-line commands
