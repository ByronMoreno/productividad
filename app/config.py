import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-key-for-development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///antigravity.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
