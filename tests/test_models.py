"""
Pruebas unitarias para modelos y métodos del dominio de la aplicación.
"""
from datetime import timedelta

from app import db
from app.models.equipos import Equipo
from app.models.libros import Libro
from app.models.multas import Multa
from app.models.renovaciones import RenovacionEquipo, RenovacionLibro
from app.models.usuarios import Usuario


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


class TestMultaModel:
    """Pruebas del modelo Multa."""

    def test_multa_creacion_equipo(self, app, aprendiz_user, sample_prestamo_equipo):
        """Una multa de equipo debe guardar el préstamo y el usuario asociados."""
        multa = Multa(
            tipo_recurso='equipo',
            id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
            id_usuario=aprendiz_user.id_usuario,
            dias_retraso=3,
            dias_suspension=3,
            estado='activa'
        )
        multa.save()
        db.session.commit()

        assert multa.id_multa is not None
        assert multa.estado == 'activa'
        assert multa.dias_retraso == 3
        assert multa.dias_suspension == 3
        assert multa.usuario.correo == aprendiz_user.correo
        assert multa.prestamo_equipo.id_prestamo == sample_prestamo_equipo.id_prestamo

    def test_multa_creacion_libro(self, app, aprendiz_user, sample_prestamo_libro):
        """Una multa de libro debe guardar el préstamo de libro asociado."""
        multa = Multa(
            tipo_recurso='libro',
            id_prestamo_libro=sample_prestamo_libro.id_prestamo_libro,
            id_usuario=aprendiz_user.id_usuario,
            dias_retraso=5,
            dias_suspension=5,
            estado='acumulando'
        )
        multa.save()
        db.session.commit()

        assert multa.tipo_recurso == 'libro'
        assert multa.estado == 'acumulando'
        assert multa.prestamo_libro.id_prestamo_libro == sample_prestamo_libro.id_prestamo_libro
        assert multa.fecha_generacion is not None

    def test_multa_defaults(self, app, aprendiz_user):
        """Los valores por defecto de una multa deben ser acumulando y cero días."""
        multa = Multa(
            tipo_recurso='equipo',
            id_usuario=aprendiz_user.id_usuario
        )
        multa.save()
        db.session.commit()

        assert multa.estado == 'acumulando'
        assert multa.dias_retraso == 0
        assert multa.dias_suspension == 0
        assert multa.fecha_generacion is not None

    def test_multa_to_dict(self, app, aprendiz_user, sample_prestamo_equipo):
        """to_dict debe serializar los campos principales y el nombre del usuario."""
        multa = Multa(
            tipo_recurso='equipo',
            id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
            id_usuario=aprendiz_user.id_usuario,
            dias_retraso=4,
            dias_suspension=4,
            estado='activa'
        )
        multa.save()
        db.session.commit()

        data = multa.to_dict()
        assert data['tipo_recurso'] == 'equipo'
        assert data['estado'] == 'activa'
        assert data['dias_suspension'] == 4
        assert data['usuario_nombres'] == aprendiz_user.nombre_completo()

    def test_multa_relacion_inversa_usuario(self, app, aprendiz_user):
        """backref 'multas' debe permitir listar multas desde el usuario."""
        multa1 = Multa(tipo_recurso='equipo', id_usuario=aprendiz_user.id_usuario, estado='acumulando')
        multa2 = Multa(tipo_recurso='libro', id_usuario=aprendiz_user.id_usuario, estado='activa')
        multa1.save()
        multa2.save()
        db.session.commit()

        assert len(aprendiz_user.multas) == 2
        assert {m.estado for m in aprendiz_user.multas} == {'acumulando', 'activa'}


class TestRenovacionModel:
    """Pruebas de los modelos RenovacionEquipo y RenovacionLibro."""

    def test_renovacion_equipo_creacion(self, app, aprendiz_user, sample_prestamo_equipo):
        """Una renovación de equipo debe persistir motivo y fechas esperadas."""
        renovacion = RenovacionEquipo(
            id_prestamo=sample_prestamo_equipo.id_prestamo,
            id_usuario=aprendiz_user.id_usuario,
            fecha_esperada_original=sample_prestamo_equipo.fecha_devolucion_esperada,
            fecha_esperada_nueva=sample_prestamo_equipo.fecha_devolucion_esperada + timedelta(days=7),
            motivo_solicitud='Prórroga para finalizar proyecto',
            estado='pendiente'
        )
        renovacion.save()
        db.session.commit()

        assert renovacion.id_renovacion is not None
        assert renovacion.estado == 'pendiente'
        assert renovacion.motivo_solicitud == 'Prórroga para finalizar proyecto'
        assert renovacion.prestamo.id_prestamo == sample_prestamo_equipo.id_prestamo
        assert renovacion.fecha_solicitud is not None

    def test_renovacion_equipo_backref_historial(self, app, aprendiz_user, sample_prestamo_equipo):
        """backref 'historial_renovaciones' debe listar renovaciones del préstamo."""
        renovacion = RenovacionEquipo(
            id_prestamo=sample_prestamo_equipo.id_prestamo,
            id_usuario=aprendiz_user.id_usuario,
            fecha_esperada_original=sample_prestamo_equipo.fecha_devolucion_esperada,
            fecha_esperada_nueva=sample_prestamo_equipo.fecha_devolucion_esperada + timedelta(days=7),
            motivo_solicitud='Prórroga',
            estado='aprobada'
        )
        renovacion.save()
        db.session.commit()

        assert len(sample_prestamo_equipo.historial_renovaciones) == 1
        assert sample_prestamo_equipo.historial_renovaciones[0].estado == 'aprobada'

    def test_renovacion_libro_creacion(self, app, aprendiz_user, sample_prestamo_libro):
        """Una renovación de libro debe persistir motivo y estado."""
        renovacion = RenovacionLibro(
            id_prestamo_libro=sample_prestamo_libro.id_prestamo_libro,
            id_usuario=aprendiz_user.id_usuario,
            fecha_esperada_original=sample_prestamo_libro.fecha_devolucion_esperada,
            fecha_esperada_nueva=sample_prestamo_libro.fecha_devolucion_esperada + timedelta(days=15),
            motivo_solicitud='Continuar lectura para investigación',
            estado='pendiente'
        )
        renovacion.save()
        db.session.commit()

        assert renovacion.id_renovacion is not None
        assert renovacion.estado == 'pendiente'
        assert renovacion.prestamo_libro.id_prestamo_libro == sample_prestamo_libro.id_prestamo_libro
        assert renovacion.fecha_solicitud is not None

    def test_renovacion_libro_backref_historial(self, app, aprendiz_user, sample_prestamo_libro):
        """backref 'historial_renovaciones' debe listar renovaciones del préstamo de libro."""
        renovacion = RenovacionLibro(
            id_prestamo_libro=sample_prestamo_libro.id_prestamo_libro,
            id_usuario=aprendiz_user.id_usuario,
            fecha_esperada_original=sample_prestamo_libro.fecha_devolucion_esperada,
            fecha_esperada_nueva=sample_prestamo_libro.fecha_devolucion_esperada + timedelta(days=15),
            motivo_solicitud='Prórroga de lectura',
            estado='rechazada',
            motivo_rechazo='Libro requerido por otro curso'
        )
        renovacion.save()
        db.session.commit()

        assert len(sample_prestamo_libro.historial_renovaciones) == 1
        assert sample_prestamo_libro.historial_renovaciones[0].motivo_rechazo == 'Libro requerido por otro curso'
