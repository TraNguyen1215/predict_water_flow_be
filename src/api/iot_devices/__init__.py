from flask import Blueprint

# Khởi tạo blueprint cho monitoring well
users_bp = Blueprint('iot-devices', __name__)

from . import routes