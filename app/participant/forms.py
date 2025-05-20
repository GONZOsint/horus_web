from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, URLField, FileField
from wtforms.validators import DataRequired, Length, URL, Optional
from flask_wtf.file import FileAllowed
from app.models import FlagSubmission

class CreateTeamForm(FlaskForm):
    name = StringField('Nombre del Equipo', validators=[
        DataRequired(),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])
    submit = SubmitField('Crear Equipo')

class JoinTeamForm(FlaskForm):
    invitation_code = StringField('Código de Invitación', validators=[
        DataRequired(),
        Length(min=8, max=8, message='El código de invitación debe tener 8 caracteres')
    ])
    submit = SubmitField('Unirse al Equipo')

class FlagSubmissionForm(FlaskForm):
    category = SelectField('Categoría', 
                         choices=[(k, f"{v[0]} ({v[1]} puntos)") for k, v in FlagSubmission.CATEGORIES.items()],
                         validators=[DataRequired()])
    flag = StringField('Flag', validators=[
        DataRequired(),
        Length(min=1, max=255, message='La flag debe tener entre 1 y 255 caracteres')
    ])
    source_url = URLField('Fuente (URL)', validators=[
        Optional(),
        URL(message='Por favor, ingresa una URL válida'),
        Length(max=500, message='La URL no puede tener más de 500 caracteres')
    ])
    photo = FileField('Foto', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes')
    ])
    description = TextAreaField('Descripción del Hallazgo', validators=[
        DataRequired(),
        Length(min=10, max=1000, message='La descripción debe tener entre 10 y 1000 caracteres')
    ])
    submit = SubmitField('Enviar Flag') 