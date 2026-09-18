"""
Pruebas unitarias y de integración para el Blueprint de Préstamos de Equipos (prestamos).
"""
import pytest
from app.models.prestamos import Prestamo
from app.models.equipos import Equipo
from app import db


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
