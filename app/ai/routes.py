from flask import Blueprint, request, render_template
from app.core.database import db
from app.core.models import UserStatus
from app.tasks.models import Task
from app.ai.services import AIService
from app.ai.models import AgentCollaborationLog

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/coach', methods=['POST'])
def coach():
    user_message = request.form.get('message', '').strip()
    if not user_message:
        return ""

    status = UserStatus.get_status()
    pending_tasks = Task.query.filter(Task.status != 'DONE').all()

    coach_reply = AIService.get_coach_response(
        user_message=user_message,
        energy_limit=status.current_energy_limit,
        pending_tasks=pending_tasks
    )

    return render_template('ai/partials/chat_response.html', user_message=user_message, coach_reply=coach_reply)

@ai_bp.route('/agents-debate', methods=['POST'])
def agents_debate():
    status = UserStatus.get_status()
    pending_tasks = Task.query.filter(Task.status != 'DONE').all()

    # Simular debate
    transcript, recommendations = AIService.simulate_agent_debate(
        energy_limit=status.current_energy_limit,
        pending_tasks=pending_tasks
    )

    # Convertir recomendaciones a string para guardar en DB
    rec_str = ", ".join(recommendations) if isinstance(recommendations, list) else str(recommendations)

    # Registrar debate en BD
    log = AgentCollaborationLog(transcript=transcript, recommendations=rec_str)
    db.session.add(log)
    db.session.commit()

    return render_template('ai/partials/debate_result.html', transcript=transcript, recommendations=recommendations)
