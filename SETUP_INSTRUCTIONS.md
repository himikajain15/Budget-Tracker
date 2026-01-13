# 🚀 Budget Tracker - Setup & Run Instructions

## Quick Start (3 Steps)
```bash
# 1. Create virtual environment and activate
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python run.py
```
Then open: **http://localhost:5000**

---

## Prerequisites
- Python 3.8 or higher installed
- pip (Python package manager)

## Step-by-Step Setup

### Step 1: Navigate to Project Directory
```bash
cd "C:\Users\user\Downloads\Budget Tracker\Budget-Tracker"
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
# source venv/bin/activate
```

You should see `(venv)` at the beginning of your command prompt when activated.

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** This may take a few minutes as it installs all required packages including Flask, SQLAlchemy, scikit-learn, etc.

### Step 4: Initialize Database (Optional - Auto-creates on first run)
The database will be created automatically when you first run the app. However, if you want to initialize it manually:

```bash
# Option 1: Using Python directly
python -c "from budget_app import create_app; from budget_app.models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created!')"

# Option 2: Using manage.py (for migrations)
python manage.py db init
python manage.py db migrate -m "Initial migration"
python manage.py db upgrade
```

**Note:** The database will be created automatically on first run, so this step is optional.

### Step 5: Run the Application
```bash
python run.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Step 6: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```
or
```
http://127.0.0.1:5000
```

## First Time Usage

1. **Register a New Account**
   - Click "Register" in the navigation
   - Fill in username, email, password
   - Optionally upload a profile picture
   - Click "Register"

2. **Login**
   - Use your registered credentials to log in

3. **Start Using the App**
   - Add your first income/expense
   - View dashboard with summaries
   - Create groups for shared expenses
   - Export your data

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Port already in use"
**Solution:** Change the port in `run.py`:
```python
app.run(debug=True, port=5001)  # Use different port
```

### Issue: Database errors
**Solution:** Delete the database file and let it recreate:
```bash
# Delete instance/budget.db (if exists)
# Then run the app again
```

### Issue: Profile picture upload fails
**Solution:** Ensure the `budget_app/static/profile_pics/` directory exists:
```bash
mkdir budget_app\static\profile_pics
```

## Optional: Environment Variables

Create a `.env` file (optional) for production settings:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///budget.db
FLASK_ENV=development
```

## Running in Production Mode

For production, disable debug mode in `run.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

## Stopping the Application

Press `Ctrl + C` in the terminal to stop the server.

## Quick Start (All-in-One)

```bash
# Navigate to project
cd "C:\Users\user\Downloads\Budget Tracker\Budget-Tracker"

# Create and activate venv
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py
```

Then open: http://localhost:5000

