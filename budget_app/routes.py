# routes.py
# Define application routes for the enhanced Budget Tracker app with profile picture upload

import os
import secrets
import csv
from collections import Counter, defaultdict
from datetime import datetime, date
from io import BytesIO, StringIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .forms import ProfileForm
try:
    import cloudinary.uploader
except ImportError:
    cloudinary = None

from . import db
from .models import User, Income, Expense, UserProfile, Group, SharedExpense, GroupMember, ExpenseShare
from .currencies import CURRENCY_SYMBOLS
from .forms import (
    RegistrationForm, LoginForm, IncomeForm, ExpenseForm,
    ProfileForm, ExportForm, CreateGroupForm, AddMemberForm, AddSharedExpenseForm
)

main = Blueprint('main', __name__, template_folder='templates')


def _sum_amounts_by_currency(records):
    totals = defaultdict(float)
    for record in records:
        totals[getattr(record, 'currency_code', 'USD') or 'USD'] += record.amount
    return dict(sorted(totals.items()))


def _preferred_currency(user):
    if getattr(user, 'profile', None) and user.profile.currency:
        if user.profile.currency == 'USD':
            return 'INR'
        return user.profile.currency
    return 'INR'


def _member_display_name(user):
    if not user:
        return 'Unknown'
    if getattr(user, 'is_guest', False):
        return user.name or 'Guest member'
    return user.name or user.username


def _member_meta(user):
    if not user:
        return 'No details available'
    if getattr(user, 'is_guest', False):
        return 'Guest member'
    return user.email


def _split_method_label(split_method):
    labels = {
        'equal': 'Split equally',
        'percentage': 'Split by percentage',
        'exact': 'Split by exact amounts',
    }
    return labels.get(split_method, 'Split equally')


def _parse_split_amounts(group, amount, split_method):
    members = [member for member in group.members if member.user_id]
    if not members:
        return {}, 'Group has no members.'

    if split_method == 'equal':
        share_per_person = round(amount / len(members), 2)
        split_map = {member.user_id: share_per_person for member in members}
        adjustment = round(amount - sum(split_map.values()), 2)
        if adjustment:
            split_map[members[0].user_id] = round(split_map[members[0].user_id] + adjustment, 2)
        return split_map, None

    split_map = {}
    raw_values = {}
    for member in members:
        raw_value = (request.form.get(f'share_{member.user_id}') or '').strip()
        if not raw_value:
            return {}, f'Enter a split value for {_member_display_name(member.user)}.'
        try:
            raw_values[member.user_id] = float(raw_value)
        except ValueError:
            return {}, f'Enter a valid number for {_member_display_name(member.user)}.'

    if split_method == 'percentage':
        total_percentage = round(sum(raw_values.values()), 2)
        if abs(total_percentage - 100) > 0.05:
            return {}, 'Percentage split must total 100.'
        for user_id, percentage in raw_values.items():
            split_map[user_id] = round(amount * (percentage / 100), 2)
    elif split_method == 'exact':
        total_exact = round(sum(raw_values.values()), 2)
        if abs(total_exact - amount) > 0.05:
            return {}, 'Exact split amounts must match the total expense.'
        split_map = {user_id: round(value, 2) for user_id, value in raw_values.items()}
    else:
        return {}, 'Unsupported split method selected.'

    adjustment = round(amount - sum(split_map.values()), 2)
    if adjustment:
        first_user_id = members[0].user_id
        split_map[first_user_id] = round(split_map[first_user_id] + adjustment, 2)

    return split_map, None


def _recent_transactions(incomes, expenses):
    timeline = []

    for income in incomes:
        timeline.append({
            'kind': 'income',
            'title': income.source,
            'description': income.description or 'Income added',
            'amount': income.amount,
            'currency_code': income.currency_code or 'USD',
            'date': income.date,
        })

    for expense in expenses:
        timeline.append({
            'kind': 'expense',
            'title': expense.category,
            'description': expense.description or 'Expense logged',
            'amount': expense.amount,
            'currency_code': expense.currency_code or 'USD',
            'date': expense.date,
        })

    def _normalize_sort_date(value):
        if value is None:
            return datetime.min
        if isinstance(value, datetime):
            return value
        return datetime.combine(value, datetime.min.time())

    timeline.sort(key=lambda item: _normalize_sort_date(item['date']), reverse=True)
    return timeline[:8]


def _build_dashboard_charts(incomes, expenses):
    monthly_totals = defaultdict(lambda: {'income': 0.0, 'expense': 0.0})

    for income in incomes:
        if income.date:
            month_key = income.date.strftime('%b')
            monthly_totals[month_key]['income'] += income.amount

    for expense in expenses:
        expense_date = expense.date.date() if isinstance(expense.date, datetime) else expense.date
        if expense_date:
            month_key = expense_date.strftime('%b')
            monthly_totals[month_key]['expense'] += expense.amount

    ordered_months = list(monthly_totals.keys())[-6:]
    if not ordered_months:
        ordered_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']

    income_series = [round(monthly_totals[month]['income'], 2) for month in ordered_months]
    expense_series = [round(monthly_totals[month]['expense'], 2) for month in ordered_months]
    max_value = max(income_series + expense_series + [1])

    def _points(series):
        if len(series) == 1:
            return "0,80"
        width = 320
        height = 80
        step = width / (len(series) - 1)
        coords = []
        for index, value in enumerate(series):
            x = round(index * step, 1)
            y = round(height - ((value / max_value) * height), 1)
            coords.append(f"{x},{y}")
        return " ".join(coords)

    def _point_objects(series):
        if len(series) == 1:
            return [{'x': 0, 'y': 80, 'value': series[0]}]
        width = 320
        height = 80
        step = width / (len(series) - 1)
        points = []
        for index, value in enumerate(series):
            points.append({
                'x': round(index * step, 1),
                'y': round(height - ((value / max_value) * height), 1),
                'value': value,
            })
        return points

    category_totals = defaultdict(float)
    for expense in expenses:
        category_totals[expense.category or 'Other'] += expense.amount

    top_categories = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:4]
    top_category_max = max([value for _, value in top_categories] + [1])

    return {
        'months': ordered_months,
        'income_series': income_series,
        'expense_series': expense_series,
        'income_points': _points(income_series),
        'expense_points': _points(expense_series),
        'income_point_objects': _point_objects(income_series),
        'expense_point_objects': _point_objects(expense_series),
        'top_categories': top_categories,
        'top_category_max': top_category_max,
    }


def _build_group_snapshot(group):
    member_users = {}
    balances = defaultdict(lambda: defaultdict(float))
    expense_feed = []

    for member in group.members:
        if member.user:
            member_users[member.user_id] = member.user

    for expense in sorted(group.expenses, key=lambda item: item.created_at or datetime.min, reverse=True):
        currency_code = expense.currency_code or 'USD'
        shares = list(expense.shares)
        split_count = len(shares) or max(len(group.members), 1)
        split_amount = sum(share.amount_owed for share in shares) / split_count if shares else expense.amount / split_count

        for share in shares:
            balances[share.user_id][currency_code] -= share.amount_owed

        balances[expense.paid_by][currency_code] += expense.amount

        payer = member_users.get(expense.paid_by)
        expense_feed.append({
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'currency_code': currency_code,
            'split_amount': split_amount,
            'split_method': _split_method_label(getattr(expense, 'split_method', 'equal')),
            'paid_by_name': _member_display_name(payer),
            'created_at': expense.created_at,
        })

    member_balance_rows = []
    currency_totals = defaultdict(float)

    for user_id, user in member_users.items():
        per_currency = dict(sorted(balances[user_id].items()))
        for currency_code, value in per_currency.items():
            currency_totals[currency_code] += value

        member_balance_rows.append({
            'user': user,
            'balances': per_currency,
        })

    settlement_suggestions = []
    for currency_code in sorted({code for row in member_balance_rows for code in row['balances']}):
        creditors = []
        debtors = []

        for row in member_balance_rows:
            balance_value = row['balances'].get(currency_code, 0)
            if balance_value > 0:
                creditors.append({'username': _member_display_name(row['user']), 'amount': balance_value})
            elif balance_value < 0:
                debtors.append({'username': _member_display_name(row['user']), 'amount': -balance_value})

        creditors.sort(key=lambda item: item['amount'], reverse=True)
        debtors.sort(key=lambda item: item['amount'], reverse=True)

        creditor_idx = 0
        debtor_idx = 0
        while creditor_idx < len(creditors) and debtor_idx < len(debtors):
            transfer_amount = min(creditors[creditor_idx]['amount'], debtors[debtor_idx]['amount'])
            settlement_suggestions.append({
                'currency_code': currency_code,
                'from_user': debtors[debtor_idx]['username'],
                'to_user': creditors[creditor_idx]['username'],
                'amount': round(transfer_amount, 2),
            })

            creditors[creditor_idx]['amount'] -= transfer_amount
            debtors[debtor_idx]['amount'] -= transfer_amount

            if creditors[creditor_idx]['amount'] <= 0.009:
                creditor_idx += 1
            if debtors[debtor_idx]['amount'] <= 0.009:
                debtor_idx += 1

    return {
        'member_users': member_users,
        'member_balance_rows': member_balance_rows,
        'expense_feed': expense_feed,
        'settlement_suggestions': settlement_suggestions,
        'currency_symbols': CURRENCY_SYMBOLS,
    }


# -------------------- Helper: Save Profile Picture --------------------
def save_picture(form_picture):
    cloudinary_ready = (
        cloudinary is not None
        and (
            os.environ.get('CLOUDINARY_URL')
            or (
                os.environ.get('CLOUDINARY_CLOUD_NAME')
                and os.environ.get('CLOUDINARY_API_KEY')
                and os.environ.get('CLOUDINARY_API_SECRET')
            )
        )
    )

    if cloudinary_ready:
        upload_result = cloudinary.uploader.upload(
            form_picture,
            folder='budget-tracker/profile_pics',
            resource_type='image',
        )
        return upload_result.get('secure_url')

    if os.environ.get('VERCEL'):
        return None

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (150, 150)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn


# -------------------- Home --------------------
@main.route('/')
def home():
    return redirect(url_for('main.login'))


# -------------------- Register --------------------
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        picture_file = save_picture(form.profile_picture.data) if form.profile_picture.data else None
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            profile_picture=picture_file
        )
        db.session.add(new_user)
        try:
            db.session.flush()
            db.session.add(UserProfile(user_id=new_user.id, currency='INR'))
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('That username or email is already in use. Try a different one or sign in instead.', 'danger')
    return render_template('register.html', form=form)


# -------------------- Login --------------------
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


# -------------------- Logout --------------------
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


# -------------------- Toggle Dark Mode --------------------
@main.route('/toggle_dark_mode')
@login_required
def toggle_dark_mode():
    from .services.dark_mode import toggle_dark_mode as toggle_dark
    toggle_dark()
    return redirect(request.referrer or url_for('main.dashboard'))


# -------------------- Dashboard --------------------
@main.route('/dashboard')
@login_required
def dashboard():
    incomes = Income.query.filter_by(user_id=current_user.id).all()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    income_totals = _sum_amounts_by_currency(incomes)
    expense_totals = _sum_amounts_by_currency(expenses)
    balance_totals = {}
    for currency_code in set(income_totals) | set(expense_totals):
        balance_totals[currency_code] = income_totals.get(currency_code, 0) - expense_totals.get(currency_code, 0)

    active_groups = Group.query.join(GroupMember).filter(GroupMember.user_id == current_user.id).count()
    recent_transactions = _recent_transactions(incomes, expenses)
    chart_data = _build_dashboard_charts(incomes, expenses)
    preferred_currency = _preferred_currency(current_user)
    savings_rate = 0
    preferred_income = income_totals.get(preferred_currency, 0)
    preferred_expense = expense_totals.get(preferred_currency, 0)
    if preferred_income:
        savings_rate = round(max(preferred_income - preferred_expense, 0) / preferred_income * 100, 1)

    return render_template(
        'dashboard.html',
        income_totals=income_totals,
        expense_totals=expense_totals,
        balance_totals=balance_totals,
        preferred_currency=preferred_currency,
        savings_rate=savings_rate,
        active_groups=active_groups,
        recent_transactions=recent_transactions,
        chart_data=chart_data,
        currency_symbols=CURRENCY_SYMBOLS,
    )


@main.route('/income')
@login_required
def income_ledger():
    incomes = Income.query.filter_by(user_id=current_user.id).all()
    income_totals = _sum_amounts_by_currency(incomes)
    return render_template(
        'income_ledger.html',
        incomes=sorted(incomes, key=lambda item: item.date or date.min, reverse=True),
        income_totals=income_totals,
        currency_symbols=CURRENCY_SYMBOLS,
    )


@main.route('/expenses')
@login_required
def expense_ledger():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    expense_totals = _sum_amounts_by_currency(expenses)
    return render_template(
        'expense_ledger.html',
        expenses=sorted(expenses, key=lambda item: item.date or datetime.min, reverse=True),
        expense_totals=expense_totals,
        currency_symbols=CURRENCY_SYMBOLS,
    )


# -------------------- Add Income --------------------
@main.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    form = IncomeForm()
    form.currency_code.data = form.currency_code.data or _preferred_currency(current_user)
    if form.validate_on_submit():
        income = Income(
            amount=form.amount.data,
            source=form.source.data,
            currency_code=form.currency_code.data,
            description=form.description.data,
            date=form.date.data,
            is_recurring=form.is_recurring.data,
            frequency=form.frequency.data,
            user_id=current_user.id
        )
        db.session.add(income)
        db.session.commit()
        flash('Income added successfully!', 'success')
        return redirect(url_for('main.income_ledger'))
    return render_template('add_income.html', form=form)


# -------------------- Add Expense --------------------
@main.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    form.currency_code.data = form.currency_code.data or _preferred_currency(current_user)
    if form.validate_on_submit():
        # Use ML to predict category if description provided and category is empty
        if form.description.data and not form.category.data:
            from .ml_utils import predict_category
            predicted_category = predict_category(form.description.data)
            category = predicted_category if predicted_category else "Other"
        elif not form.category.data:
            category = "Other"
        else:
            category = form.category.data
        
        expense = Expense(
            amount=form.amount.data,
            category=category,
            currency_code=form.currency_code.data,
            description=form.description.data,
            date=form.date.data or datetime.utcnow().date(),
            is_recurring=form.is_recurring.data,
            frequency=form.frequency.data if form.is_recurring.data else 'none',
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added!', 'success')
        return redirect(url_for('main.expense_ledger'))
    return render_template('add_expense.html', form=form)


# -------------------- Edit Expense --------------------
@main.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        flash('You do not have permission to edit this expense.', 'danger')
        return redirect(url_for('main.expense_ledger'))
    
    form = ExpenseForm(obj=expense)
    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.currency_code = form.currency_code.data
        # Use ML to predict category if description provided and category is empty
        if form.description.data and not form.category.data:
            from .ml_utils import predict_category
            predicted_category = predict_category(form.description.data)
            expense.category = predicted_category if predicted_category else "Other"
        elif not form.category.data:
            expense.category = "Other"
        else:
            expense.category = form.category.data
        expense.description = form.description.data
        expense.date = form.date.data or datetime.utcnow().date()
        expense.is_recurring = form.is_recurring.data
        expense.frequency = form.frequency.data if form.is_recurring.data else 'none'
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('main.expense_ledger'))
    return render_template('add_expense.html', form=form, expense=expense, is_edit=True)


# -------------------- Delete Expense --------------------
@main.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        flash('You do not have permission to delete this expense.', 'danger')
        return redirect(url_for('main.expense_ledger'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('main.expense_ledger'))


# -------------------- Edit Income --------------------
@main.route('/edit_income/<int:income_id>', methods=['GET', 'POST'])
@login_required
def edit_income(income_id):
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user.id:
        flash('You do not have permission to edit this income.', 'danger')
        return redirect(url_for('main.income_ledger'))
    
    form = IncomeForm(obj=income)
    if form.validate_on_submit():
        income.amount = form.amount.data
        income.source = form.source.data
        income.currency_code = form.currency_code.data
        income.description = form.description.data
        income.date = form.date.data
        income.is_recurring = form.is_recurring.data
        income.frequency = form.frequency.data if form.is_recurring.data else 'none'
        db.session.commit()
        flash('Income updated successfully!', 'success')
        return redirect(url_for('main.income_ledger'))
    return render_template('add_income.html', form=form, income=income, is_edit=True)


# -------------------- Delete Income --------------------
@main.route('/delete_income/<int:income_id>', methods=['POST'])
@login_required
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user.id:
        flash('You do not have permission to delete this income.', 'danger')
        return redirect(url_for('main.income_ledger'))
    
    db.session.delete(income)
    db.session.commit()
    flash('Income deleted successfully!', 'success')
    return redirect(url_for('main.income_ledger'))


# -------------------- Profile --------------------
@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()

    if current_user.profile and current_user.profile.currency == 'USD':
        current_user.profile.currency = 'INR'
        db.session.commit()

    # Pre-fill current user data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.preferred_currency.data = _preferred_currency(current_user)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if not current_user.profile:
            db.session.add(UserProfile(user_id=current_user.id, currency=form.preferred_currency.data))
            db.session.flush()
        else:
            current_user.profile.currency = form.preferred_currency.data

        # Update password only if provided
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)

        if form.profile_picture.data:
            picture_file = save_picture(form.profile_picture.data)
            if picture_file:
                current_user.profile_picture = picture_file
            else:
                flash('Profile image upload is not configured yet. Add Cloudinary credentials in production to enable it.', 'warning')

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('profile.html', form=form, user=current_user)


# -------------------- Graph --------------------
@main.route('/graph')
@login_required
def graph():
    # Retrieve the income and expense data from the database
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    # Process the data to get categories and amounts
    categories = [f"{expense.category} ({expense.currency_code or 'USD'})" for expense in expenses]
    amounts = [expense.amount for expense in expenses]

    # Calculate additional insights
    total_income = sum(i.amount for i in Income.query.filter_by(user_id=current_user.id).all())
    total_expense = sum(e.amount for e in expenses)
    
    # Handle empty categories list
    if categories:
        category_counts = Counter(categories)
        top_category = category_counts.most_common(1)[0][0] if category_counts else "N/A"
    else:
        top_category = "N/A"

    return render_template('graph.html', categories=categories, amounts=amounts,
                           total_income=total_income, total_expense=total_expense, top_category=top_category,
                           currency_symbols=CURRENCY_SYMBOLS)


# -------------------- Export --------------------
@main.route('/export', methods=['GET', 'POST'])
@login_required
def export():
    form = ExportForm()
    if form.validate_on_submit():
        export_format = form.export_format.data
        start_date = form.start_date.data
        end_date = form.end_date.data

        # Get actual user data
        expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all()
        
        incomes = Income.query.filter(
            Income.user_id == current_user.id,
            Income.date >= start_date,
            Income.date <= end_date
        ).all()

        # Prepare data for export
        data = []
        for expense in expenses:
            data.append({
                'type': 'Expense',
                'category': expense.category,
                'description': expense.description or '',
                'amount': expense.amount,
                'currency_code': expense.currency_code or 'USD',
                'date': expense.date.strftime('%Y-%m-%d') if isinstance(expense.date, datetime) else str(expense.date)
            })
        
        for income in incomes:
            data.append({
                'type': 'Income',
                'category': income.source,
                'description': income.description or '',
                'amount': income.amount,
                'currency_code': income.currency_code or 'USD',
                'date': income.date.strftime('%Y-%m-%d') if isinstance(income.date, date) else str(income.date)
            })

        if export_format == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['type', 'category', 'description', 'amount', 'currency_code', 'date'])
            writer.writeheader()
            writer.writerows(data)
            csv_data = output.getvalue().encode('utf-8')
            return Response(csv_data, mimetype='text/csv',
                            headers={"Content-Disposition": f"attachment;filename=financial_data_{start_date}_to_{end_date}.csv"})

        elif export_format == 'pdf':
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.drawString(100, 750, f"Financial Data Export - {start_date} to {end_date}")
            c.drawString(100, 730, f"User: {current_user.username}")
            y = 710
            for entry in data:
                if y < 50:  # New page if needed
                    c.showPage()
                    y = 750
                c.drawString(100, y, f"{entry['type']}: {entry['category']} - {entry['description']} - {entry['currency_code']} {entry['amount']} - {entry['date']}")
                y -= 20
            c.showPage()
            c.save()
            buffer.seek(0)
            return Response(buffer.getvalue(), mimetype='application/pdf',
                            headers={"Content-Disposition": f"attachment;filename=financial_data_{start_date}_to_{end_date}.pdf"})

        flash('Data exported successfully!', 'success')
        return redirect(url_for('main.export'))

    return render_template('export.html', form=form)


# -------------------- Create Group --------------------
@main.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = CreateGroupForm()
    if form.validate_on_submit():
        group_name = form.name.data
        new_group = Group(name=group_name, created_by=current_user.id)  # Use 'created_by' here
        db.session.add(new_group)
        db.session.flush()
        db.session.add(GroupMember(group_id=new_group.id, user_id=current_user.id))
        db.session.commit()
        flash(f'Group "{group_name}" created successfully!', 'success')
        return redirect(url_for('main.view_group', group_id=new_group.id))
    return render_template('create_group.html', form=form)



# -------------------- Add Member --------------------
@main.route('/group/<int:group_id>/add_member', methods=['GET', 'POST'])
@login_required
def add_member(group_id):
    member_name = (request.form.get('member_name') or '').strip()
    group = Group.query.get(group_id)

    if not group:
        flash("Group not found.", "danger")
        return redirect(url_for('main.dashboard'))

    if group.created_by != current_user.id:
        flash("Only the group owner can add members.", "danger")
        return redirect(url_for('main.view_group', group_id=group_id))

    if not member_name:
        flash("Enter a member name to continue.", "danger")
        return redirect(url_for('main.group_detail', group_id=group_id))

    user = User.query.filter_by(username=member_name, is_guest=False).first()

    if not user:
        safe_token = secrets.token_urlsafe(16)
        guest_stub = safe_token[:12]
        user = User(
            username=f'guest_{guest_stub}',
            email=f'guest_{guest_stub}@budgettracker.local',
            name=member_name,
            password=generate_password_hash(secrets.token_urlsafe(24)),
            is_guest=True,
            invite_token=safe_token,
        )
        db.session.add(user)
        db.session.flush()

    # Check if already a member
    existing = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if existing:
        flash("That member is already part of this group.", "warning")
        return redirect(url_for('main.group_detail', group_id=group_id))

    # Safely create and add member
    new_member = GroupMember(group_id=group.id, user_id=user.id)
    db.session.add(new_member)
    db.session.commit()
    if user.is_guest:
        flash(f"{member_name} added as a guest member. Share the invite link from the group page if they want to join later.", "success")
    else:
        flash(f"{member_name} added to the group.", "success")
    return redirect(url_for('main.group_detail', group_id=group_id))



@main.route('/group/<int:group_id>', methods=['GET'])
@login_required
def group_detail(group_id):
    group = Group.query.get(group_id)

    if not group:
        flash("Group not found.", "danger")
        return redirect(url_for('main.dashboard'))

    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not is_member and group.created_by != current_user.id:
        flash('You do not have access to manage this group.', 'danger')
        return redirect(url_for('main.view_groups'))

    member_users = {}
    for member in group.members:
        user = User.query.get(member.user_id)
        if user:
            member_users[member.user_id] = user

    invite_links = {
        user_id: url_for('main.claim_invite', token=user.invite_token, _external=True)
        for user_id, user in member_users.items()
        if user.is_guest and user.invite_token
    }

    return render_template(
        'group_detail.html',
        group=group,
        member_users=member_users,
        invite_links=invite_links,
        currency_symbols=CURRENCY_SYMBOLS,
        member_display_name=_member_display_name,
        member_meta=_member_meta,
    )


# -------------------- View Groups --------------------
@main.route('/groups')
@login_required
def view_groups():
    # Get all groups where user is a member
    user_groups = Group.query.join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    # Also include groups created by user
    created_groups = Group.query.filter_by(created_by=current_user.id).all()
    all_groups = list({group.id: group for group in user_groups + created_groups}.values())
    group_cards = []
    for group in all_groups:
        snapshot = _build_group_snapshot(group)
        group_cards.append({
            'group': group,
            'member_count': len(snapshot['member_users']),
            'expense_count': len(group.expenses),
            'currencies': sorted({expense.currency_code or 'USD' for expense in group.expenses}),
        })
    return render_template('view_groups.html', group_cards=group_cards, currency_symbols=CURRENCY_SYMBOLS)


# -------------------- View Group --------------------
@main.route('/view_group/<int:group_id>')
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    # Check if user is a member
    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not is_member and group.created_by != current_user.id:
        flash('You do not have access to this group.', 'danger')
        return redirect(url_for('main.view_groups'))
    
    snapshot = _build_group_snapshot(group)

    return render_template(
        'view_group.html',
        group=group,
        members=group.members,
        member_balance_rows=snapshot['member_balance_rows'],
        member_users=snapshot['member_users'],
        expense_feed=snapshot['expense_feed'],
        settlement_suggestions=snapshot['settlement_suggestions'],
        currency_symbols=CURRENCY_SYMBOLS,
        member_display_name=_member_display_name,
        member_meta=_member_meta,
    )


# -------------------- Add Shared Expense --------------------
@main.route('/add_shared_expense/<int:group_id>', methods=['GET', 'POST'])
@login_required
def add_shared_expense(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member of the group
    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not is_member and group.created_by != current_user.id:
        flash('You must be a member of this group to add expenses.', 'danger')
        return redirect(url_for('main.view_group', group_id=group_id))
    
    form = AddSharedExpenseForm()
    form.currency_code.data = form.currency_code.data or _preferred_currency(current_user)
    form.split_method.data = form.split_method.data or 'equal'
    member_users = [User.query.get(member.user_id) for member in group.members if User.query.get(member.user_id)]
    form.paid_by.choices = [(user.id, _member_display_name(user)) for user in member_users]

    if form.validate_on_submit():
        description = form.description.data
        amount = form.amount.data
        paid_by_id = form.paid_by.data
        currency_code = form.currency_code.data
        split_method = form.split_method.data
        split_map, error_message = _parse_split_amounts(group, amount, split_method)
        if error_message:
            flash(error_message, 'danger')
            return render_template('add_shared_expense.html', form=form, group=group, member_users=member_users, member_display_name=_member_display_name)

        expense = SharedExpense(
            description=description,
            amount=amount,
            currency_code=currency_code,
            split_method=split_method,
            group_id=group.id,
            paid_by=paid_by_id
        )
        db.session.add(expense)
        db.session.flush()

        for member in group.members:
            if member.user_id not in split_map:
                continue
            share = ExpenseShare(
                expense_id=expense.id,
                user_id=member.user_id,
                amount_owed=split_map[member.user_id]
            )
            db.session.add(share)

        db.session.commit()
        flash('Shared expense added successfully!', 'success')
        return redirect(url_for('main.view_group', group_id=group.id))

    return render_template(
        'add_shared_expense.html',
        form=form,
        group=group,
        member_users=member_users,
        member_display_name=_member_display_name,
    )


@main.route('/invite/<token>')
@login_required
def claim_invite(token):
    guest_user = User.query.filter_by(invite_token=token, is_guest=True).first()

    if not guest_user:
        flash('This invite link is invalid or has already been claimed.', 'warning')
        return redirect(url_for('main.view_groups'))

    guest_memberships = GroupMember.query.filter_by(user_id=guest_user.id).all()
    for membership in guest_memberships:
        existing_membership = GroupMember.query.filter_by(group_id=membership.group_id, user_id=current_user.id).first()
        if existing_membership:
            db.session.delete(membership)
        else:
            membership.user_id = current_user.id

    for expense in SharedExpense.query.filter_by(paid_by=guest_user.id).all():
        expense.paid_by = current_user.id

    guest_shares = ExpenseShare.query.filter_by(user_id=guest_user.id).all()
    for share in guest_shares:
        existing_share = ExpenseShare.query.filter_by(expense_id=share.expense_id, user_id=current_user.id).first()
        if existing_share:
            existing_share.amount_owed += share.amount_owed
            db.session.delete(share)
        else:
            share.user_id = current_user.id

    db.session.flush()
    db.session.delete(guest_user)
    db.session.commit()
    flash('Invite claimed successfully. Your account is now connected to those shared balances.', 'success')
    return redirect(url_for('main.view_groups'))
