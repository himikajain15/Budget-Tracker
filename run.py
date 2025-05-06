# run.py

from budget_app import create_app

# Create an instance of the app
app = create_app()

if __name__ == '__main__':
    # Run the app on localhost with debug enabled
    app.run(debug=True)

