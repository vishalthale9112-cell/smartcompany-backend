from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Ticket, User
from services.ticket_priority import predict_priority
from services.ticket_category import predict_category

tickets_bp = Blueprint('tickets', __name__)


@tickets_bp.route('/', methods=['GET'])
@jwt_required()
def list_tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    result = []
    for t in tickets:
        result.append({
            'id': t.id,
            'subject': t.subject,
            'description': t.description,
            'category': t.category,
            'category_confidence': t.category_confidence,
            'category_source': t.category_source,
            'priority': t.priority,
            'priority_confidence': t.priority_confidence,
            'priority_source': t.priority_source,
            'status': t.status,
            'raised_by': t.raiser.name if t.raiser else None,
            'assigned_to': t.handler.name if t.handler else None,
            'assigned_to_id': t.assigned_to,
        })
    return jsonify(result), 200


@tickets_bp.route('/summary', methods=['GET'])
@jwt_required()
def tickets_summary():
    open_count = Ticket.query.filter_by(status='open').count()
    in_progress = Ticket.query.filter_by(status='in_progress').count()
    resolved = Ticket.query.filter_by(status='resolved').count()

    return jsonify({
        'open': open_count,
        'in_progress': in_progress,
        'resolved': resolved,
        'total_pending': open_count + in_progress,
    }), 200


@tickets_bp.route('/', methods=['POST'])
@jwt_required()
def create_ticket():
    data = request.get_json()
    raiser_id = int(get_jwt_identity())

    subject = data.get('subject')
    if not subject:
        return jsonify({'error': 'subject is required'}), 400

    priority_prediction = predict_priority(subject, data.get('description'))
    category_prediction = predict_category(subject, data.get('description'))
    new_ticket = Ticket(
        subject=subject,
        description=data.get('description'),
        category=category_prediction['category'],
        category_confidence=category_prediction['confidence'],
        category_source=category_prediction['source'],
        priority=priority_prediction['priority'],
        priority_confidence=priority_prediction['confidence'],
        priority_source=priority_prediction['source'],
        status=data.get('status', 'open'),
        raised_by=raiser_id,
        assigned_to=data.get('assigned_to'),
    )
    db.session.add(new_ticket)
    db.session.commit()

    return jsonify({
        'message': 'Ticket created',
        'id': new_ticket.id,
        'ai_prediction': {
            'priority': priority_prediction,
            'category': category_prediction,
        },
    }), 201


@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    data = request.get_json()
    ticket.status = data.get('status', ticket.status)
    ticket.assigned_to = data.get('assigned_to', ticket.assigned_to)

    db.session.commit()
    return jsonify({'message': 'Ticket updated'}), 200


@tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@jwt_required()
def delete_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'Ticket deleted'}), 200
