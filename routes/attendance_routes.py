from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime
from models import db, Attendance, User

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/', methods=['GET'])
@jwt_required()
def list_attendance():
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    result = []
    for r in records:
        result.append({
            'id': r.id,
            'user_id': r.user_id,
            'user_name': r.user.name if r.user else None,
            'date': r.date.isoformat(),
            'status': r.status,
        })
    return jsonify(result), 200


@attendance_bp.route('/summary', methods=['GET'])
@jwt_required()
def attendance_summary():
    """Counts for the dashboard donut chart"""
    present = Attendance.query.filter_by(status='present').count()
    absent = Attendance.query.filter_by(status='absent').count()
    half_day = Attendance.query.filter_by(status='half_day').count()
    leave = Attendance.query.filter_by(status='leave').count()

    return jsonify({
        'present': present,
        'absent': absent,
        'half_day': half_day,
        'leave': leave,
    }), 200


@attendance_bp.route('/', methods=['POST'])
@jwt_required()
def mark_attendance():
    """Mark attendance for yourself, or for someone else if admin/manager"""
    data = request.get_json()
    user_id = data.get('user_id') or int(get_jwt_identity())
    status = data.get('status', 'present')
    attendance_date = data.get('date')

    if attendance_date:
        attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
    else:
        attendance_date = date.today()

    # If a record already exists for that day, update it — otherwise create a new one
    existing = Attendance.query.filter_by(user_id=user_id, date=attendance_date).first()
    if existing:
        existing.status = status
        db.session.commit()
        return jsonify({'message': 'Attendance updated', 'id': existing.id}), 200

    new_record = Attendance(user_id=user_id, date=attendance_date, status=status)
    db.session.add(new_record)
    db.session.commit()

    return jsonify({'message': 'Attendance marked', 'id': new_record.id}), 201