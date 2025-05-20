from datetime import datetime, timedelta
from flask import session, redirect, url_for, flash
from functools import wraps

def check_session_timeout():
    """Check if the session has timed out"""
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        if datetime.utcnow() - last_activity > timedelta(minutes=30):
            session.clear()
            return True
    return False

def update_session_activity():
    """Update the last activity timestamp"""
    session['last_activity'] = datetime.utcnow().isoformat()

def session_activity_required(f):
    """Decorator to check session activity and update it"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if check_session_timeout():
            flash('Your session has expired. Please login again.')
            return redirect(url_for('auth.login'))
        update_session_activity()
        return f(*args, **kwargs)
    return decorated_function 