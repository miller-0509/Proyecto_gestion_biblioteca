"""
Pruebas unitarias y de integración para el Blueprint de Autenticación (auth).
"""
from app.models.usuarios import Usuario


def test_health_check(client):
    """El endpoint /health debe responder 200 y JSON con estado healthy."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_login_page_renders(client):
    """GET / debe cargar la página de login exitosamente con código 200."""
    response = client.get('/')
    assert response.status_code == 200


def test_login_success_admin(client, admin_user):
    """POST / con credenciales de administrador válidas debe autenticar y redirigir al dashboard."""
    response = client.post('/', data={
        'correo': 'admin@biblioteca.test',
        'password': 'Admin123!'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')


def test_login_success_verified_aprendiz(client, aprendiz_user):
    """POST / con credenciales de aprendiz verificado debe iniciar sesión exitosamente."""
    response = client.post('/', data={
        'correo': 'aprendiz@biblioteca.test',
        'password': 'Aprendiz123!'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')


def test_login_invalid_password(client, admin_user):
    """POST / con contraseña incorrecta no debe autenticar y debe mostrar la vista de login."""
    response = client.post('/', data={
        'correo': 'admin@biblioteca.test',
        'password': 'WrongPassword123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    # No debe haberse redirigido al dashboard
    assert b'dashboard' not in response.data or b'Iniciar Sesi' in response.data


def test_login_nonexistent_user(client):
    """POST / con usuario inexistente debe fallar sin revelar existencia."""
    response = client.post('/', data={
        'correo': 'noexiste@biblioteca.test',
        'password': 'Password123!'
    }, follow_redirects=True)

    assert response.status_code == 200


def test_login_unverified_aprendiz_blocked(client, unverified_user):
    """POST / con aprendiz no verificado debe bloquear el acceso y solicitar verificación."""
    response = client.post('/', data={
        'correo': 'noverificado@biblioteca.test',
        'password': 'Password123!'
    }, follow_redirects=True)

    assert response.status_code == 200


def test_login_inactive_user_blocked(client, inactive_user):
    """POST / con usuario inactivo debe rechazar la autenticación."""
    response = client.post('/', data={
        'correo': 'inactivo@biblioteca.test',
        'password': 'Password123!'
    }, follow_redirects=True)

    assert response.status_code == 200


def test_dashboard_requires_login(client):
    """GET /dashboard sin autenticación previa debe redirigir al login."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')


def test_dashboard_authenticated(admin_client):
    """GET /dashboard con sesión autenticada debe responder 200."""
    response = admin_client.get('/dashboard')
    assert response.status_code == 200


def test_registro_page_renders(client):
    """GET /registro debe responder 200 con el formulario de registro."""
    response = client.get('/registro')
    assert response.status_code == 200


def test_registro_success(client):
    """POST /registro con datos válidos crea el usuario en la BD con estado no verificado."""
    response = client.post('/registro', data={
        'nombres': 'Nuevo',
        'apellidos': 'Usuario',
        'correo': 'nuevo.usuario@biblioteca.test',
        'password': 'PasswordSeguro123!',
        'rol': 'aprendiz',
        'website': ''  # Honeypot vacío
    }, follow_redirects=False)

    assert response.status_code == 302

    # Verificar creación en base de datos
    user = Usuario.query.filter_by(correo='nuevo.usuario@biblioteca.test').first()
    assert user is not None
    assert user.nombres == 'Nuevo'
    assert user.email_verificado is False
    assert user.check_password('PasswordSeguro123!') is True


def test_registro_duplicate_email(client, aprendiz_user):
    """POST /registro con correo duplicado debe fallar y no crear usuario adicional."""
    response = client.post('/registro', data={
        'nombres': 'Duplicado',
        'apellidos': 'Test',
        'correo': 'aprendiz@biblioteca.test',
        'password': 'Password123!',
        'rol': 'aprendiz',
        'website': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    total_users = Usuario.query.filter_by(correo='aprendiz@biblioteca.test').count()
    assert total_users == 1


def test_registro_validation_errors(client):
    """POST /registro con contraseña inválida o campos vacíos debe retornar la vista con errores."""
    response = client.post('/registro', data={
        'nombres': '',
        'apellidos': '',
        'correo': 'invalido',
        'password': '123',  # Muy corta, sin mayúsculas
        'rol': 'invalido',
        'website': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert Usuario.query.filter_by(correo='invalido').first() is None


def test_registro_honeypot_bot_detection(client):
    """POST /registro con honeypot 'website' lleno debe simular éxito sin crear registro."""
    response = client.post('/registro', data={
        'nombres': 'Bot',
        'apellidos': 'Spam',
        'correo': 'bot@spam.com',
        'password': 'Password123!',
        'rol': 'aprendiz',
        'website': 'http://spam-link.com'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert Usuario.query.filter_by(correo='bot@spam.com').first() is None


def test_logout(admin_client):
    """GET /logout debe cerrar sesión y redirigir al login."""
    response = admin_client.get('/logout', follow_redirects=False)
    assert response.status_code == 302

    # Verificar que ya no tiene acceso al dashboard
    dashboard_response = admin_client.get('/dashboard', follow_redirects=False)
    assert dashboard_response.status_code == 302


def test_logout_beacon_post(admin_client):
    """POST /logout (sendBeacon) debe responder con código HTTP 204 No Content."""
    response = admin_client.post('/logout')
    assert response.status_code == 204
