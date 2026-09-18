"""
Pruebas unitarias para modelos y métodos del dominio de la aplicación.
"""
import pytest
from app.models.usuarios import Usuario
from app.models.libros import Libro
from app.models.equipos import Equipo
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro
from app import db


class TestUsuarioModel:
    """Pruebas del modelo Usuario."""

    def test_password_hashing(self, app):
        """Las contraseñas deben estar hasheadas y validarse correctamente."""
        user = Usuario(
            nombres="Pedro",
            apellidos="Alvarez",
            correo="pedro@test.com",
            rol="aprendiz"
        )
        user.set_password("MiClaveSegura123!")
        assert user.password != "MiClaveSegura123!"
        assert user.check_password("MiClaveSegura123!") is True
        assert user.check_password("ClaveErronea") is False

    def test_is_active_property(self, app):
        """is_active debe reflejar si el estado es 'activo'."""
        activo = Usuario(nombres="A", apellidos="A", correo="a@test.com", rol="aprendiz", estado="activo")
        inactivo = Usuario(nombres="B", apellidos="B", correo="b@test.com", rol="aprendiz", estado="inactivo")
        bloqueado = Usuario(nombres="C", apellidos="C", correo="c@test.com", rol="aprendiz", estado="bloqueado")

        assert activo.is_active is True
        assert inactivo.is_active is False
        assert bloqueado.is_active is False

    def test_limite_prestamos(self, app):
        """limite_prestamos debe devolver la cuota asignada por rol."""
        aprendiz = Usuario(nombres="A", apellidos="A", correo="a@test.com", rol="aprendiz")
        instructor = Usuario(nombres="B", apellidos="B", correo="b@test.com", rol="instructor")
        admin = Usuario(nombres="C", apellidos="C", correo="c@test.com", rol="administrador")

        assert aprendiz.limite_prestamos == 3
        assert instructor.limite_prestamos == 8
        assert admin.limite_prestamos == 999

    def test_nombre_completo(self, app):
        """nombre_completo debe concatenar nombres y apellidos."""
        user = Usuario(nombres="Laura", apellidos="Gomez", correo="laura@test.com", rol="aprendiz")
        assert user.nombre_completo() == "Laura Gomez"

    def test_validate_registro_rules(self, app):
        """validate_registro debe detectar campos faltantes, correos inválidos y contraseñas débiles."""
        # Válido
        assert len(Usuario.validate_registro("Ana", "Rios", "ana@test.com", "ClaveSegura1!", "aprendiz")) == 0

        # Inválido por contraseña corta y sin números
        errors = Usuario.validate_registro("Ana", "Rios", "ana@test.com", "corta", "aprendiz")
        assert len(errors) > 0

        # Inválido por correo mal formado
        errors = Usuario.validate_registro("Ana", "Rios", "correo-invalido", "ClaveSegura1!", "aprendiz")
        assert any("formato" in e.lower() for e in errors)

    def test_usuario_to_dict(self, app):
        """to_dict debe serializar los campos principales."""
        user = Usuario(id_usuario=1, nombres="Test", apellidos="User", correo="test@test.com", rol="aprendiz", estado="activo")
        data = user.to_dict()
        assert data['correo'] == "test@test.com"
        assert data['rol'] == "aprendiz"
        assert 'password' not in data


class TestLibroModel:
    """Pruebas del modelo Libro."""

    def test_validate_libro(self, app):
        """validate_libro debe exigir campos mínimos."""
        assert len(Libro.validate_libro("Título", "Autor", "Género", "COD-001")) == 0
        errors = Libro.validate_libro("", "", "", "")
        assert len(errors) >= 4

    def test_libro_to_dict(self, sample_libro):
        """to_dict debe incluir el id y metadatos."""
        data = sample_libro.to_dict()
        assert data['titulo'] == sample_libro.titulo
        assert data['codigo_unico'] == sample_libro.codigo_unico

    def test_tiene_prestamo_activo(self, sample_prestamo_libro, sample_libro):
        """tiene_prestamo_activo debe ser True cuando el libro está prestado."""
        assert sample_libro.tiene_prestamo_activo is True


class TestEquipoModel:
    """Pruebas del modelo Equipo."""

    def test_validate_equipo(self, app):
        """validate_equipo debe validar nombre, tipo y serial."""
        assert len(Equipo.validate_equipo("Laptop", "Laptop", "SER-001")) == 0
        errors = Equipo.validate_equipo("", "", "")
        assert len(errors) >= 3

    def test_equipo_to_dict(self, sample_equipo):
        """to_dict debe estructurar los datos del equipo."""
        data = sample_equipo.to_dict()
        assert data['nombre'] == sample_equipo.nombre
        assert data['numero_serie'] == sample_equipo.numero_serie
