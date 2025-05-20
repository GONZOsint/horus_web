import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'  # Only use secure cookies in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protect against CSRF
    
    # Judge access code
    JUDGE_ACCESS_CODE = 'JUDGE2024'
    
    # Security config
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  # How long to remember logged in users
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'  # Only use secure cookies in production
    REMEMBER_COOKIE_HTTPONLY = True  # Prevent JavaScript access to remember cookie
    REMEMBER_COOKIE_SAMESITE = 'Lax'  # Protect against CSRF

    # File upload config
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'case_photos')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 