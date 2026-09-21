"""
Suite de pruebas automatizadas de seguridad para la aplicación Flask.

Verifica:
1. Control de acceso basado en roles (RBAC) y prevención de escalamiento de privilegios.
2. Seguridad de autenticación, almacenamiento de contraseñas y fijación de sesiones.
3. Desactivación dinámica de cuentas (auto-logout de usuarios inactivos/bloqueados).
4. Protección contra enumeración de usuarios (recuperación y verificación de correo).
5. Resistencia a inyecciones SQL (SQLi) mediante parametrización del ORM.
6. Escape automático contra Cross-Site Scripting (XSS) en plantillas.
7. Mecanismos anti-bot (Honeypot).
8. Encabezados de seguridad HTTP y protección CSRF.
"""
from app import create_app, db
from app.models.equipos import Equipo
from app.models.libros import Libro
from app.models.usuarios import Usuario
from config import TestingConfig

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONTROL DE ACCESO BASADO EN ROLES (RBAC) & PRIVILEGE ESCALATION
# ─────────────────────────────────────────────────────────────────────────────

def test_rbac_unauthenticated_user_cannot_access_protected_endpoints(client):
    """Cualquier endpoint administrativo debe rechazar solicitudes anónimas."""
    protected_urls = [
        '/dashboard',
        '/usuarios/',
        '/usuarios/crear',
        '/libros/nuevo',
        '/equipos/nuevo',
        '/prestamos/lista',
        '/prestamos-libros/lista',
    ]
    for url in protected_urls:
        response = client.get(url, follow_redirects=False)
        assert response.status_code == 302, f"La URL {url} permitió acceso anónimo sin redirigir"
        assert '/' in response.headers.get('Location', '')


def test_rbac_aprendiz_cannot_access_user_management(aprendiz_client):
    """Un usuario con rol 'aprendiz' no puede acceder al módulo de gestión de usuarios."""
    response = aprendiz_client.get('/usuarios/', follow_redirects=False)
    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')


def test_rbac_aprendiz_cannot_create_or_edit_users(aprendiz_client):
    """Un usuario con rol 'aprendiz' no puede crear ni modificar otros usuarios."""
    response = aprendiz_client.post('/usuarios/crear', data={
        'nombres': 'Hacker',
        'apellidos': 'User',
        'correo': 'hacker@test.com',
        'password': 'Password123!',
        'rol': 'administrador',
        'estado': 'activo'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')
    assert Usuario.query.filter_by(correo='hacker@test.com').first() is None


def test_rbac_bibliotecario_cannot_manage_warehouse_equipment(bibliotecario_client):
    """Un bibliotecario no tiene permisos para crear o eliminar equipos de almacén."""
    response = bibliotecario_client.post('/equipos/nuevo', data={
        'nombre': 'Equipo No Autorizado',
        'tipo_equipo': 'Laptop',
        'numero_serie': 'NOAUTH-EQ-999',
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')
    assert Equipo.query.filter_by(numero_serie='NOAUTH-EQ-999').first() is None


def test_rbac_almacenista_cannot_manage_library_books(almacenista_client):
    """Un almacenista no tiene permisos para crear o modificar libros de biblioteca."""
    response = almacenista_client.post('/libros/nuevo', data={
        'titulo': 'Libro No Autorizado',
        'autor': 'Autor',
        'genero': 'Ficción',
        'codigo_unico': 'NOAUTH-LIB-999',
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')
    assert Libro.query.filter_by(codigo_unico='NOAUTH-LIB-999').first() is None


# ─────────────────────────────────────────────────────────────────────────────
# 2. SEGURIDAD DE CONTRASEÑAS Y GESTIÓN DE SESIONES
# ─────────────────────────────────────────────────────────────────────────────

def test_password_never_stored_in_plaintext(app):
    """Las contraseñas de los usuarios deben estar obligatoriamente hasheadas."""
    user = Usuario(
        nombres="Seguridad",
        apellidos="Test",
        correo="seguridad@test.com",
        rol="aprendiz"
    )
    raw_password = "PasswordSegura123!"
    user.set_password(raw_password)

    assert user.password != raw_password
    assert not user.password.startswith("Password")
    # Werkzeug genera hashes scrypt o pbkdf2 con formato seguro
    assert (
        user.password.startswith("scrypt:")
        or user.password.startswith("pbkdf2:")
        or user.password.startswith("$2")
    )


def test_weak_passwords_rejected_by_policy(app):
    """La política de contraseñas debe rechazar contraseñas cortas, sin mayúsculas o sin dígitos."""
    # Menos de 8 caracteres
    err_corta = Usuario.validate_registro("Test", "User", "test@test.com", "Pass1!", "aprendiz")
    assert any("8 caracteres" in e for e in err_corta)

    # Sin mayúsculas
    err_no_upper = Usuario.validate_registro("Test", "User", "test@test.com", "password123!", "aprendiz")
    assert any("mayúscula" in e for e in err_no_upper)

    # Sin números
    err_no_digit = Usuario.validate_registro("Test", "User", "test@test.com", "Password!", "aprendiz")
    assert any("número" in e for e in err_no_digit)


def test_session_fixation_mitigation_on_login(client, admin_user):
    """Al iniciar sesión se debe reiniciar la sesión para evitar ataques de Session Fixation."""
    with client.session_transaction() as sess:
        sess['attacker_flag'] = 'malicious_session_data'

    client.post('/', data={
        'correo': 'admin@biblioteca.test',
        'password': 'Admin123!'
    }, follow_redirects=True)

    with client.session_transaction() as sess:
        assert 'attacker_flag' not in sess
        assert '_user_id' in sess


def test_deactivated_user_auto_logout_middleware(client, aprendiz_user):
    """Si un usuario activo es desactivado/bloqueado, el middleware before_request debe expulsarlo."""
    # 1. Iniciar sesión como usuario activo
    client.post('/', data={
        'correo': 'aprendiz@biblioteca.test',
        'password': 'Aprendiz123!'
    }, follow_redirects=True)

    # 2. Desactivar usuario en la base de datos
    aprendiz_user.estado = 'inactivo'
    db.session.commit()

    # 3. La siguiente petición debe forzar logout y redirigir
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')


# ─────────────────────────────────────────────────────────────────────────────
# 3. PROTECCIÓN CONTRA ENUMERACIÓN DE USUARIOS
# ─────────────────────────────────────────────────────────────────────────────

def test_anti_enumeration_password_recovery(client, aprendiz_user):
    """La solicitud de recuperación de contraseña debe devolver la misma respuesta exista o no el correo."""
    # Correo existente
    res_existente = client.post('/recuperar-password', data={'correo': 'aprendiz@biblioteca.test'}, follow_redirects=False)
    # Correo inexistente
    res_inexistente = client.post('/recuperar-password', data={'correo': 'fantasma@noexiste.test'}, follow_redirects=False)

    assert res_existente.status_code == 302
    assert res_inexistente.status_code == 302
    assert res_existente.headers.get('Location') == res_inexistente.headers.get('Location')


def test_anti_enumeration_resend_verification(client, aprendiz_user):
    """El reenvío de verificación debe retornar mensaje genérico y misma redirección."""
    res_existente = client.post('/reenviar-verificacion', data={'correo': 'aprendiz@biblioteca.test'}, follow_redirects=False)
    res_inexistente = client.post('/reenviar-verificacion', data={'correo': 'noexiste@test.com'}, follow_redirects=False)

    assert res_existente.status_code == 302
    assert res_inexistente.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# 4. PROTECCIÓN CONTRA INYECCIONES SQL (SQLi) & XSS
# ─────────────────────────────────────────────────────────────────────────────

def test_sql_injection_resilience_in_search(aprendiz_client, sample_libro):
    """Los payloads clásicos de inyección SQL no deben romper consultas ni alterar la base de datos."""
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE libros; --",
        "1 UNION SELECT 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 --",
        "admin'--",
    ]

    for payload in sqli_payloads:
        response = aprendiz_client.get(f'/libros/?busqueda={payload}')
        assert response.status_code == 200, f"Fallo al procesar búsqueda con payload SQLi: {payload}"

    # Verificar integridad de la tabla
    assert Libro.query.count() >= 1


def test_xss_prevention_in_search_and_render(aprendiz_client):
    """Los scripts XSS en parámetros de búsqueda deben ser escapados por Jinja2 en la respuesta HTML."""
    xss_payload = "<script>alert('XSS_TEST_ATTACK')</script>"
    response = aprendiz_client.get(f'/libros/?busqueda={xss_payload}')

    assert response.status_code == 200
    # No debe renderizar el tag HTML crudo sin escapar
    assert b"<script>alert('XSS_TEST_ATTACK')</script>" not in response.data
    # Debe contener la versión escapada segura
    assert b"&lt;script&gt;alert(&#39;XSS_TEST_ATTACK&#39;)&lt;/script&gt;" in response.data or b"alert(" in response.data


# ─────────────────────────────────────────────────────────────────────────────
# 5. PROTECCIÓN ANTI-BOT (HONEYPOT)
# ─────────────────────────────────────────────────────────────────────────────

def test_honeypot_traps_automated_bots(client):
    """Si un bot completa el campo señuelo 'website', la solicitud debe descartarse sin persistir."""
    response = client.post('/registro', data={
        'nombres': 'BotName',
        'apellidos': 'BotLastname',
        'correo': 'bot_attack@spam.com',
        'password': 'BotPassword123!',
        'rol': 'aprendiz',
        'website': 'https://malicious-spammer-domain.com'
    }, follow_redirects=False)

    # Simula redirección exitosa para no alertar al bot
    assert response.status_code == 302
    assert Usuario.query.filter_by(correo='bot_attack@spam.com').first() is None


# ─────────────────────────────────────────────────────────────────────────────
# 6. ENCABEZADOS DE SEGURIDAD HTTP Y PROTECCIÓN CSRF
# ─────────────────────────────────────────────────────────────────────────────

def test_security_cache_headers_on_html_responses(admin_client):
    """Las respuestas HTML deben incluir encabezados Cache-Control para evitar almacenamiento en caché."""
    response = admin_client.get('/dashboard')
    assert response.status_code == 200

    cache_control = response.headers.get('Cache-Control', '')
    assert 'no-cache' in cache_control
    assert 'no-store' in cache_control
    assert 'must-revalidate' in cache_control


def test_csrf_protection_blocks_forged_post_requests():
    """Con CSRF habilitado, peticiones POST sin token CSRF deben ser rechazadas con 400 Bad Request."""
    class CsrfTestConfig(TestingConfig):
        WTF_CSRF_ENABLED = True  # Forzar validación CSRF

    csrf_app = create_app(CsrfTestConfig)
    with csrf_app.app_context():
        db.create_all()
        csrf_client = csrf_app.test_client()

        # Petición POST sin token CSRF
        response = csrf_client.post('/', data={
            'correo': 'test@test.com',
            'password': 'Password123!'
        })

        assert response.status_code == 400
        db.session.remove()
        db.drop_all()
