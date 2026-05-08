from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, logout_user, current_user
from datetime import datetime, timezone, timedelta
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

def create_app(config_class=None):
    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────────────
    if config_class is None:
        from config import get_config
        config_class = get_config()

    app.config.from_object(config_class)

    # ── Extensiones ────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # ── Health Check ───────────────────────────────────────────────
    @app.route("/health")
    @limiter.exempt
    def health():
        return {"status": "healthy"}, 200

    # Eximir /logout de CSRF para sendBeacon (POST al cerrar pestaña)
    from app.routes.auth import bp as auth_bp
    csrf.exempt(auth_bp)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder.'
    login_manager.login_message_category = 'warning'

    # ── Logging ────────────────────────────────────────────────────
    from app.logger import setup_logging
    setup_logging(app)

    @login_manager.user_loader
    def load_user(id_usuario):
        from .models.usuarios import Usuario
        return Usuario.query.get(int(id_usuario))

    # Agregar función 'now' al contexto global de Jinja
    @app.context_processor
    def inject_now():
        return {
            'now': lambda: datetime.now(timezone.utc).replace(tzinfo=None)
        }

    # Auto-logout si la cuenta fue desactivada
    @app.before_request
    def check_user_active():
        if current_user.is_authenticated and not current_user.is_active:
            logout_user()

            from flask import flash, redirect, url_for

            flash(
                'Tu cuenta ha sido desactivada. Contacta al administrador.',
                'warning'
            )

            return redirect(url_for('auth.login'))

    # Sesión no permanente
    @app.before_request
    def configure_session():
        from flask import session

        session.permanent = False
        app.permanent_session_lifetime = timedelta(minutes=30)

    # Limpieza segura de sesión DB
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()

        db.session.remove()

    # ── Blueprints ─────────────────────────────────────────────────
    from app.routes import (
        auth,
        equipos,
        prestamos,
        libros,
        prestamos_libros,
        usuarios
    )

    app.register_blueprint(auth.bp)
    app.register_blueprint(equipos.bp)
    app.register_blueprint(prestamos.bp)
    app.register_blueprint(libros.bp)
    app.register_blueprint(prestamos_libros.bp)
    app.register_blueprint(usuarios.bp)

    # ── Error Handlers ─────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if app.debug:
            return render_template('errors/404.html')

        return {"error": "Página no encontrada"}, 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(
            'Rate limit excedido: %s',
            e.description
        )

        return {
            "error": "Demasiadas solicitudes. Intenta de nuevo más tarde."
        }, 429

    @app.errorhandler(Exception)
    def handle_error(e):

        # Evita convertir errores HTTP normales en 500
        if isinstance(e, HTTPException):
            return e

        app.logger.error(
            'Error no manejado: %s',
            str(e),
            exc_info=True
        )

        return {
            "error": "Ha ocurrido un error interno. Contacta al administrador."
        }, 500

    return app