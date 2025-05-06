# 💰 Budget Tracker Web App

A fully-featured budget tracker built with Flask to manage your income, expenses, and spending insights — with cool features like currency conversion, recurring entries, expense sharing, AI-powered analytics, dark mode, and even a voice assistant!

---

## 🔧 Features

- ✅ Secure user login & registration
- ➕ Add/Edit/Delete income and expenses
- 📊 Graphs and spending summaries
- 🔄 Recurring expenses/income support
- 🌍 Currency conversion with live exchange rates
- 🤝 Expense sharing among friends
- 🧠 AI-based auto-categorization and insights
- 🗣 Voice Assistant for hands-free commands
- 🌙 Dark Mode toggle
- 📁 Export expenses to CSV
- 👤 User profile page

---

## 🛠 Technologies Used

- **Python + Flask** (Backend)
- **SQLite** (Database)
- **HTML/CSS + Bootstrap** (Frontend)
- **Chart.js** (Graphs)
- **SpeechRecognition + PyAudio** (Voice assistant)
- **scikit-learn** (ML model)

---

## 🧪 Running Locally

```bash
# Clone the repo
git clone https://github.com/yourusername/budget-tracker.git
cd budget-tracker

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export FLASK_APP=run.py
export FLASK_ENV=development

# Run the app
python run.py
