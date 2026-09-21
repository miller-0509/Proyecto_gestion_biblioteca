"""
Pruebas unitarias y de integración para el flujo de verificación de correo
y recuperación/restablecimiento de contraseña.

Cubre:
1. Verificación de email (token válido, inválido, usuario inexistente, ya verificado).
2. Recuperación de contraseña (solicitud y restablecimiento con token).
3. Anti-replay: un token de recuperación no puede reutilizarse tras cambiar la contraseña.
"""
from app import db
from app.models.usuarios import Usuario
from app.services.email_service import (
    generar_token_recuperacion,
    generar_token_verificacion,
    verificar_token,
    verificar_token_recuperacion,
)

# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN DE EMAIL (servicio + ruta)
# ─────────────────────────────────────────────────────────────────────────────

def test_generar_y_verificar_token_verificacion(app):
    """Un token de verificación debe generarse y recuperar el correo original."""
    correo = 'token-test@biblioteca.test'
    token = generar_token_verificacion(correo)

    assert token != correo
    assert verificar_token(token) == correo


def test_verificar_token_invalido_retorna_none(app):
    """Un token manipulado debe devolver None."""
    assert verificar_token('token-manipulado-no-valido') is None


def test_verificar_email_token_valido(client, unverified_user):
    """GET /verificar/<token> con token válido debe verificar el correo."""
    token = generar_token_verificacion('noverificado@biblioteca.test')
    response = client.get(f'/verificar/{token}', follow_redirects=False)

    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')

    db.session.refresh(unverified_user)
    assert unverified_user.email_verificado is True
    assert unverified_user.fecha_verificacion is not None


def test_verificar_email_token_invalido(client, unverified_user):
    """GET /verificar/<token> con token inválido debe redirigir a login sin verificar."""
    response = client.get('/verificar/token-invalido', follow_redirects=False)

    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')

    db.session.refresh(unverified_user)
    assert unverified_user.email_verificado is False


def test_verificar_email_usuario_inexistente(client):
    """Un token firmado para un correo sin cuenta debe redirigir a login."""
    token = generar_token_verificacion('fantasma@noexiste.test')
    response = client.get(f'/verificar/{token}', follow_redirects=False)

    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')


def test_verificar_email_ya_verificado(client, aprendiz_user):
    """Verificar un correo ya verificado debe ser idempotente y redirigir."""
    aprendiz_user.email_verificado = True
    db.session.commit()

    token = generar_token_verificacion('aprendiz@biblioteca.test')
    response = client.get(f'/verificar/{token}', follow_redirects=False)

    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')


# ─────────────────────────────────────────────────────────────────────────────
# RECUPERACIÓN DE CONTRASEÑA (servicio + ruta)
# ─────────────────────────────────────────────────────────────────────────────

def test_generar_y_verificar_token_recuperacion(app, aprendiz_user):
    """Un token de recuperación debe contener correo y fragmento del hash."""
    token = generar_token_recuperacion(aprendiz_user.correo, aprendiz_user.password)

    payload = verificar_token_recuperacion(token)
    assert payload is not None
    assert payload['correo'] == aprendiz_user.correo
    assert payload['ph'] == aprendiz_user.password[:64]


def test_verificar_token_recuperacion_invalido(app):
    """Un token de recuperación manipulado debe devolver None."""
    assert verificar_token_recuperacion('token-invalido') is None


def test_recuperar_password_redirige_siempre(client, aprendiz_user):
    """POST /recuperar-password debe redirigir igual exista o no el usuario."""
    res_existente = client.post('/recuperar-password', data={'correo': 'aprendiz@biblioteca.test'}, follow_redirects=False)
    res_inexistente = client.post('/recuperar-password', data={'correo': 'nadie@noexiste.test'}, follow_redirects=False)

    assert res_existente.status_code == 302
    assert res_inexistente.status_code == 302
    assert res_existente.headers.get('Location') == res_inexistente.headers.get('Location')


def test_restablecer_password_token_valido(client, aprendiz_user):
    """POST /restablecer-password/<token> con token válido debe cambiar la contraseña."""
    password_anterior = aprendiz_user.password
    token = generar_token_recuperacion(aprendiz_user.correo, aprendiz_user.password)

    response = client.post(f'/restablecer-password/{token}', data={
        'password': 'NuevaClaveSegura123!',
        'password_confirm': 'NuevaClaveSegura123!'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')

    db.session.refresh(aprendiz_user)
    assert aprendiz_user.password != password_anterior
    assert aprendiz_user.check_password('NuevaClaveSegura123!') is True


def test_restablecer_password_token_invalido(client):
    """Un token de recuperación inválido debe redirigir a solicitar uno nuevo."""
    response = client.get('/restablecer-password/token-invalido', follow_redirects=False)

    assert response.status_code == 302
    assert '/recuperar-password' in response.headers.get('Location', '')


def test_restablecer_password_antireplay(client, aprendiz_user):
    """Un token de recuperación no debe funcionar tras cambiar la contraseña (anti-replay)."""
    token = generar_token_recuperacion(aprendiz_user.correo, aprendiz_user.password)

    # Primer uso: cambia la contraseña
    response_ok = client.post(f'/restablecer-password/{token}', data={
        'password': 'PrimeraClave123!',
        'password_confirm': 'PrimeraClave123!'
    }, follow_redirects=False)
    assert response_ok.status_code == 302

    # Segundo uso: el token ya no es válido porque el hash cambió
    response_replay = client.get(f'/restablecer-password/{token}', follow_redirects=False)
    assert response_replay.status_code == 302
    assert '/recuperar-password' in response_replay.headers.get('Location', '')


def test_restablecer_password_validaciones(client, aprendiz_user):
    """Contraseñas débiles o que no coinciden deben mostrar errores sin cambiar nada."""
    token = generar_token_recuperacion(aprendiz_user.correo, aprendiz_user.password)
    password_anterior = aprendiz_user.password

    response = client.post(f'/restablecer-password/{token}', data={
        'password': 'corta',
        'password_confirm': 'corta'
    }, follow_redirects=False)

    assert response.status_code == 200
    db.session.refresh(aprendiz_user)
    assert aprendiz_user.password == password_anterior


def test_restablecer_password_usuario_inexistente(client):
    """Un token firmado para un correo sin cuenta debe redirigir a login."""
    token = generar_token_recuperacion('fantasma@noexiste.test', 'hashfragmentounico01')
    response = client.get(f'/restablecer-password/{token}', follow_redirects=False)

    assert response.status_code == 302
    assert '/' in response.headers.get('Location', '')


# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN DE CORREO AL REGISTRARSE
# ─────────────────────────────────────────────────────────────────────────────

def test_registro_crea_usuario_no_verificado(client):
    """Un usuario registrado debe nacer con email_verificado=False."""
    response = client.post('/registro', data={
        'nombres': 'Nuevo',
        'apellidos': 'Usuario',
        'correo': 'nuevo@biblioteca.test',
        'password': 'ClaveSegura123!',
        'rol': 'aprendiz'
    }, follow_redirects=False)

    assert response.status_code == 302

    usuario = Usuario.query.filter_by(correo='nuevo@biblioteca.test').first()
    assert usuario is not None
    assert usuario.email_verificado is False


def test_login_bloqueado_sin_verificar(client, unverified_user):
    """Un aprendiz sin correo verificado no debe poder iniciar sesión."""
    response = client.post('/', data={
        'correo': 'noverificado@biblioteca.test',
        'password': 'Password123!'
    }, follow_redirects=False)

    assert response.status_code == 200
    assert 'verificar tu correo' in response.get_data(as_text=True).lower()
