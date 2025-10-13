from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Load các biến môi trường từ tệp .env
    load_dotenv()

    # Khởi tạo ứng dụng Flask
    app = Flask(__name__)

    # Đăng ký các blueprint cho các module API
    from .api.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    from .api.iot_devices import users_bp as iot_devices_bp
    app.register_blueprint(iot_devices_bp, url_prefix='/api/iot-devices')

    # Trả về ứng dụng Flask đã được cấu hình
    return app
