# Budget Tracker

A modern Flask finance app for tracking personal cash flow, reviewing expenses, and managing shared group spending with a Splitwise-style workflow.

## Highlights

- Personal dashboard with a polished finance-style UI
- Dedicated `Overview`, `Income`, and `Expenses` experiences
- Multi-currency income and expense tracking
- Shared group expenses with settlement suggestions
- Guest members for shared groups, even if they do not use the app yet
- Invite-link flow so guest members can join later and claim their balances
- Multiple shared-expense split methods:
  - Equal split
  - Percentage split
  - Exact amount split
- Profile picture uploads and personalized workspace
- Export support for CSV and PDF
- Expense category insights and analytics support

## Tech Stack

- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy
- Flask-Migrate
- WTForms / Flask-WTF
- SQLite for local development
- PostgreSQL-compatible deployment support via `DATABASE_URL`

## Core Features

### Overview Dashboard

- Key financial stats
- Income vs expense visual trend
- Spend-category view
- Recent transaction feed
- Multi-currency balance snapshot

### Income Ledger

- Add, edit, and delete income records
- Track source, amount, description, date, and currency
- View income totals by currency

### Expense Ledger

- Add, edit, and delete expense records
- Track category, amount, description, date, and currency
- View expense totals by currency

### Shared Groups

- Create shared spending groups
- Add registered users or guest members by name
- Log shared expenses in multiple currencies
- Choose how to split:
  - Equally
  - By percentage
  - By exact amount
- View member balances and suggested settlements
- Share invite links so guest members can later connect their account

### Profile and Preferences

- Update username and email
- Upload a profile picture
- Set preferred currency
- Update password

## Project Structure

```text
budget_app/
  __init__.py
  forms.py
  models.py
  routes.py
  static/
  templates/
run.py
requirements.txt
vercel.json
```

## Run Locally

### 1. Clone the repository

```powershell
git clone https://github.com/himikajain15/Budget-Tracker.git
cd Budget-Tracker
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Set environment variables

At minimum:

```powershell
$env:SECRET_KEY="local-dev-secret"
```

Optional for PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql://username:password@host:5432/dbname"
```

If `DATABASE_URL` is not set, the app uses local SQLite.

### 5. Run the app

```powershell
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## Deployment Notes

This project is configured for Vercel deployment with a Flask entrypoint.

Important environment variables for production:

- `SECRET_KEY`
- `DATABASE_URL` for persistent production data
- `CLOUDINARY_URL` or:
  - `CLOUDINARY_CLOUD_NAME`
  - `CLOUDINARY_API_KEY`
  - `CLOUDINARY_API_SECRET`

If `DATABASE_URL` is not configured on Vercel, the app falls back to temporary SQLite storage, which is not suitable for persistent production use.

For production profile image uploads on Vercel, configure Cloudinary. Without Cloudinary credentials, the app falls back to avatar initials instead of storing uploaded files.

## Resume Value

This project demonstrates:

- Full-stack Flask application development
- Authentication and profile management
- Multi-currency financial data modeling
- Shared-expense logic and balance settlement
- Guest-to-user invite conversion flows
- Product-oriented UI/UX refinement
- Deployment debugging and production readiness work

## License

This project is for educational and portfolio use.
