from flask import Blueprint

bp = Blueprint('judge', __name__)

from app.judge import routes 