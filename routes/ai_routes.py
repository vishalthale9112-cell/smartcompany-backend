import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import google.generativeai as genai
from models import Task, Ticket, User

ai_bp = Blueprint('ai', __name__)

# Reads GEMINI_API_KEY from the environment
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-3.6-flash')


def build_context():
    """Pull a lightweight snapshot of current data to ground the AI's answers."""
    tasks = Task.query.all()
    tickets = Ticket.query.all()
    employee_count = User.query.count()

    task_lines = [
        f"- [{t.status}] {t.title} (priority: {t.priority}, assigned to: {t.assignee.name if t.assignee else 'unassigned'})"
        for t in tasks
    ]
    ticket_lines = [
        f"- [{tk.status}] {tk.subject} (category: {tk.category}, assigned to: {tk.handler.name if tk.handler else 'unassigned'})"
        for tk in tickets
    ]

    context = (
        f"Company snapshot:\n"
        f"Total employees: {employee_count}\n\n"
        f"Tasks ({len(tasks)} total):\n" + ("\n".join(task_lines) if task_lines else "None") + "\n\n"
        f"Tickets ({len(tickets)} total):\n" + ("\n".join(ticket_lines) if ticket_lines else "None")
    )
    return context


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'message is required'}), 400

    context = build_context()

    prompt = (
        "You are the AI Assistant inside SmartCompany, an internal operations dashboard. "
        "Answer the user's question using the data snapshot below. Be concise (a few sentences "
        "or a short bullet list), and speak like a helpful colleague, not a report generator.\n\n"
        f"{context}\n\n"
        f"User question: {user_message}"
    )

    try:
        response = model.generate_content(prompt)
        return jsonify({'reply': response.text}), 200

    except Exception as e:
        return jsonify({'error': f'AI request failed: {str(e)}'}), 500