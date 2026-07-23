from flask import Blueprint, request, render_template, session
from app.core.database import db
from app.core.models import UserStatus
from app.tasks.models import Task
from app.ai.services import AIService
from app.ai.models import AgentCollaborationLog
from app.auth.utils import login_required

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/coach', methods=['POST'])
@login_required
def coach():
    u_id = session['user_id']
    user_message = request.form.get('message', '').strip()
    if not user_message:
        return ""

    from datetime import date
    from app.auth.models import DailyObjective
    
    status = UserStatus.get_status(user_id=u_id)
    pending_tasks = Task.query.filter(Task.status != 'DONE', Task.user_id == u_id).all()
    daily_obj = DailyObjective.query.filter_by(user_id=u_id, date=date.today()).first()
    daily_obj_content = daily_obj.content if daily_obj else None

    coach_reply = AIService.get_coach_response(
        user_message=user_message,
        energy_limit=status.current_energy_limit,
        pending_tasks=pending_tasks,
        daily_objective=daily_obj_content
    )

    return render_template('ai/partials/chat_response.html', user_message=user_message, coach_reply=coach_reply)

@ai_bp.route('/agents-debate', methods=['POST'])
@login_required
def agents_debate():
    u_id = session['user_id']
    
    from datetime import date
    from app.auth.models import DailyObjective
    
    status = UserStatus.get_status(user_id=u_id)
    pending_tasks = Task.query.filter(Task.status != 'DONE', Task.user_id == u_id).all()
    daily_obj = DailyObjective.query.filter_by(user_id=u_id, date=date.today()).first()
    daily_obj_content = daily_obj.content if daily_obj else None

    # Simular debate
    transcript, recommendations = AIService.simulate_agent_debate(
        energy_limit=status.current_energy_limit,
        pending_tasks=pending_tasks,
        daily_objective=daily_obj_content
    )

    # Convertir recomendaciones a string para guardar en DB
    rec_str = ", ".join(recommendations) if isinstance(recommendations, list) else str(recommendations)

    # Registrar debate en BD
    log = AgentCollaborationLog(transcript=transcript, recommendations=rec_str)
    db.session.add(log)
    db.session.commit()

    return render_template('ai/partials/debate_result.html', transcript=transcript, recommendations=recommendations)

