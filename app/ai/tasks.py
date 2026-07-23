from app.core.celery_app import celery_app
from app.core.database import db
from app.inbox.models import InboxItem
from app.tasks.models import Task
from app.projects.models import Project
from app.ai.services import AIService
from datetime import datetime

@celery_app.task(name='app.ai.tasks.process_inbox_item_task')
def process_inbox_item_task(item_id: int):
    item = db.session.get(InboxItem, item_id)
    if not item or item.is_processed:
        return f"Item {item_id} no encontrado o ya procesado."

    data = AIService.classify_text(item.content)

    project_name = data.get('project_name')
    project_id = None
    if project_name:
        project_name = project_name.strip()
        project = Project.query.filter_by(name=project_name, user_id=item.user_id).first()
        if not project:
            project = Project(
                name=project_name, 
                description=f"Creado automáticamente por la IA para {project_name}.",
                user_id=item.user_id
            )
            db.session.add(project)
            db.session.commit()
        project_id = project.id

    due_date = None
    due_date_str = data.get('due_date')
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    task = Task(
        title=data.get('title', item.content[:100]),
        description=data.get('description', item.content),
        status='PENDING',
        energy=data.get('energy', 3),
        priority=data.get('priority', 'MEDIUM'),
        estimated_time=data.get('estimated_time', 30),
        due_date=due_date,
        project_id=project_id,
        user_id=item.user_id
    )
    
    db.session.add(task)
    
    item.is_processed = True
    item.processed_at = datetime.utcnow()
    
    db.session.commit()

    return f"Inbox item {item_id} clasificado como tarea: '{task.title}'"
