"""
Fixtures globales y configuración de pruebas unitarias/integración para pytest.
Utiliza base de datos SQLite en memoria para garantizar aislamiento total y rapidez.
"""
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app, db
from app.models.usuarios import Usuario
from app.models.libros import Libro
from app.models.equipos import Equipo
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro
from config import TestingConfig


@pytest.fixture(scope='function')
def app():
    """Crea y configura una nueva instancia de la aplicación para cada prueba."""
    flask_app = create_app(TestingConfig)

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Cliente de pruebas de Flask para simular peticiones HTTP."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """CLI runner para probar comandos de consola de Flask."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Acceso a la sesión de base de datos activa de la prueba."""
    return db.session


# ── Fixtures de Usuarios ──────────────────────────────────────────────────

@pytest.fixture
def admin_user(app):
    """Crea y persiste un usuario Administrador activo y verificado."""
    user = Usuario(
        nombres="Admin",
        apellidos="Sistema",
        correo="admin@biblioteca.test",
        rol="administrador",
        estado="activo",
        email_verificado=True,
        fecha_verificacion=datetime.now(timezone.utc)
    )
    user.set_password("Admin123!")
    user.save()
    db.session.commit()
    return user


@pytest.fixture
def bibliotecario_user(app):
    """Crea y persiste un usuario Bibliotecario activo y verificado."""
    user = Usuario(
        nombres="Carlos",
        apellidos="Bibliotecario",
        correo="bibliotecario@biblioteca.test",
        rol="bibliotecario",
        estado="activo",
        email_verificado=True,
        fecha_verificacion=datetime.now(timezone.utc)
    )
    user.set_password("Biblio123!")
    user.save()
    db.session.commit()
    return user


@pytest.fixture
def almacenista_user(app):
    """Crea y persiste un usuario Almacenista activo y verificado."""
    user = Usuario(
        nombres="Ana",
        apellidos="Almacenista",
        correo="almacenista@biblioteca.test",
        rol="almacenista",
        estado="activo",
        email_verificado=True,
        fecha_verificacion=datetime.now(timezone.utc)
    )
    user.set_password("Almacen123!")
    user.save()
    db.session.commit()
    return user


@pytest.fixture
def aprendiz_user(app):
    """Crea y persiste un usuario Aprendiz activo y verificado."""
    user = Usuario(
        nombres="Juan",
        apellidos="Perez",
        correo="aprendiz@biblioteca.test",
        rol="aprendiz",
        estado="activo",
        email_verificado=True,
        fecha_verificacion=datetime.now(timezone.utc)
    )
    user.set_password("Aprendiz123!")
    user.save()
    db.session.commit()
    return user


@pytest.fixture
def instructor_user(app):
    """Crea y persiste un usuario Instructor activo y verificado."""
    user = Usuario(
        nombres="Maria",
        apellidos="Docente",
        correo="instructor@biblioteca.test",
        rol="instructor",
        estado="activo",
        email_verificado=True,
        fecha_verificacion=datetime.now(timezone.utc)
    )
    user.set_password("Docente123!")
    user.save()
    db.session.commit()
    return user


@pytest.fixture
def unverified_user(app):
    """Crea y persiste un usuario Aprendiz no verificado."""
    user = Usuario(
        nombres="NoVerificado",
        apellidos="Usuario",
        correo="noverificado@biblioteca.test",
        rol="aprendiz",
        estado="activo",
        email_verificado=False
    )
    user.set_password("Password123!")
    user.save()
    db.session.commit()
    return user


@pytest.fixture
def inactive_user(app):
    """Crea y persiste un usuario Inactivo."""
    user = Usuario(
        nombres="Inactivo",
        apellidos="Usuario",
        correo="inactivo@biblioteca.test",
        rol="aprendiz",
        estado="inactivo",
        email_verificado=True
    )
    user.set_password("Password123!")
    user.save()
    db.session.commit()
    return user


# ── Fixtures de Autenticación ─────────────────────────────────────────────

@pytest.fixture
def auth_client(client):
    """Helper fixture para autenticar a un usuario en el test_client."""
    def _login(correo, password):
        return client.post(
            '/',
            data={'correo': correo, 'password': password},
            follow_redirects=True
        )
    return _login


@pytest.fixture
def admin_client(client, admin_user, auth_client):
    """Cliente de prueba autenticado como Administrador."""
    auth_client("admin@biblioteca.test", "Admin123!")
    return client


@pytest.fixture
def bibliotecario_client(client, bibliotecario_user, auth_client):
    """Cliente de prueba autenticado como Bibliotecario."""
    auth_client("bibliotecario@biblioteca.test", "Biblio123!")
    return client


@pytest.fixture
def almacenista_client(client, almacenista_user, auth_client):
    """Cliente de prueba autenticado como Almacenista."""
    auth_client("almacenista@biblioteca.test", "Almacen123!")
    return client


@pytest.fixture
def aprendiz_client(client, aprendiz_user, auth_client):
    """Cliente de prueba autenticado como Aprendiz."""
    auth_client("aprendiz@biblioteca.test", "Aprendiz123!")
    return client


# ── Fixtures de Entidades de Dominio ──────────────────────────────────────

@pytest.fixture
def sample_libro(app):
    """Crea y persiste un libro de muestra disponible."""
    libro = Libro(
        titulo="Cien Años de Soledad",
        autor="Gabriel García Márquez",
        genero="Novela",
        codigo_unico="LIB-TEST-001",
        estado="disponible",
        ubicacion="Estante A-1",
        disponible_prestamo=True,
        tiempo_max_prestamo=15,
        descripcion="Edición especial de prueba"
    )
    libro.save()
    db.session.commit()
    return libro


@pytest.fixture
def sample_equipo(app):
    """Crea y persiste un equipo de muestra disponible."""
    equipo = Equipo(
        nombre="Laptop Dell Latitude",
        tipo_equipo="Laptop",
        marca="Dell",
        modelo="5420",
        numero_serie="EQ-TEST-001",
        estado="disponible",
        ubicacion="Almacén Central",
        disponible_prestamo=True,
        tiempo_max_prestamo=7,
        descripcion="Equipo portátil para pruebas"
    )
    equipo.save()
    db.session.commit()
    return equipo


@pytest.fixture
def sample_prestamo_libro(app, sample_libro, aprendiz_user):
    """Crea un préstamo de libro aceptado."""
    ahora = datetime.now(timezone.utc)
    prestamo = PrestamoLibro(
        id_libro=sample_libro.id_libro,
        id_usuario=aprendiz_user.id_usuario,
        estado="aceptado",
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora + timedelta(days=15),
        observaciones="Estudio e investigación"
    )
    prestamo.save()
    sample_libro.estado = "prestado"
    db.session.commit()
    return prestamo


@pytest.fixture
def sample_prestamo_equipo(app, sample_equipo, aprendiz_user):
    """Crea un préstamo de equipo aceptado."""
    ahora = datetime.now(timezone.utc)
    prestamo = Prestamo(
        id_equipo=sample_equipo.id_equipo,
        id_usuario=aprendiz_user.id_usuario,
        estado="aceptado",
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora + timedelta(days=7),
        observaciones="Desarrollo de proyecto"
    )
    prestamo.save()
    sample_equipo.estado = "prestado"
    db.session.commit()
    return prestamo
