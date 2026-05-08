import os
from dotenv import load_dotenv

# Solo cargar .env en desarrollo local
if os.environ.get("FLASK_ENV") != "production":
    load_dotenv()


class Config:
    """Configuración base compartida."""
    
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'dev-cambiar-en-produccion-obligatorio'
    )

    database_url = os.getenv("DATABASE_URL")

    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = database_url

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

    if env == 'production' and os.environ.get('SECRET_KEY') is None:
        raise ValueError(
            "Falta la SECRET_KEY en el entorno de Producción."
        )

    return config_by_env.get(env, DevelopmentConfig)