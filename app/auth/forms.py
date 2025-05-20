from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, message='Username must be at least 3 characters long')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists')

    def validate_password(self, password):
        if not any(c.isupper() for c in password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password.data):
            raise ValidationError('Password must contain at least one number')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password.data):
            raise ValidationError('Password must contain at least one special character') 