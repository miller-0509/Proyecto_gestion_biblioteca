"""
Pruebas unitarias y de integración para el Blueprint de Equipos (equipos).
"""
from app import db
from app.models.equipos import Equipo


def test_lista_equipos_unauthenticated(client):
    """GET /equipos/ sin autenticación debe redirigir a login."""
    response = client.get('/equipos/', follow_redirects=False)
    assert response.status_code == 302


def test_lista_equipos_authenticated(aprendiz_client, sample_equipo):
    """GET /equipos/ con usuario autenticado debe retornar 200."""
    response = aprendiz_client.get('/equipos/')
    assert response.status_code == 200


def test_lista_equipos_filtros(almacenista_client, sample_equipo):
    """GET /equipos/ con filtros de búsqueda, estado y tipo debe responder 200."""
    response = almacenista_client.get('/equipos/?busqueda=Dell&estado=disponible&tipo=Laptop')
    assert response.status_code == 200


def test_crear_equipo_success_almacenista(almacenista_client):
    """POST /equipos/nuevo por almacenista crea el equipo en la BD y redirige."""
    response = almacenista_client.post('/equipos/nuevo', data={
        'nombre': 'Proyector Epson PowerLite',
        'tipo_equipo': 'Proyector',
        'marca': 'Epson',
        'modelo': 'X49',
        'numero_serie': 'EQ-TEST-002',
        'ubicacion': 'Almacén Audiovisual',
        'disponible_prestamo': 'on',
        'tiempo_max_prestamo': '3',
        'descripcion': 'Proyector 3600 lúmenes'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/equipos' in response.headers.get('Location', '')

    equipo = Equipo.query.filter_by(numero_serie='EQ-TEST-002').first()
    assert equipo is not None
    assert equipo.nombre == 'Proyector Epson PowerLite'
    assert equipo.tipo_equipo == 'Proyector'


def test_crear_equipo_forbidden_for_aprendiz(aprendiz_client):
    """POST /equipos/nuevo por aprendiz debe ser denegado."""
    response = aprendiz_client.post('/equipos/nuevo', data={
        'nombre': 'Equipo No Autorizado',
        'tipo_equipo': 'Laptop',
        'numero_serie': 'EQ-NOAUTH-001',
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')

    equipo = Equipo.query.filter_by(numero_serie='EQ-NOAUTH-001').first()
    assert equipo is None


def test_crear_equipo_validation_error(almacenista_client):
    """POST /equipos/nuevo con campos obligatorios vacíos debe fallar."""
    response = almacenista_client.post('/equipos/nuevo', data={
        'nombre': '',
        'tipo_equipo': '',
        'numero_serie': '',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert Equipo.query.filter_by(nombre='').first() is None


def test_crear_equipo_duplicate_serial(almacenista_client, sample_equipo):
    """POST /equipos/nuevo con numero_serie duplicado debe fallar."""
    response = almacenista_client.post('/equipos/nuevo', data={
        'nombre': 'Otro Equipo',
        'tipo_equipo': 'Laptop',
        'numero_serie': sample_equipo.numero_serie,  # Duplicado
    }, follow_redirects=True)

    assert response.status_code == 200
    total = Equipo.query.filter_by(numero_serie=sample_equipo.numero_serie).count()
    assert total == 1


def test_editar_equipo_success(almacenista_client, sample_equipo):
    """POST /equipos/<id>/editar actualiza los datos del equipo."""
    response = almacenista_client.post(f'/equipos/{sample_equipo.id_equipo}/editar', data={
        'nombre': 'Laptop Dell Latitude 5420 (Modificada)',
        'tipo_equipo': sample_equipo.tipo_equipo,
        'marca': sample_equipo.marca,
        'modelo': sample_equipo.modelo,
        'numero_serie': sample_equipo.numero_serie,
        'estado': 'disponible',
        'ubicacion': 'Laboratorio 2',
        'disponible_prestamo': 'on',
        'tiempo_max_prestamo': '10'
    }, follow_redirects=False)

    assert response.status_code == 302
    db.session.refresh(sample_equipo)
    assert sample_equipo.nombre == 'Laptop Dell Latitude 5420 (Modificada)'
    assert sample_equipo.ubicacion == 'Laboratorio 2'


def test_eliminar_equipo_soft_delete(almacenista_client, sample_equipo):
    """POST /equipos/<id>/eliminar marca el equipo como eliminado."""
    response = almacenista_client.post(
        f'/equipos/{sample_equipo.id_equipo}/eliminar',
        follow_redirects=False
    )
    assert response.status_code == 302

    db.session.refresh(sample_equipo)
    assert sample_equipo.eliminado is True


def test_detalle_equipo(aprendiz_client, sample_equipo):
    """GET /equipos/<id> retorna la vista de detalle con código 200."""
    response = aprendiz_client.get(f'/equipos/{sample_equipo.id_equipo}')
    assert response.status_code == 200


def test_detalle_equipo_not_found(aprendiz_client):
    """GET /equipos/<id_inexistente> debe retornar 404."""
    response = aprendiz_client.get('/equipos/999999')
    assert response.status_code == 404
