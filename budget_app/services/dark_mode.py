# dark_mode.py
# Handles theme switching logic for dark mode and light mode

from flask import session

def toggle_dark_mode():
    """
    Toggle the dark mode setting stored in the user's session.
    """
    current = session.get('dark_mode', False)
    session['dark_mode'] = not current

def is_dark_mode_enabled():
    """
    Check if dark mode is currently enabled.

    Returns:
        bool: True if dark mode is on, False otherwise.
    """
    return session.get('dark_mode', False)
