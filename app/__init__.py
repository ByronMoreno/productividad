from flask import Flask
from app.config import Config
from app.core.database import db
from flask_migrate import Migrate
from celery import Celery, Task

migrate = Migrate()

def init_celery(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config, namespace='CELERY')
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    init_celery(app)

    # Registrar blueprints
    from app.inbox.routes import inbox_bp
    from app.projects.routes import projects_bp
    from app.tasks.routes import tasks_bp
    from app.calendar.routes import calendar_bp
    from app.core.routes import core_bp
    from app.ai.routes import ai_bp
    from app.knowledge.routes import knowledge_bp
    from app.analytics.routes import analytics_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(inbox_bp, url_prefix='/inbox')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(knowledge_bp, url_prefix='/knowledge')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    @app.context_processor
    def inject_projects():
        from app.projects.models import Project
        return dict(projects=Project.query.order_by(Project.name).all())

    return app
