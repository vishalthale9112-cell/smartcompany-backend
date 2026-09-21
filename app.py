import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db


app = Flask(__name__)

# --- Database config ---
database_url = os.getenv('DATABASE_URL')

if database_url and database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+mysqlconnector://", 1)

if not database_url:
    raise RuntimeError('DATABASE_URL environment variable is required')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- JWT config ---
jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    raise RuntimeError('JWT_SECRET_KEY environment variable is required')

app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

db.init_app(app)
jwt = JWTManager(app)

allowed_origins = [
    origin.strip()
    for origin in os.getenv('FRONTEND_URLS', 'http://localhost:5173').split(',')
    if origin.strip()
]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})


@jwt.expired_token_loader
def expired_token_callback(_jwt_header, _jwt_payload):
    return jsonify({'error': 'Your session has expired. Please sign in again.'}), 401


@jwt.invalid_token_loader
def invalid_token_callback(_error):
    return jsonify({'error': 'Invalid access token'}), 401


@jwt.unauthorized_loader
def missing_token_callback(_error):
    return jsonify({'error': 'Authentication is required'}), 401


# --- Blueprints (routes) ---
from routes.auth_routes import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')

from routes.employee_routes import employees_bp
app.register_blueprint(employees_bp, url_prefix='/api/employees')

from routes.task_routes import tasks_bp
app.register_blueprint(tasks_bp, url_prefix='/api/tasks')

from routes.attendance_routes import attendance_bp
app.register_blueprint(attendance_bp, url_prefix='/api/attendance')

from routes.ticket_routes import tickets_bp
app.register_blueprint(tickets_bp, url_prefix='/api/tickets')

from routes.ai_routes import ai_bp
app.register_blueprint(ai_bp, url_prefix='/api/ai')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', port=5000)
