"""
Pruebas unitarias y de integración para el Blueprint de Préstamos de Equipos (prestamos).
"""
from datetime import UTC, datetime, timedelta

from app import db
from app.models.prestamos import Prestamo
from app.models.renovaciones import RenovacionEquipo


def test_lista_prestamos_unauthenticated(client):
    """GET /prestamos/lista sin login debe redirigir a login."""
    response = client.get('/prestamos/lista', follow_redirects=False)
    assert response.status_code == 302


def test_lista_prestamos_aprendiz(aprendiz_client, sample_prestamo_equipo):
    """GET /prestamos/lista para aprendiz debe retornar 200 con su lista."""
    response = aprendiz_client.get('/prestamos/lista')
    assert response.status_code == 200


def test_lista_prestamos_admin(admin_client, sample_prestamo_equipo):
    """GET /prestamos/lista para administrador debe retornar 200 con gestión completa."""
    response = admin_client.get('/prestamos/lista')
    assert response.status_code == 200


def test_crear_prestamo_admin_success(admin_client, sample_equipo, aprendiz_user):
    """POST /prestamos/crear por admin debe generar préstamo aceptado y cambiar estado del equipo."""
    response = admin_client.post('/prestamos/crear', data={
        'id_equipo': sample_equipo.id_equipo,
        'id_usuario': aprendiz_user.id_usuario,
        'dias_prestamo': 7,
        'observaciones': 'Préstamo para proyecto formativo'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/prestamos/lista' in response.headers.get('Location', '')

    db.session.refresh(sample_equipo)
    assert sample_equipo.estado == 'prestado'

    prestamo = Prestamo.query.filter_by(
        id_equipo=sample_equipo.id_equipo,
        id_usuario=aprendiz_user.id_usuario
    ).first()
    assert prestamo is not None
    assert prestamo.estado == 'aceptado'


def test_crear_prestamo_unavailable_equipo(admin_client, sample_equipo, aprendiz_user):
    """POST /prestamos/crear con equipo no disponible debe rechazar la creación."""
    sample_equipo.estado = 'prestado'
    db.session.commit()

    response = admin_client.post('/prestamos/crear', data={
        'id_equipo': sample_equipo.id_equipo,
        'id_usuario': aprendiz_user.id_usuario,
        'dias_prestamo': 7,
    }, follow_redirects=True)

    assert response.status_code == 200
    total = Prestamo.query.filter_by(id_equipo=sample_equipo.id_equipo).count()
    assert total == 0


# ── CICLO DE VIDA: ACEPTAR / RECHAZAR / DEVOLVER ───────────────────────────

def test_aceptar_prestamo_equipo_admin(admin_client, sample_prestamo_equipo_pendiente, sample_equipo):
    """POST /prestamos/<id>/aceptar por admin acepta el préstamo y marca el equipo prestado."""
    pid = sample_prestamo_equipo_pendiente.id_prestamo
    response = admin_client.post(f'/prestamos/{pid}/aceptar', follow_redirects=False)

    assert response.status_code == 302
    assert '/prestamos/lista' in response.headers.get('Location', '')

    db.session.refresh(sample_prestamo_equipo_pendiente)
    db.session.refresh(sample_equipo)
    assert sample_prestamo_equipo_pendiente.estado == 'aceptado'
    assert sample_prestamo_equipo_pendiente.fecha_aprobacion is not None
    assert sample_equipo.estado == 'prestado'


def test_aceptar_prestamo_equipo_not_pendiente(admin_client, sample_prestamo_equipo):
    """Aceptar un préstamo que no está pendiente debe ser rechazado."""
    pid = sample_prestamo_equipo.id_prestamo
    response = admin_client.post(f'/prestamos/{pid}/aceptar', follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(sample_prestamo_equipo)
    assert sample_prestamo_equipo.estado == 'aceptado'


def test_rechazar_prestamo_equipo_admin(admin_client, sample_prestamo_equipo_pendiente, sample_equipo):
    """POST /prestamos/<id>/rechazar por admin rechaza y guarda la razón."""
    pid = sample_prestamo_equipo_pendiente.id_prestamo
    response = admin_client.post(f'/prestamos/{pid}/rechazar', data={
        'razon_rechazo': 'El equipo está reservado para otro proyecto.'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/prestamos/lista' in response.headers.get('Location', '')

    db.session.refresh(sample_prestamo_equipo_pendiente)
    assert sample_prestamo_equipo_pendiente.estado == 'rechazado'
    assert sample_prestamo_equipo_pendiente.razon_rechazo == 'El equipo está reservado para otro proyecto.'
    assert sample_equipo.estado == 'disponible'


def test_devolver_prestamo_equipo_admin(admin_client, sample_prestamo_equipo, sample_equipo):
    """POST /prestamos/<id>/devolver por admin registra la devolución y libera el equipo."""
    pid = sample_prestamo_equipo.id_prestamo
    response = admin_client.post(f'/prestamos/{pid}/devolver', data={
        'estado_fisico': 'bueno',
        'estado_final': 'disponible',
        'observacion_devolucion': 'Equipo en buen estado'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/prestamos/lista' in response.headers.get('Location', '')

    db.session.refresh(sample_prestamo_equipo)
    db.session.refresh(sample_equipo)
    assert sample_prestamo_equipo.estado == 'devuelto'
    assert sample_prestamo_equipo.fecha_devolucion_real is not None
    assert sample_prestamo_equipo.estado_fisico_devolucion == 'bueno'
    assert sample_equipo.estado == 'disponible'


def test_devolver_prestamo_equipo_requiere_observacion(admin_client, sample_prestamo_equipo):
    """Devolución sin observación debe ser rechazada."""
    pid = sample_prestamo_equipo.id_prestamo
    response = admin_client.post(f'/prestamos/{pid}/devolver', data={
        'estado_fisico': 'bueno',
        'estado_final': 'disponible',
        'observacion_devolucion': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(sample_prestamo_equipo)
    assert sample_prestamo_equipo.estado == 'aceptado'


# ── DETALLE DE PRÉSTAMO ────────────────────────────────────────────────────

def test_detalle_prestamo_equipo_admin(admin_client, sample_prestamo_equipo):
    """GET /prestamos/<id> para admin debe retornar 200."""
    response = admin_client.get(f'/prestamos/{sample_prestamo_equipo.id_prestamo}')
    assert response.status_code == 200


def test_detalle_prestamo_equipo_propietario(aprendiz_client, sample_prestamo_equipo):
    """El usuario propietario debe poder ver su préstamo."""
    response = aprendiz_client.get(f'/prestamos/{sample_prestamo_equipo.id_prestamo}')
    assert response.status_code == 200


def test_detalle_prestamo_equipo_denegado_otro_usuario(aprendiz_client, sample_prestamo_equipo, instructor_user):
    """Un usuario que no es propietario ni admin no debe ver el préstamo ajeno."""
    ahora = datetime.now(UTC)
    prestamo_ajeno = Prestamo(
        id_equipo=sample_prestamo_equipo.id_equipo,
        id_usuario=instructor_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_devolucion_esperada=ahora + timedelta(days=7)
    )
    prestamo_ajeno.save()
    db.session.commit()

    response = aprendiz_client.get(f'/prestamos/{prestamo_ajeno.id_prestamo}', follow_redirects=False)
    assert response.status_code == 302
    assert '/prestamos/lista' in response.headers.get('Location', '')


# ── RENOVACIONES ───────────────────────────────────────────────────────────

def test_solicitar_renovacion_equipo_aprendiz(aprendiz_client, sample_prestamo_equipo, aprendiz_user):
    """POST /prestamos/<id>/renovar por aprendiz crea la solicitud de renovación."""
    pid = sample_prestamo_equipo.id_prestamo
    response = aprendiz_client.post(f'/prestamos/{pid}/renovar', data={
        'motivo_renovacion': 'Necesito más tiempo para el proyecto.'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_prestamo_equipo)
    assert sample_prestamo_equipo.estado_renovacion == 'pendiente'

    renovacion = RenovacionEquipo.query.filter_by(id_prestamo=pid).first()
    assert renovacion is not None
    assert renovacion.estado == 'pendiente'
    assert renovacion.id_usuario == aprendiz_user.id_usuario
    assert renovacion.motivo_solicitud == 'Necesito más tiempo para el proyecto.'


def test_solicitar_renovacion_requiere_motivo(aprendiz_client, sample_prestamo_equipo):
    """Solicitar renovación sin motivo debe ser rechazada."""
    pid = sample_prestamo_equipo.id_prestamo
    response = aprendiz_client.post(f'/prestamos/{pid}/renovar', data={
        'motivo_renovacion': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(sample_prestamo_equipo)
    assert sample_prestamo_equipo.estado_renovacion is None


def test_aprobar_renovacion_equipo_admin(admin_client, aprendiz_client, sample_prestamo_equipo):
    """POST /prestamos/<id>/procesar_renovacion con accion=aprobar extiende la fecha."""
    pid = sample_prestamo_equipo.id_prestamo
    fecha_original = sample_prestamo_equipo.fecha_devolucion_esperada

    # El aprendiz solicita primero
    aprendiz_client.post(f'/prestamos/{pid}/renovar', data={
        'motivo_renovacion': 'Necesito más tiempo.'
    }, follow_redirects=False)

    response = admin_client.post(f'/prestamos/{pid}/procesar_renovacion', data={
        'accion': 'aprobar'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_prestamo_equipo)
    assert sample_prestamo_equipo.estado_renovacion == 'aprobada'
    assert sample_prestamo_equipo.renovaciones_aplicadas == 1
    assert sample_prestamo_equipo.fecha_devolucion_esperada > fecha_original


def test_rechazar_renovacion_equipo_admin(admin_client, aprendiz_client, sample_prestamo_equipo):
    """POST /prestamos/<id>/procesar_renovacion con accion=rechazar rechaza la renovación."""
    pid = sample_prestamo_equipo.id_prestamo
    fecha_original = sample_prestamo_equipo.fecha_devolucion_esperada

    aprendiz_client.post(f'/prestamos/{pid}/renovar', data={
        'motivo_renovacion': 'Necesito más tiempo.'
    }, follow_redirects=False)

    response = admin_client.post(f'/prestamos/{pid}/procesar_renovacion', data={
        'accion': 'rechazar',
        'motivo_rechazo': 'El equipo se necesita en el almacén.'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_prestamo_equipo)
    assert sample_prestamo_equipo.estado_renovacion == 'rechazada'
    assert sample_prestamo_equipo.renovaciones_aplicadas == 0
    assert sample_prestamo_equipo.fecha_devolucion_esperada == fecha_original
