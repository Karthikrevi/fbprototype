
from flask import Blueprint

bp = Blueprint('pets', __name__)

from . import routes
