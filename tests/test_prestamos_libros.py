"""
Pruebas unitarias y de integración para el Blueprint de Préstamos de Libros (prestamos_libros).
"""
from datetime import UTC, datetime, timedelta

from app import db
from app.models.prestamos_libros import PrestamoLibro
from app.models.renovaciones import RenovacionLibro


def test_lista_prestamos_libros_unauthenticated(client):
    """GET /prestamos-libros/lista sin login debe redirigir a login."""
    response = client.get('/prestamos-libros/lista', follow_redirects=False)
    assert response.status_code == 302


def test_lista_prestamos_libros_aprendiz(aprendiz_client, sample_prestamo_libro):
    """GET /prestamos-libros/lista para aprendiz debe retornar 200 con su historial."""
    response = aprendiz_client.get('/prestamos-libros/lista')
    assert response.status_code == 200


def test_lista_prestamos_libros_bibliotecario(bibliotecario_client, sample_prestamo_libro):
    """GET /prestamos-libros/lista para bibliotecario debe retornar 200."""
    response = bibliotecario_client.get('/prestamos-libros/lista')
    assert response.status_code == 200


def test_crear_prestamo_libro_bibliotecario_success(bibliotecario_client, sample_libro, aprendiz_user):
    """POST /prestamos-libros/crear por bibliotecario crea el préstamo y marca el libro como prestado."""
    response = bibliotecario_client.post('/prestamos-libros/crear', data={
        'id_libro': sample_libro.id_libro,
        'id_usuario': aprendiz_user.id_usuario,
        'dias_prestamo': 15,
        'observaciones': 'Préstamo académico'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/prestamos-libros/lista' in response.headers.get('Location', '')

    db.session.refresh(sample_libro)
    assert sample_libro.estado == 'prestado'

    prestamo = PrestamoLibro.query.filter_by(
        id_libro=sample_libro.id_libro,
        id_usuario=aprendiz_user.id_usuario
    ).first()
    assert prestamo is not None
    assert prestamo.estado == 'aceptado'


def test_solicitar_prestamo_libro_aprendiz(aprendiz_client, sample_libro):
    """POST /prestamos-libros/crear por aprendiz registra solicitud de préstamo."""
    response = aprendiz_client.post('/prestamos-libros/crear', data={
        'id_libro': sample_libro.id_libro,
        'observaciones': 'Necesario para taller de lectura'
    }, follow_redirects=False)

    assert response.status_code == 302
    prestamo = PrestamoLibro.query.filter_by(id_libro=sample_libro.id_libro).first()
    assert prestamo is not None
    assert prestamo.estado == 'pendiente'


# ── CICLO DE VIDA: ACEPTAR / RECHAZAR / DEVOLVER ───────────────────────────

def test_aceptar_prestamo_libro_bibliotecario(bibliotecario_client, sample_prestamo_libro_pendiente, sample_libro):
    """POST /prestamos-libros/<id>/aceptar por bibliotecario acepta el préstamo."""
    pid = sample_prestamo_libro_pendiente.id_prestamo_libro
    response = bibliotecario_client.post(f'/prestamos-libros/{pid}/aceptar', follow_redirects=False)

    assert response.status_code == 302
    assert '/prestamos-libros/lista' in response.headers.get('Location', '')

    db.session.refresh(sample_prestamo_libro_pendiente)
    db.session.refresh(sample_libro)
    assert sample_prestamo_libro_pendiente.estado == 'aceptado'
    assert sample_prestamo_libro_pendiente.fecha_aprobacion is not None
    assert sample_libro.estado == 'prestado'


def test_rechazar_prestamo_libro_bibliotecario(bibliotecario_client, sample_prestamo_libro_pendiente, sample_libro):
    """POST /prestamos-libros/<id>/rechazar por bibliotecario rechaza y guarda la razón."""
    pid = sample_prestamo_libro_pendiente.id_prestamo_libro
    response = bibliotecario_client.post(f'/prestamos-libros/{pid}/rechazar', data={
        'razon_rechazo': 'El libro tiene reservas previas.'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_prestamo_libro_pendiente)
    assert sample_prestamo_libro_pendiente.estado == 'rechazado'
    assert sample_prestamo_libro_pendiente.razon_rechazo == 'El libro tiene reservas previas.'
    assert sample_libro.estado == 'disponible'


def test_devolver_prestamo_libro_bibliotecario(bibliotecario_client, sample_prestamo_libro, sample_libro):
    """POST /prestamos-libros/<id>/devolver por bibliotecario registra la devolución."""
    pid = sample_prestamo_libro.id_prestamo_libro
    response = bibliotecario_client.post(f'/prestamos-libros/{pid}/devolver', data={
        'estado_fisico': 'bueno',
        'estado_final': 'disponible',
        'observacion_devolucion': 'Libro en buen estado'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/prestamos-libros/lista' in response.headers.get('Location', '')

    db.session.refresh(sample_prestamo_libro)
    db.session.refresh(sample_libro)
    assert sample_prestamo_libro.estado == 'devuelto'
    assert sample_prestamo_libro.fecha_devolucion_real is not None
    assert sample_prestamo_libro.estado_fisico_devolucion == 'bueno'
    assert sample_libro.estado == 'disponible'


def test_devolver_prestamo_libro_estado_fisico_invalido(bibliotecario_client, sample_prestamo_libro):
    """Devolución con estado físico inválido debe ser rechazada."""
    pid = sample_prestamo_libro.id_prestamo_libro
    response = bibliotecario_client.post(f'/prestamos-libros/{pid}/devolver', data={
        'estado_fisico': 'inexistente',
        'estado_final': 'disponible',
        'observacion_devolucion': 'Prueba inválida'
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(sample_prestamo_libro)
    assert sample_prestamo_libro.estado == 'aceptado'


# ── DETALLE DE PRÉSTAMO ────────────────────────────────────────────────────

def test_detalle_prestamo_libro_bibliotecario(bibliotecario_client, sample_prestamo_libro):
    """GET /prestamos-libros/<id> para bibliotecario debe retornar 200."""
    response = bibliotecario_client.get(f'/prestamos-libros/{sample_prestamo_libro.id_prestamo_libro}')
    assert response.status_code == 200


def test_detalle_prestamo_libro_propietario(aprendiz_client, sample_prestamo_libro):
    """El usuario propietario debe poder ver su préstamo de libro."""
    response = aprendiz_client.get(f'/prestamos-libros/{sample_prestamo_libro.id_prestamo_libro}')
    assert response.status_code == 200


def test_detalle_prestamo_libro_denegado_otro_usuario(aprendiz_client, sample_prestamo_libro, instructor_user):
    """Un usuario que no es propietario ni bibliotecario no debe ver el préstamo ajeno."""
    ahora = datetime.now(UTC)
    prestamo_ajeno = PrestamoLibro(
        id_libro=sample_prestamo_libro.id_libro,
        id_usuario=instructor_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_devolucion_esperada=ahora + timedelta(days=15)
    )
    prestamo_ajeno.save()
    db.session.commit()

    response = aprendiz_client.get(f'/prestamos-libros/{prestamo_ajeno.id_prestamo_libro}', follow_redirects=False)
    assert response.status_code == 302
    assert '/prestamos-libros/lista' in response.headers.get('Location', '')


# ── RENOVACIONES ───────────────────────────────────────────────────────────

def test_solicitar_renovacion_libro_aprendiz(aprendiz_client, sample_prestamo_libro, aprendiz_user):
    """POST /prestamos-libros/<id>/renovar por aprendiz crea la solicitud de renovación."""
    pid = sample_prestamo_libro.id_prestamo_libro
    response = aprendiz_client.post(f'/prestamos-libros/{pid}/renovar', data={
        'motivo_renovacion': 'Necesito más tiempo para la lectura.'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_prestamo_libro)
    assert sample_prestamo_libro.estado_renovacion == 'pendiente'

    renovacion = RenovacionLibro.query.filter_by(id_prestamo_libro=pid).first()
    assert renovacion is not None
    assert renovacion.estado == 'pendiente'
    assert renovacion.id_usuario == aprendiz_user.id_usuario
    assert renovacion.motivo_solicitud == 'Necesito más tiempo para la lectura.'


def test_solicitar_renovacion_libro_sin_motivo(aprendiz_client, sample_prestamo_libro):
    """Solicitar renovación sin motivo debe ser rechazada."""
    pid = sample_prestamo_libro.id_prestamo_libro
    response = aprendiz_client.post(f'/prestamos-libros/{pid}/renovar', data={
        'motivo_renovacion': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(sample_prestamo_libro)
    assert sample_prestamo_libro.estado_renovacion is None


def test_aprobar_renovacion_libro_bibliotecario(bibliotecario_client, aprendiz_client, sample_prestamo_libro):
    """POST /prestamos-libros/<id>/procesar_renovacion con accion=aprobar extiende la fecha."""
    pid = sample_prestamo_libro.id_prestamo_libro
    fecha_original = sample_prestamo_libro.fecha_devolucion_esperada

    aprendiz_client.post(f'/prestamos-libros/{pid}/renovar', data={
        'motivo_renovacion': 'Necesito más tiempo.'
    }, follow_redirects=False)

    response = bibliotecario_client.post(f'/prestamos-libros/{pid}/procesar_renovacion', data={
        'accion': 'aprobar'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_prestamo_libro)
    assert sample_prestamo_libro.estado_renovacion == 'aprobada'
    assert sample_prestamo_libro.renovaciones_aplicadas == 1
    assert sample_prestamo_libro.fecha_devolucion_esperada > fecha_original


def test_rechazar_renovacion_libro_bibliotecario(bibliotecario_client, aprendiz_client, sample_prestamo_libro):
    """POST /prestamos-libros/<id>/procesar_renovacion con accion=rechazar rechaza la renovación."""
    pid = sample_prestamo_libro.id_prestamo_libro
    fecha_original = sample_prestamo_libro.fecha_devolucion_esperada

    aprendiz_client.post(f'/prestamos-libros/{pid}/renovar', data={
        'motivo_renovacion': 'Necesito más tiempo.'
    }, follow_redirects=False)

    response = bibliotecario_client.post(f'/prestamos-libros/{pid}/procesar_renovacion', data={
        'accion': 'rechazar',
        'motivo_rechazo': 'El libro se necesita para otro curso.'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_prestamo_libro)
    assert sample_prestamo_libro.estado_renovacion == 'rechazada'
    assert sample_prestamo_libro.renovaciones_aplicadas == 0
    assert sample_prestamo_libro.fecha_devolucion_esperada == fecha_original
