"""
Pruebas unitarias y de integración para el Blueprint de Libros (libros).
"""
import pytest
from app.models.libros import Libro
from app import db


def test_lista_libros_unauthenticated(client):
    """GET /libros/ sin autenticación debe redirigir a login."""
    response = client.get('/libros/', follow_redirects=False)
    assert response.status_code == 302


def test_lista_libros_authenticated(aprendiz_client, sample_libro):
    """GET /libros/ con sesión activa debe retornar 200."""
    response = aprendiz_client.get('/libros/')
    assert response.status_code == 200


def test_lista_libros_filtros(bibliotecario_client, sample_libro):
    """GET /libros/ con filtros de búsqueda, estado y género debe responder 200."""
    response = bibliotecario_client.get('/libros/?busqueda=Cien&estado=disponible&genero=Novela')
    assert response.status_code == 200


def test_crear_libro_success_bibliotecario(bibliotecario_client):
    """POST /libros/nuevo por bibliotecario debe crear el libro en la BD y redirigir."""
    response = bibliotecario_client.post('/libros/nuevo', data={
        'titulo': 'Don Quijote de la Mancha',
        'autor': 'Miguel de Cervantes',
        'genero': 'Clásico',
        'codigo_unico': 'LIB-TEST-002',
        'ubicacion': 'Estante B-3',
        'disponible_prestamo': 'on',
        'tiempo_max_prestamo': '15',
        'descripcion': 'Libro clásico de la literatura española'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/libros' in response.headers.get('Location', '')

    libro = Libro.query.filter_by(codigo_unico='LIB-TEST-002').first()
    assert libro is not None
    assert libro.titulo == 'Don Quijote de la Mancha'
    assert libro.autor == 'Miguel de Cervantes'
    assert libro.disponible_prestamo is True


def test_crear_libro_forbidden_for_aprendiz(aprendiz_client):
    """POST /libros/nuevo por aprendiz debe ser denegado por falta de permisos."""
    response = aprendiz_client.post('/libros/nuevo', data={
        'titulo': 'Libro No Autorizado',
        'autor': 'Autor Test',
        'genero': 'Test',
        'codigo_unico': 'LIB-NOAUTH-001',
    }, follow_redirects=False)

    # El decorador gestion_libros_required redirige al dashboard
    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')

    libro = Libro.query.filter_by(codigo_unico='LIB-NOAUTH-001').first()
    assert libro is None


def test_crear_libro_validation_error(bibliotecario_client):
    """POST /libros/nuevo con campos obligatorios vacíos debe fallar la validación."""
    response = bibliotecario_client.post('/libros/nuevo', data={
        'titulo': '',
        'autor': '',
        'genero': '',
        'codigo_unico': '',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert Libro.query.filter_by(titulo='').first() is None


def test_crear_libro_duplicate_code(bibliotecario_client, sample_libro):
    """POST /libros/nuevo con un codigo_unico existente debe rechazar el registro."""
    response = bibliotecario_client.post('/libros/nuevo', data={
        'titulo': 'Otro Libro',
        'autor': 'Otro Autor',
        'genero': 'Drama',
        'codigo_unico': sample_libro.codigo_unico,  # Duplicado
    }, follow_redirects=True)

    assert response.status_code == 200
    total = Libro.query.filter_by(codigo_unico=sample_libro.codigo_unico).count()
    assert total == 1


def test_editar_libro_success(bibliotecario_client, sample_libro):
    """POST /libros/<id>/editar actualiza los campos del libro."""
    response = bibliotecario_client.post(f'/libros/{sample_libro.id_libro}/editar', data={
        'titulo': 'Cien Años de Soledad (Edición Ilustrada)',
        'autor': sample_libro.autor,
        'genero': sample_libro.genero,
        'codigo_unico': sample_libro.codigo_unico,
        'estado': 'disponible',
        'ubicacion': 'Estante A-2',
        'disponible_prestamo': 'on',
        'tiempo_max_prestamo': '20'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_libro)
    assert sample_libro.titulo == 'Cien Años de Soledad (Edición Ilustrada)'
    assert sample_libro.ubicacion == 'Estante A-2'
    assert sample_libro.tiempo_max_prestamo == 20


def test_eliminar_libro_soft_delete(bibliotecario_client, sample_libro):
    """POST /libros/<id>/eliminar debe marcar el libro como eliminado lógicamente."""
    response = bibliotecario_client.post(
        f'/libros/{sample_libro.id_libro}/eliminar',
        follow_redirects=False
    )
    assert response.status_code == 302

    db.session.refresh(sample_libro)
    assert sample_libro.eliminado is True


def test_detalle_libro(aprendiz_client, sample_libro):
    """GET /libros/<id> debe retornar la ficha del libro con código 200."""
    response = aprendiz_client.get(f'/libros/{sample_libro.id_libro}')
    assert response.status_code == 200


def test_detalle_libro_not_found(aprendiz_client):
    """GET /libros/<id_inexistente> debe retornar código 404."""
    response = aprendiz_client.get('/libros/999999')
    assert response.status_code == 404
