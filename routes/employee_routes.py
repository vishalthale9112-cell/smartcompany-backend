from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from flask_bcrypt import Bcrypt
from models import db, User, Department

employees_bp = Blueprint('employees', __name__)
bcrypt = Bcrypt()


def admin_or_manager_required():
    """Helper to allow access only to admin or manager"""
    claims = get_jwt()
    return claims.get('role') in ('admin', 'manager')


@employees_bp.route('/', methods=['GET'])
@jwt_required()
def list_employees():
    users = User.query.all()
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'department': u.department.name if u.department else None,
        })
    return jsonify(result), 200


@employees_bp.route('/count', methods=['GET'])
@jwt_required()
def employee_count():
    count = User.query.count()
    return jsonify({'count': count}), 200


@employees_bp.route('', methods=['POST'])
@jwt_required()
def add_employee():
    if not admin_or_manager_required():
        return jsonify({'error': 'Only admin or manager can add employees'}), 403

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'employee')
    department_name = data.get('department')

    if not name or not email or not password:
        return jsonify({'error': 'name, email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'This email is already in use'}), 409

    department = None
    if department_name:
        department = Department.query.filter_by(name=department_name).first()
        if not department:
            department = Department(name=department_name)
            db.session.add(department)
            db.session.flush()

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(
        name=name,
        email=email,
        password_hash=hashed_pw,
        role=role,
        department_id=department.id if department else None,
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Employee created', 'id': new_user.id}), 201


@employees_bp.route('/<int:employee_id>', methods=['PUT'])
@jwt_required()
def edit_employee(employee_id):
    if not admin_or_manager_required():
        return jsonify({'error': 'Only admin or manager can edit employees'}), 403

    user = User.query.get(employee_id)
    if not user:
        return jsonify({'error': 'Employee not found'}), 404

    data = request.get_json()
    user.name = data.get('name', user.name)
    user.role = data.get('role', user.role)

    db.session.commit()
    return jsonify({'message': 'Employee updated'}), 200


@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
@jwt_required()
def delete_employee(employee_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Only admin can delete employees'}), 403

    user = User.query.get(employee_id)
    if not user:
        return jsonify({'error': 'Employee not found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Employee deleted'}), 200