from app import create_app
from app.core.database import db
from app.projects.models import Project
from app.tasks.models import Task

def init_demo():
    app = create_app()
    with app.app_context():
        p_docencia = Project.query.filter_by(name="Docencia").first()
        if not p_docencia:
            p_docencia = Project(name="Docencia", color_hex="#2563eb", description="Gestión académica, clases y tesis.")
            db.session.add(p_docencia)
            
        p_devops = Project.query.filter_by(name="DevOps/Desarrollo").first()
        if not p_devops:
            p_devops = Project(name="DevOps/Desarrollo", color_hex="#16a34a", description="Infraestructura de Docker y código de software.")
            db.session.add(p_devops)

        p_bolsa = Project.query.filter_by(name="Bolsa").first()
        if not p_bolsa:
            p_bolsa = Project(name="Bolsa", color_hex="#ca8a04", description="Inversiones, análisis de mercado y acciones.")
            db.session.add(p_bolsa)

        p_salud = Project.query.filter_by(name="Salud").first()
        if not p_salud:
            p_salud = Project(name="Salud", color_hex="#dc2626", description="Bienestar físico, personal y descanso.")
            db.session.add(p_salud)

        db.session.commit()

        t1 = Task.query.filter_by(title="Revisar tesis de Pedro antes del viernes").first()
        if not t1:
            t1 = Task(title="Revisar tesis de Pedro antes del viernes", description="Lectura crítica del capítulo 3 y feedback.", estimated_time=90, energy=4, status="PENDING", project_id=p_docencia.id)
            db.session.add(t1)

        t2 = Task.query.filter_by(title="Ajustar contenedor de Docker para producción").first()
        if not t2:
            t2 = Task(title="Ajustar contenedor de Docker para producción", description="Configurar volumen persistente y límites de memoria.", estimated_time=45, energy=3, status="PENDING", project_id=p_devops.id)
            db.session.add(t2)

        t3 = Task.query.filter_by(title="Analizar balance trimestral de Apple").first()
        if not t3:
            t3 = Task(title="Analizar balance trimestral de Apple", description="Revisar EPS y proyecciones de ventas de iPhone.", estimated_time=30, energy=2, status="PENDING", project_id=p_bolsa.id)
            db.session.add(t3)

        t4 = Task.query.filter_by(title="Hacer 30 min de ejercicio cardiovascular").first()
        if not t4:
            t4 = Task(title="Hacer 30 min de ejercicio cardiovascular", description="Caminar o trotar suave para oxigenar el cerebro.", estimated_time=30, energy=1, status="PENDING", project_id=p_salud.id)
            db.session.add(t4)

        db.session.commit()
        print("Datos de prueba cargados exitosamente para el debate.")

if __name__ == "__main__":
    init_demo()
