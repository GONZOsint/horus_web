from flask import Flask, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()
moment = Moment()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

def create_app(config_class=Config):
    app = Flask(__name__, 
                static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
                static_url_path='/static')
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)

    # Import models
    from app.models import User

    # Configure login manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_user_from_id(user_id)

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.participant import bp as participant_bp
    app.register_blueprint(participant_bp, url_prefix='/participant')

    from app.judge import bp as judge_bp
    app.register_blueprint(judge_bp, url_prefix='/judge')

    # Register template context processors
    @app.context_processor
    def inject_user():
        return {'current_user': current_user}

    # Register error handlers
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app 