# app/forms.py
# This file defines all web forms using Flask-WTF

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, BooleanField, SelectField, TextAreaField, DateField, FileField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Optional, NumberRange
from flask_wtf.file import FileAllowed
from flask_login import current_user


# -------------------- Profile Update Form --------------------
class ProfileForm(FlaskForm):
    """
    Form for updating the user's profile information.
    Includes username, email, password, profile picture, and other necessary fields.
    """
    # Username field (required)
    username = StringField('Username', validators=[DataRequired()])

    # Email field (required, must be in email format)
    email = StringField('Email', validators=[DataRequired(), Email()])

    # Password field (required)
    password = PasswordField('Password', validators=[DataRequired()])

    # Confirm password field (required and must match password)
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    # Profile picture field (optional, allows image uploads)
    profile_picture = FileField('Profile Picture', validators=[
        Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])

    # Submit button for the form
    submit = SubmitField('Update')


# -------------------- User Registration Form --------------------
class RegistrationForm(FlaskForm):
    """
    Form used to register a new user.
    Includes username, email, password, confirm password, and profile picture.
    """
    # Username field (required, must be between 2 and 150 characters)
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])

    # Email field (required, must be in email format)
    email = StringField('Email', validators=[DataRequired(), Email()])

    # Password field (required, must be at least 6 characters long)
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

    # Confirm password field (required and must match password)
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    # Profile picture field (optional, allows image uploads)
    profile_picture = FileField('Upload Profile Picture (JPG/PNG)', validators=[
        Optional(), FileAllowed(['jpg', 'png'], 'Images only!')
    ])

    # Submit button for the form
    submit = SubmitField('Register')


# -------------------- User Login Form --------------------
class LoginForm(FlaskForm):
    """
    Form used for user login.
    Includes username and password fields.
    """
    # Username field (required, must be between 2 and 150 characters)
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])

    # Password field (required)
    password = PasswordField('Password', validators=[DataRequired()])

    # Submit button for the form
    submit = SubmitField('Login')


# -------------------- Income Entry Form --------------------
class IncomeForm(FlaskForm):
    """
    Form for adding new income records.
    Includes amount, source, description, date, and frequency details.
    """
    # Amount field (required, should be a float)
    amount = FloatField('Amount', validators=[DataRequired()])

    # Source field (required, should be a string)
    source = StringField('Source', validators=[DataRequired()])

    # Description field (optional)
    description = StringField('Description')

    # Date field (required)
    date = DateField('Date', validators=[DataRequired()])

    # Recurring field (optional, for recurring incomes)
    is_recurring = BooleanField('Recurring?')

    # Frequency field (optional, to set recurrence frequency)
    frequency = SelectField('Frequency', choices=[
        ('none', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')
    ])

    # Submit button for the form
    submit = SubmitField('Add Income')


# -------------------- Expense Entry Form --------------------
class ExpenseForm(FlaskForm):
    """
    Form for adding new expense records.
    Includes amount, category, description, date, and frequency details.
    """
    # Amount field (required, should be a float)
    amount = FloatField('Amount', validators=[DataRequired()])

    # Category field (required, should be a string)
    category = StringField('Category', validators=[DataRequired()])

    # Description field (optional)
    description = TextAreaField('Description', validators=[Optional()])

    # Date field (optional)
    date = DateField('Date', validators=[Optional()])

    # Recurring field (optional, for recurring expenses)
    is_recurring = BooleanField('Recurring?')

    # Frequency field (optional, to set recurrence frequency)
    frequency = SelectField(
        'Frequency',
        choices=[('', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        validators=[Optional()]
    )

    # Submit button for the form
    submit = SubmitField('Add Expense')


# -------------------- Export Form --------------------
class ExportForm(FlaskForm):
    """
    Form to select export format (CSV or PDF) and date range.
    """
    # Export format field (required, options: CSV or PDF)
    export_format = SelectField('Export Format', choices=[('csv', 'CSV'), ('pdf', 'PDF')], validators=[DataRequired()])

    # Start date field (required)
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])

    # End date field (required)
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])

    # Submit button for the form
    submit = SubmitField('Export')


# -------------------- Group Management Forms --------------------

class CreateGroupForm(FlaskForm):
    """
    Form to create a new group.
    Includes group name.
    """
    # Group name field (required, should be between 2 and 100 characters)
    name = StringField('Group Name', validators=[DataRequired(), Length(min=2, max=100)])

    # Submit button for the form
    submit = SubmitField('Create Group')


class AddMemberForm(FlaskForm):
    """
    Form to add a member to an existing group.
    Includes username and group ID.
    """
    # Username field (required)
    username = StringField('Username', validators=[DataRequired()])

    # Hidden field to store the group ID being modified
    group_id = HiddenField()

    # Submit button for the form
    submit = SubmitField('Add Member')


class AddSharedExpenseForm(FlaskForm):
    """
    Form to add a shared expense to a group.
    Includes description, amount, and paid by fields.
    """
    # Description field (required)
    description = StringField('Description', validators=[DataRequired(), Length(min=1, max=255)])

    # Amount field (required, should be a float)
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])

    # Paid by field (required, selects the user who paid)
    paid_by = SelectField('Paid By', coerce=int, validators=[DataRequired()])

    # Hidden field to store the group ID context
    group_id = HiddenField()

    # Submit button for the form
    submit = SubmitField('Add Expense')

