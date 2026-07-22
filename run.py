import time
from sqlalchemy.exc import OperationalError
from app import create_app
from app.core.database import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        for i in range(10):
            try:
                db.create_all()
                print("Base de datos inicializada correctamente.")
                break
            except OperationalError as e:
                print(f"Base de datos no disponible, reintentando en 2 segundos... ({i+1}/10)")
                time.sleep(2)
        else:
            print("Error: No se pudo conectar a la base de datos tras varios intentos.")
    app.run(host='0.0.0.0', port=5000, debug=True)


