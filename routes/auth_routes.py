from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import SQLAlchemyError
from models import db, User

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()


def _request_data():
    return request.get_json(silent=True) or {}


@auth_bp.route('/register', methods=['POST'])
def register():
    data = _request_data()
    name = str(data.get('name', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    if len(name) < 2:
        return jsonify({'error': 'Please enter a valid full name'}), 400

    if not email or '@' not in email:
        return jsonify({'error': 'Please enter a valid email address'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must contain at least 8 characters'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'This email is already in use'}), 409

    # Public registration always creates an employee account. Admin and manager
    # roles must only be assigned through a protected management endpoint.
    new_user = User(
        name=name,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
        role='employee',
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'Unable to create the account right now'}), 500

    return jsonify({
        'message': 'Account created successfully',
        'user_id': new_user.id,
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = _request_data()
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role},
    )

    return jsonify({
        'access_token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
        },
    }), 200
