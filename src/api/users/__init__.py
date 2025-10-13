from flask import Blueprint

# Khởi tạo blueprint cho monitoring well
users_bp = Blueprint('users', __name__)

from . import routes