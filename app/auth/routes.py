from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.models import User, LoginAttempt
from app.auth.forms import RegistrationForm, LoginForm
from datetime import datetime, timedelta
import re

def is_strong_password(password):
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def check_login_attempts(username, ip_address):
    """Check if user is banned from login attempts"""
    # Clean old attempts
    LoginAttempt.query.filter(
        LoginAttempt.timestamp < datetime.utcnow() - timedelta(minutes=15)
    ).delete()
    db.session.commit()
    
    # Count recent failed attempts
    recent_attempts = LoginAttempt.query.filter(
        LoginAttempt.username == username,
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(minutes=15)
    ).count()
    
    if recent_attempts >= 5:
        return True, "Demasiados intentos fallidos. Por favor espera 15 minutos."
    
    # Count recent failed attempts by IP
    ip_attempts = LoginAttempt.query.filter(
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(minutes=15)
    ).count()
    
    if ip_attempts >= 10:  # More attempts allowed for IP to prevent easy DoS
        return True, "Demasiados intentos fallidos desde esta IP. Por favor espera 15 minutos."
    
    return False, None

def record_failed_attempt(username, ip_address):
    """Record a failed login attempt"""
    attempt = LoginAttempt(
        username=username,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('judge.dashboard' if current_user.is_judge else 'participant.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        
        # Check for too many failed attempts
        is_banned, message = check_login_attempts(username, request.remote_addr)
        if is_banned:
            flash(message, 'danger')
            return render_template('auth/login.html', form=form)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Tu cuenta ha sido desactivada. Por favor contacta soporte.', 'danger')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember.data)
            user.update_login_info()
            
            # Store login timestamp and IP in session
            session['last_activity'] = datetime.utcnow().isoformat()
            session['login_ip'] = request.remote_addr
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('judge.dashboard' if user.is_judge else 'participant.dashboard')
            return redirect(next_page)
        
        # Record failed attempt
        record_failed_attempt(username, request.remote_addr)
        flash('Usuario o contraseña inválidos', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp.route('/judges/login', methods=['GET', 'POST'])
def judge_login():
    if current_user.is_authenticated:
        return redirect(url_for('judge.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Por favor ingresa usuario y contraseña', 'danger')
            return render_template('auth/judge_login.html')
        
        # Check for too many failed attempts
        is_banned, message = check_login_attempts(username, request.remote_addr)
        if is_banned:
            flash(message, 'danger')
            return render_template('auth/judge_login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_judge:
            if not user.is_active:
                flash('Tu cuenta ha sido desactivada. Por favor contacta soporte.', 'danger')
                return render_template('auth/judge_login.html')
            
            login_user(user, remember=remember)
            user.update_login_info()
            
            # Store login timestamp and IP in session
            session['last_activity'] = datetime.utcnow().isoformat()
            session['login_ip'] = request.remote_addr
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('judge.dashboard')
            return redirect(next_page)
        
        # Record failed attempt
        record_failed_attempt(username, request.remote_addr)
        flash('Usuario o contraseña inválidos', 'danger')
    return render_template('auth/judge_login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('participant.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, is_judge=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('¡Registro exitoso! Por favor inicia sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/judges/register', methods=['GET', 'POST'])
def judge_register():
    if current_user.is_authenticated:
        return redirect(url_for('judge.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        access_code = request.form.get('access_code')
        
        if not username or not password or not confirm_password or not access_code:
            flash('Por favor completa todos los campos', 'danger')
            return render_template('auth/judge_register.html')
        
        if len(username) < 3:
            flash('El nombre de usuario debe tener al menos 3 caracteres', 'danger')
            return render_template('auth/judge_register.html')
        
        if not is_strong_password(password):
            flash('La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial', 'danger')
            return render_template('auth/judge_register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/judge_register.html')
        
        if access_code != current_app.config['JUDGE_ACCESS_CODE']:
            flash('Código de acceso inválido', 'danger')
            return render_template('auth/judge_register.html')
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'danger')
            return render_template('auth/judge_register.html')
        
        user = User(username=username, is_judge=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('¡Registro exitoso! Por favor inicia sesión.', 'success')
        return redirect(url_for('auth.judge_login'))
    return render_template('auth/judge_register.html')

@bp.route('/logout')
@login_required
def logout():
    # Store user type for flash message
    user_type = "juez" if current_user.is_judge else "participante"
    
    # Clear all session data
    session.clear()
    
    # Clear remember me cookie if it exists
    if 'remember_token' in session:
        session.pop('remember_token', None)
    
    # Clear last activity timestamp
    if 'last_activity' in session:
        session.pop('last_activity', None)
    
    # Clear any other session variables
    for key in list(session.keys()):
        session.pop(key, None)
    
    # Logout the user
    logout_user()
    
    # Flash success message with user type
    flash(f'Has cerrado sesión exitosamente como {user_type}', 'success')
    
    # Redirect to home page
    return redirect(url_for('main.index'))

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'danger')
        return redirect(url_for('participant.dashboard' if not current_user.is_judge else 'judge.dashboard'))
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('participant.dashboard' if not current_user.is_judge else 'judge.dashboard'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('participant.dashboard' if not current_user.is_judge else 'judge.dashboard'))
    
    if not is_strong_password(new_password):
        flash('Password must be at least 8 characters long and contain uppercase, lowercase, number and special character', 'danger')
        return redirect(url_for('participant.dashboard' if not current_user.is_judge else 'judge.dashboard'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('participant.dashboard' if not current_user.is_judge else 'judge.dashboard')) 