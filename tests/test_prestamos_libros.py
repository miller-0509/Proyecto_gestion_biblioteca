"""
Pruebas unitarias y de integración para el Blueprint de Préstamos de Libros (prestamos_libros).
"""
import pytest
from app.models.prestamos_libros import PrestamoLibro
from app.models.libros import Libro
from app import db


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
