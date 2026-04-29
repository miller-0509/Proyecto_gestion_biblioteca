from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime, timezone
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(id_usuario):
        from .models.usuarios import Usuario
        return Usuario.query.get(int(id_usuario))

    # Agregar función 'now' al contexto global de Jinja
    @app.context_processor
    def inject_now():
        return {'now': lambda: datetime.now(timezone.utc).replace(tzinfo=None)}

    # Manejador para confirmar transacciones correctamente
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Cierra la sesión de BD de forma segura"""
        if exception is None:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error al confirmar transacción: {e}")
        db.session.remove()

    #Blueprints
    from app.routes import auth, equipos, prestamos, libros, prestamos_libros, usuarios
    app.register_blueprint(auth.bp)
    app.register_blueprint(equipos.bp)
    app.register_blueprint(prestamos.bp)
    app.register_blueprint(libros.bp)
    app.register_blueprint(prestamos_libros.bp)
    app.register_blueprint(usuarios.bp)


    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_error(e):
        db.session.rollback()
        print(f"Error no controlado: {str(e)}")
        return render_template('errors/500.html'), 500

    return app
