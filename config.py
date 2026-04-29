import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base compartida."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-cambiar-en-produccion-obligatorio')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///almacendb.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Seguridad de cookies ──────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600  # 1 hora


class DevelopmentConfig(Config):
    """Configuración para desarrollo local."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configuración para producción."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# Mapa de entornos
config_by_env = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}


def get_config():
    """Retorna la configuración según FLASK_ENV."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_env.get(env, DevelopmentConfig)
