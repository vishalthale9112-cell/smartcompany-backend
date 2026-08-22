from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db

app = Flask(__name__)

# --- Database config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Vishal%40123@localhost/smartcompany_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- JWT config ---
app.config['JWT_SECRET_KEY'] = 'change-this-secret-key-later'

db.init_app(app)
jwt = JWTManager(app)
CORS(app)

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
    db.create_all()  # This will automatically create all tables above in MySQL

if __name__ == '__main__':
    app.run(debug=True, port=5000)