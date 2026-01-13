# routes.py
# Define application routes for the enhanced Budget Tracker app with profile picture upload

import os
import secrets
import csv
from datetime import datetime, date
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
from .models import User, Income, Expense, UserProfile, Group, SharedExpense, GroupMember, ExpenseShare
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
            description=form.description.data,
            date=form.date.data or datetime.utcnow().date(),
            is_recurring=form.is_recurring.data,
            frequency=form.frequency.data if form.is_recurring.data else 'none',
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_expense.html', form=form)


# -------------------- Edit Expense --------------------
@main.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        flash('You do not have permission to edit this expense.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = ExpenseForm(obj=expense)
    if form.validate_on_submit():
        expense.amount = form.amount.data
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
        return redirect(url_for('main.dashboard'))
    return render_template('add_expense.html', form=form, expense=expense, is_edit=True)


# -------------------- Delete Expense --------------------
@main.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        flash('You do not have permission to delete this expense.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))


# -------------------- Edit Income --------------------
@main.route('/edit_income/<int:income_id>', methods=['GET', 'POST'])
@login_required
def edit_income(income_id):
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user.id:
        flash('You do not have permission to edit this income.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = IncomeForm(obj=income)
    if form.validate_on_submit():
        income.amount = form.amount.data
        income.source = form.source.data
        income.description = form.description.data
        income.date = form.date.data
        income.is_recurring = form.is_recurring.data
        income.frequency = form.frequency.data if form.is_recurring.data else 'none'
        db.session.commit()
        flash('Income updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_income.html', form=form, income=income, is_edit=True)


# -------------------- Delete Income --------------------
@main.route('/delete_income/<int:income_id>', methods=['POST'])
@login_required
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)
    if income.user_id != current_user.id:
        flash('You do not have permission to delete this income.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(income)
    db.session.commit()
    flash('Income deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))


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

        # Update password only if provided
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)

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
    
    # Handle empty categories list
    if categories:
        from collections import Counter
        category_counts = Counter(categories)
        top_category = category_counts.most_common(1)[0][0] if category_counts else "N/A"
    else:
        top_category = "N/A"

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
                'date': expense.date.strftime('%Y-%m-%d') if isinstance(expense.date, datetime) else str(expense.date)
            })
        
        for income in incomes:
            data.append({
                'type': 'Income',
                'category': income.source,
                'description': income.description or '',
                'amount': income.amount,
                'date': income.date.strftime('%Y-%m-%d') if isinstance(income.date, date) else str(income.date)
            })

        if export_format == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['type', 'category', 'description', 'amount', 'date'])
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
                c.drawString(100, y, f"{entry['type']}: {entry['category']} - {entry['description']} - ${entry['amount']} - {entry['date']}")
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


# -------------------- View Groups --------------------
@main.route('/groups')
@login_required
def view_groups():
    # Get all groups where user is a member
    user_groups = Group.query.join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    # Also include groups created by user
    created_groups = Group.query.filter_by(created_by=current_user.id).all()
    all_groups = list(set(user_groups + created_groups))
    return render_template('view_groups.html', groups=all_groups)


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
    
    # Calculate balances for each member and get user objects
    member_balances = {}
    member_users = {}
    for member in group.members:
        user = User.query.get(member.user_id)
        if user:
            member_users[member.user_id] = user
            total_owed = sum(share.amount_owed for expense in group.expenses for share in expense.shares if share.user_id == user.id)
            total_paid = sum(expense.amount for expense in group.expenses if expense.paid_by == user.id)
            member_balances[user.id] = {
                'username': user.username,
                'owed': total_owed,
                'paid': total_paid,
                'balance': total_paid - total_owed
            }
    
    # Get user objects for expenses
    expense_users = {}
    for expense in group.expenses:
        payer = User.query.get(expense.paid_by)
        if payer:
            expense_users[expense.id] = payer
    
    return render_template('view_group.html', group=group, members=group.members, member_balances=member_balances, member_users=member_users, expense_users=expense_users)


# -------------------- Add Shared Expense --------------------
@main.route('/add_shared_expense/<int:group_id>', methods=['GET', 'POST'])
@login_required
def add_shared_expense(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member of the group
    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not is_member:
        flash('You must be a member of this group to add expenses.', 'danger')
        return redirect(url_for('main.view_group', group_id=group_id))
    
    form = AddSharedExpenseForm()
    # Get actual user objects from group members
    member_users = [User.query.get(member.user_id) for member in group.members if User.query.get(member.user_id)]
    form.paid_by.choices = [(user.id, user.username) for user in member_users]

    if form.validate_on_submit():
        description = form.description.data
        amount = form.amount.data
        paid_by_id = form.paid_by.data

        expense = SharedExpense(description=description, amount=amount, group_id=group.id, paid_by=paid_by_id)
        db.session.add(expense)
        db.session.flush()  # Get the expense ID

        # Calculate share per member
        total_members = len(group.members)
        if total_members == 0:
            flash('Group has no members.', 'danger')
            return redirect(url_for('main.view_group', group_id=group_id))
        
        share_per_person = amount / total_members

        # Create ExpenseShare records for each member
        for member in group.members:
            share = ExpenseShare(
                expense_id=expense.id,
                user_id=member.user_id,
                amount_owed=share_per_person
            )
            db.session.add(share)

        db.session.commit()
        flash('Shared expense added successfully!', 'success')
        return redirect(url_for('main.view_group', group_id=group.id))

    return render_template('add_shared_expense.html', form=form, group=group)
