# tests/test_forms.py

"""
Tests for form validation logic (LoginForm, RegistrationForm, etc.).
"""

from budget_app.forms import LoginForm, RegistrationForm

def test_login_form_valid():
    form = LoginForm(data={'username': 'testuser', 'password': 'secret'})
    assert form.validate()

def test_register_form_valid():
    form = RegistrationForm(data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'secret',
        'confirm_password': 'secret'
    })
    assert form.validate()
