from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DateField, IntegerField, FloatField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class CaseForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Descripción', validators=[Optional()])
    disappearance_date = DateField('Fecha de Desaparición', validators=[Optional()], format='%Y-%m-%d')
    birth_date = DateField('Fecha de Nacimiento', validators=[Optional()], format='%Y-%m-%d')
    age_at_disappearance = IntegerField('Edad al Desaparecer', validators=[Optional(), NumberRange(min=0, max=120)])
    current_age = IntegerField('Edad Actual', validators=[Optional(), NumberRange(min=0, max=120)])
    disappearance_location = StringField('Lugar de Desaparición', validators=[Optional(), Length(max=200)])
    
    gender = SelectField('Género', choices=[
        ('', 'Seleccionar...'),
        ('MALE', 'Masculino'),
        ('FEMALE', 'Femenino'),
        ('OTHER', 'Otro')
    ], validators=[Optional()])
    
    eye_color = StringField('Color de Ojos', validators=[Optional(), Length(max=50)])
    hair_color = StringField('Color de Cabello', validators=[Optional(), Length(max=50)])
    hair_type = StringField('Tipo de Cabello', validators=[Optional(), Length(max=50)])
    hair_length = StringField('Longitud del Cabello', validators=[Optional(), Length(max=50)])
    body_type = StringField('Tipo de Cuerpo', validators=[Optional(), Length(max=50)])
    height = FloatField('Altura (cm)', validators=[Optional(), NumberRange(min=0, max=300)])
    weight = IntegerField('Peso (kg)', validators=[Optional(), NumberRange(min=0, max=500)])
    last_seen_clothing = StringField('Última Ropa Vista', validators=[Optional(), Length(max=200)])
    
    photo = FileField('Foto', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes')
    ])
    
    first_name = StringField('Primer Nombre', validators=[Optional(), Length(max=100)])
    last_name1 = StringField('Primer Apellido', validators=[Optional(), Length(max=100)])
    last_name2 = StringField('Segundo Apellido', validators=[Optional(), Length(max=100)])
    
    disappearance_type = SelectField('Tipo de Desaparición', choices=[
        ('', 'Seleccionar...'),
        ('VOLUNTARY', 'Voluntaria'),
        ('INVOLUNTARY', 'Involuntaria'),
        ('UNKNOWN', 'Desconocido')
    ], validators=[Optional()])
    
    needs = TextAreaField('Necesidades Especiales', validators=[Optional()])
    
    submit = SubmitField('Crear Caso') 