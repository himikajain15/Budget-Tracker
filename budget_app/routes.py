# routes.py
# Define application routes for the enhanced Budget Tracker app with profile picture upload

import os
import secrets
import csv
from io import BytesIO, StringIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .forms import ProfileForm

from . import db
from .models import User, Income, Expense, UserProfile, Group, SharedExpense, GroupMember
from .forms import (
    RegistrationForm, LoginForm, IncomeForm, ExpenseForm,
    ProfileForm, ExportForm, CreateGroupForm, AddMemberForm, AddSharedExpenseForm
)

main = Blueprint('main', __name__, template_folder='templates')


# -------------------- Helper: Save Profile Picture --------------------
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (150, 150)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn

#@main.route('/')
#def index():
    #return render_template('index.html')


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
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('main.login'))
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


# -------------------- Dashboard --------------------
@main.route('/dashboard')
@login_required
def dashboard():
    incomes = Income.query.filter_by(user_id=current_user.id).all()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)
    balance = total_income - total_expense
    return render_template('dashboard.html', incomes=incomes, expenses=expenses,
                           total_income=total_income, total_expense=total_expense, balance=balance)


# -------------------- Add Income --------------------
@main.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    form = IncomeForm()
    if form.validate_on_submit():
        income = Income(
            amount=form.amount.data,
            source=form.source.data,
            description=form.description.data,
            date=form.date.data,
            is_recurring=form.is_recurring.data,
            frequency=form.frequency.data,
            user_id=current_user.id
        )
        db.session.add(income)
        db.session.commit()
        flash('Income added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_income.html', form=form)


# -------------------- Add Expense --------------------
@main.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data,
            date=form.date.data,
            is_recurring=form.is_recurring.data,
            frequency=form.frequency.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_expense.html', form=form)


# -------------------- Profile --------------------
@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()

    # Pre-fill current user data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.profile_picture.data:
            picture_file = save_picture(form.profile_picture.data)
            current_user.profile_picture = picture_file

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
    categories = [expense.category for expense in expenses]
    amounts = [expense.amount for expense in expenses]

    # Calculate additional insights
    total_income = sum(i.amount for i in Income.query.filter_by(user_id=current_user.id).all())
    total_expense = sum(e.amount for e in expenses)
    top_category = max(set(categories), key = categories.count)  # This will give the most frequent category

    return render_template('graph.html', categories=categories, amounts=amounts,
                           total_income=total_income, total_expense=total_expense, top_category=top_category)


# -------------------- Export --------------------
@main.route('/export', methods=['GET', 'POST'])
@login_required
def export():
    form = ExportForm()
    if form.validate_on_submit():
        export_format = form.export_format.data
        start_date = form.start_date.data
        end_date = form.end_date.data

        data = [
            {'category': 'Food', 'amount': 50.0, 'date': '2025-05-01'},
            {'category': 'Transport', 'amount': 20.0, 'date': '2025-05-02'},
        ]

        if export_format == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['category', 'amount', 'date'])
            writer.writeheader()
            writer.writerows(data)
            csv_data = output.getvalue().encode('utf-8')
            return Response(csv_data, mimetype='text/csv',
                            headers={"Content-Disposition": "attachment;filename=financial_data.csv"})

        elif export_format == 'pdf':
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.drawString(100, 750, f"Financial Data Export - {start_date} to {end_date}")
            y = 730
            for entry in data:
                c.drawString(100, y, f"Category: {entry['category']}, Amount: {entry['amount']}, Date: {entry['date']}")
                y -= 20
            c.showPage()
            c.save()
            buffer.seek(0)
            return Response(buffer.getvalue(), mimetype='application/pdf',
                            headers={"Content-Disposition": "attachment;filename=financial_data.pdf"})

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
        db.session.commit()
        flash(f'Group "{group_name}" created successfully!', 'success')
        return redirect(url_for('main.view_group', group_id=new_group.id))
    return render_template('create_group.html', form=form)



# -------------------- Add Member --------------------
@main.route('/group/<int:group_id>/add_member', methods=['GET', 'POST'])
@login_required
def add_member(group_id):
    member_username = request.form.get('username')
    group = Group.query.get(group_id)
    user = User.query.filter_by(username=member_username).first()

    if not group:
        flash("Group not found.", "danger")
        return redirect(url_for('main.dashboard'))

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('main.group_detail', group_id=group_id))

    # Check if already a member
    existing = GroupMember.query.filter_by(group_id=group_id, user_id=user.id).first()
    if existing:
        flash("User is already a member of this group.", "warning")
        return redirect(url_for('main.group_detail', group_id=group_id))

    # Safely create and add member
    new_member = GroupMember(group_id=group.id, user_id=user.id)
    db.session.add(new_member)
    db.session.commit()
    flash(f"{member_username} added to the group.", "success")
    return redirect(url_for('main.group_detail', group_id=group_id))



@main.route('/group/<int:group_id>', methods=['GET'])
@login_required
def group_detail(group_id):
    group = Group.query.get(group_id)

    if not group:
        flash("Group not found.", "danger")
        return redirect(url_for('main.dashboard'))

    return render_template('group_detail.html', group=group)


# -------------------- View Group --------------------
@main.route('/view_group/<int:group_id>')
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    return render_template('view_group.html', group=group, members=group.members)


# -------------------- Add Shared Expense --------------------
# -------------------- Add Shared Expense --------------------
@main.route('/add_shared_expense/<int:group_id>', methods=['GET', 'POST'])
@login_required
def add_shared_expense(group_id):
    group = Group.query.get_or_404(group_id)
    form = AddSharedExpenseForm()
    form.paid_by.choices = [(user.id, user.username) for user in group.members]

    if form.validate_on_submit():
        description = form.description.data
        amount = form.amount.data
        paid_by_id = form.paid_by.data

        expense = SharedExpense(description=description, amount=amount, group_id=group.id, paid_by_id=paid_by_id)
        db.session.add(expense)
        db.session.commit()

        total_members = len(group.members)
        share = amount / total_members

        for member in group.members:
            if member.id != paid_by_id:
                member.balance -= share
        User.query.get(paid_by_id).balance += amount

        db.session.commit()
        flash('Shared expense added successfully!', 'success')
        return redirect(url_for('main.view_group', group_id=group.id))

    return render_template('add_shared_expense.html', form=form, group=group)
