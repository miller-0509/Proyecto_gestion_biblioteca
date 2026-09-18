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

    # Optimización de conexiones DB (Pool)
    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # Forzar TimeZone=UTC en cada conexión para que los timestamps
    # se almacenen e interpreten consistentemente con datetime.now(timezone.utc).
    if database_url and database_url.startswith("postgres"):
        engine_options["connect_args"] = {"options": "-c TimeZone=UTC"}

    SQLALCHEMY_ENGINE_OPTIONS = engine_options

    # ── Seguridad y unicidad de cookies ───────────────────────────
    SESSION_COOKIE_NAME = 'biblioteca_session'  # Evita colisiones de cookies en el mismo dominio/IP (Coolify)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600  # 1 hora

    # ── Configuración de Correo SMTP ─────────────────────────────
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    MAIL_MAX_EMAILS = 10  # Límite por conexión SMTP

    # ── Configuración de Sistema de Multas (Suspensión) ───────────
    MULTA_DIAS_POR_RETRASO_LIBRO = 1  # 1 día de retraso = 1 día de suspensión
    MULTA_DIAS_POR_RETRASO_EQUIPO = 1 # 1 día de retraso = 1 día de suspensión
    DIAS_GRACIA_MULTA = 1             # Días de gracia antes de empezar a contar el retraso


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


class TestingConfig(Config):
    """Configuración para pruebas automatizadas con pytest."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}  # Deshabilita connect_args de PostgreSQL para SQLite in-memory
    WTF_CSRF_ENABLED = False        # Deshabilita validación CSRF en peticiones POST de pruebas
    RATELIMIT_ENABLED = False       # Deshabilita rate limiting durante la ejecución de tests
    MAIL_SUPPRESS_SEND = True       # Evita el envío real de correos durante pruebas
    SECRET_KEY = 'testing-secret-key-para-pruebas-unitarias'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


# Mapa de entornos
config_by_env = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config():
    """Retorna la configuración según FLASK_ENV (por defecto 'development' para facilitar desarrollo local)."""

    env = os.environ.get('FLASK_ENV', 'development')

    if env == 'production' and os.environ.get('SECRET_KEY') is None:
        raise ValueError(
            "Falta la SECRET_KEY en el entorno de Producción."
        )

    return config_by_env.get(env, DevelopmentConfig)