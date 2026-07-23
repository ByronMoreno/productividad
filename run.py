import time
from sqlalchemy.exc import OperationalError
from app import create_app
from app.core.database import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from app.auth.models import User, SystemConfig
        for i in range(10):
            try:
                db.create_all()

                print("Base de datos inicializada correctamente.")
                
                # Asegurar columnas user_id en caliente si no existen
                from sqlalchemy import text
                tables_to_migrate = ['tasks', 'projects', 'inbox_items', 'time_blocks', 'user_status', 'knowledge_nodes']
                for table in tables_to_migrate:
                    try:
                        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"))
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        print(f"Nota: Columna user_id en {table} ya existe o requiere verificación. ({e})")

                # Asegurar columna profile_pic_filename en la tabla users
                try:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_pic_filename VARCHAR(255)"))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Nota: Columna profile_pic_filename en users ya existe o requiere verificación. ({e})")

                # Asegurar columna image_filename en la tabla knowledge_nodes
                try:
                    db.session.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS image_filename VARCHAR(255)"))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Nota: Columna image_filename en knowledge_nodes ya existe o requiere verificación. ({e})")


                # Crear administrador inicial

                from app.auth.models import User
                admin = User.query.filter_by(email='bmoreno@uees.edu.ec').first()
                if not admin:
                    admin = User(email='bmoreno@uees.edu.ec', role='ADMIN')
                    admin.set_password('12345')
                    db.session.add(admin)
                    db.session.commit()
                    print("Usuario administrador bmoreno@uees.edu.ec creado con éxito.")
                    
                # Migración de datos existentes con user_id nulo al nuevo admin
                for table in tables_to_migrate:
                    db.session.execute(
                        text(f"UPDATE {table} SET user_id = :u_id WHERE user_id IS NULL"),
                        {"u_id": admin.id}
                    )
                db.session.commit()
                print("Migración en caliente de datos históricos finalizada con éxito.")
                break


            except OperationalError as e:
                print(f"Base de datos no disponible, reintentando en 2 segundos... ({i+1}/10)")
                time.sleep(2)
        else:
            print("Error: No se pudo conectar a la base de datos tras varios intentos.")
    app.run(host='0.0.0.0', port=5000, debug=True)


