import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-key-for-development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///antigravity.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Resolver desconexiones de BD inactivas (por ejemplo, al salir a almorzar)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "pool_timeout": 30,
        "pool_size": 10,
        "max_overflow": 20
    }
    
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

