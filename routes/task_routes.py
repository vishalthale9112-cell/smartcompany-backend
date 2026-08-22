from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from models import db, Task, User

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def list_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    result = []
    for t in tasks:
        result.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'assigned_to': t.assignee.name if t.assignee else None,
            'assigned_to_id': t.assigned_to,
            'due_date': t.due_date.isoformat() if t.due_date else None,
        })
    return jsonify(result), 200


@tasks_bp.route('/summary', methods=['GET'])
@jwt_required()
def tasks_summary():
    """Quick counts for dashboard stat cards"""
    in_progress = Task.query.filter_by(status='in_progress').count()
    completed = Task.query.filter_by(status='completed').count()
    pending = Task.query.filter_by(status='pending').count()

    high = Task.query.filter_by(priority='high').count()
    medium = Task.query.filter_by(priority='medium').count()
    low = Task.query.filter_by(priority='low').count()

    return jsonify({
        'in_progress': in_progress,
        'completed': completed,
        'pending': pending,
        'priority': {'high': high, 'medium': medium, 'low': low},
    }), 200


@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    creator_id = int(get_jwt_identity())

    title = data.get('title')
    if not title:
        return jsonify({'error': 'title is required'}), 400

    new_task = Task(
        title=title,
        description=data.get('description'),
        status=data.get('status', 'pending'),
        priority=data.get('priority', 'medium'),
        assigned_to=data.get('assigned_to'),
        created_by=creator_id,
    )
    db.session.add(new_task)
    db.session.commit()

    return jsonify({'message': 'Task created', 'id': new_task.id}), 201


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json()
    task.title = data.get('title', task.title)
    task.status = data.get('status', task.status)
    task.priority = data.get('priority', task.priority)
    task.assigned_to = data.get('assigned_to', task.assigned_to)

    db.session.commit()
    return jsonify({'message': 'Task updated'}), 200


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'}), 200