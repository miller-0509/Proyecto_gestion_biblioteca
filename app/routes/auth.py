from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuarios import Usuario
from app import db, limiter, mail
from app.services.email_service import (
    enviar_correo_verificacion,
    verificar_token,
    enviar_correo_recuperacion,
    verificar_token_recuperacion,
)

bp = Blueprint('auth', __name__)


# ── Login ──────────────────────────────────────────────────────────────────
@bp.route('/', methods=['GET', 'POST'])
@limiter.limit("50 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        correo   = request.form.get('correo', '').strip().lower()
        password = request.form.get('password', '')

        # Búsqueda de usuario
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario is None:
            current_app.logger.warning('Login fallido: Usuario no encontrado (%s)', correo)
        elif not usuario.check_password(password):
            current_app.logger.warning('Login fallido: Contraseña incorrecta para %s', correo)
        elif not usuario.is_active: 
            current_app.logger.warning('Login fallido: Cuenta inactiva para %s (Estado: %s)', correo, usuario.estado)
        else:
            # Verificar si el email ha sido verificado (admins están exentos)
            if not usuario.email_verificado and usuario.rol != 'administrador':
                current_app.logger.warning(
                    'Login bloqueado: Email no verificado para %s (ID: %s)',
                    correo, usuario.id_usuario
                )
                flash('Debes verificar tu correo electrónico antes de iniciar sesión. '
                      'Revisa tu bandeja de entrada o solicita un nuevo enlace.', 'warning')
                return render_template('login.html', correo=correo, email_no_verificado=True)

            # Si pasa todas las validaciones
            from flask import session

            # Cerrar sesión anterior y limpiar cookies de sesión viejas completamente
            logout_user()
            session.clear()

            login_user(usuario, remember=False, fresh=True)
            session.permanent = True  # Activar timeout de sesión

            current_app.logger.info('Login exitoso: %s (ID: %s, Rol: %s)', usuario.correo, usuario.id_usuario, usuario.rol)
            flash(f'¡Bienvenido, {usuario.nombres}!', 'success')
            return redirect(url_for('auth.dashboard'))

        # Si llegó aquí, es porque falló alguna validación
        flash('Credenciales inválidas o cuenta no autorizada.', 'danger')
        return render_template('login.html', correo=correo, email_no_verificado=False)

    return render_template('login.html', correo='', email_no_verificado=False)


# ── Dashboard (home temporal) ──────────────────────────────────────────────
@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


# ── Registro ───────────────────────────────────────────────────────────────
@bp.route('/registro', methods=['GET', 'POST'])
@limiter.limit("3 per minute", methods=["POST"])
def registro():
    if request.method == 'POST':
        # ── Honeypot anti-bot ──────────────────────────────────────
        honeypot = request.form.get('website', '')
        if honeypot:
            current_app.logger.warning('Bot detectado (honeypot) desde IP: %s', request.remote_addr)
            # Simular éxito para no darle pistas al bot
            flash('Usuario registrado exitosamente. Revisa tu correo para verificar tu cuenta.', 'success')
            return redirect(url_for('auth.login'))

        nombres   = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        correo    = request.form.get('correo', '').strip().lower()
        password  = request.form.get('password', '')
        rol       = request.form.get('rol', '').strip()

        errors = Usuario.validate_registro(nombres, apellidos, correo, password, rol)
        if errors:
            return render_template('usuarios/register.html',
                                   errors=errors,
                                   nombres=nombres, apellidos=apellidos, correo=correo, rol=rol)

        nuevo = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            rol=rol,
            email_verificado=False,
        )
        nuevo.set_password(password)
        nuevo.save()
        db.session.commit()

        current_app.logger.info('Nuevo usuario registrado: %s (rol: %s)', correo, rol)

        # Enviar email de verificación
        enviado = enviar_correo_verificacion(nuevo, mail)
        if enviado:
            flash('¡Registro exitoso! Hemos enviado un enlace de verificación a tu correo electrónico. '
                  'Revisa tu bandeja de entrada (y la carpeta de spam).', 'success')
        else:
            flash('Registro exitoso, pero no pudimos enviar el correo de verificación. '
                  'Puedes solicitar un reenvío desde la página de inicio de sesión.', 'warning')

        return redirect(url_for('auth.login'))

    return render_template('usuarios/register.html',
                           errors=[],
                           nombres='', apellidos='', correo='', rol='')


# ── Verificación de Email ──────────────────────────────────────────────────
@bp.route('/verificar/<token>')
def verificar_email(token):
    correo = verificar_token(token)

    if correo is None:
        current_app.logger.warning('Intento de verificación con token inválido/expirado')
        flash('El enlace de verificación es inválido o ha expirado. '
              'Solicita un nuevo enlace desde la página de inicio de sesión.', 'danger')
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.filter_by(correo=correo).first()

    if usuario is None:
        current_app.logger.warning('Verificación: usuario no encontrado para correo %s', correo)
        flash('No se encontró una cuenta asociada a este enlace.', 'danger')
        return redirect(url_for('auth.login'))

    if usuario.email_verificado:
        current_app.logger.info('Verificación: %s ya estaba verificado', correo)
        flash('Tu correo electrónico ya fue verificado anteriormente. Puedes iniciar sesión.', 'info')
        return redirect(url_for('auth.login'))

    # Marcar como verificado
    from datetime import datetime, timezone
    usuario.email_verificado = True
    usuario.fecha_verificacion = datetime.now(timezone.utc)
    db.session.commit()

    current_app.logger.info(
        'Email verificado exitosamente: %s (ID: %s)',
        usuario.correo, usuario.id_usuario
    )
    flash('¡Tu correo electrónico ha sido verificado exitosamente! Ya puedes iniciar sesión.', 'success')
    return redirect(url_for('auth.login'))


# ── Reenvío de Verificación ────────────────────────────────────────────────
@bp.route('/reenviar-verificacion', methods=['POST'])
@limiter.limit("2 per minute")
def reenviar_verificacion():
    correo = request.form.get('correo', '').strip().lower()

    if not correo:
        flash('Debes ingresar tu correo electrónico.', 'danger')
        return redirect(url_for('auth.login'))

    # Respuesta genérica para evitar enumeración de usuarios
    mensaje_generico = ('Si el correo está registrado y no ha sido verificado, '
                        'hemos enviado un nuevo enlace de verificación. '
                        'Revisa tu bandeja de entrada y la carpeta de spam.')

    usuario = Usuario.query.filter_by(correo=correo).first()

    if usuario and not usuario.email_verificado:
        enviado = enviar_correo_verificacion(usuario, mail)
        if enviado:
            current_app.logger.info('Reenvío de verificación exitoso para: %s', correo)
        else:
            current_app.logger.error('Fallo al reenviar verificación a: %s', correo)
    else:
        # Log pero NO revelar si el usuario existe o si ya está verificado
        current_app.logger.info(
            'Reenvío solicitado para correo: %s (usuario_existe=%s, verificado=%s)',
            correo,
            usuario is not None,
            usuario.email_verificado if usuario else 'N/A'
        )

    flash(mensaje_generico, 'info')
    return redirect(url_for('auth.login'))


# ── Recuperar Contraseña (Solicitud) ───────────────────────────────────────
@bp.route('/recuperar-password', methods=['GET', 'POST'])
@limiter.limit("3 per minute", methods=["POST"])
def recuperar_password():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        correo = request.form.get('correo', '').strip().lower()

        # Respuesta genérica SIEMPRE (protección anti-enumeración)
        mensaje_generico = ('Si existe una cuenta asociada a ese correo, '
                            'hemos enviado las instrucciones para restablecer '
                            'tu contraseña. Revisa tu bandeja de entrada y la carpeta de spam.')

        if correo:
            usuario = Usuario.query.filter_by(correo=correo).first()

            if usuario and usuario.is_active:
                enviado = enviar_correo_recuperacion(usuario, mail)
                if enviado:
                    current_app.logger.info(
                        'Recuperacion solicitada y enviada para: %s (ID: %s)',
                        correo, usuario.id_usuario
                    )
                else:
                    current_app.logger.error(
                        'Fallo al enviar correo de recuperacion a: %s', correo
                    )
            else:
                # Log silencioso — NO revelar si el usuario existe
                current_app.logger.info(
                    'Recuperacion solicitada para correo inexistente o inactivo: %s', correo
                )

        flash(mensaje_generico, 'info')
        return redirect(url_for('auth.login'))

    return render_template('recuperar_password.html')


# ── Restablecer Contraseña (con Token) ─────────────────────────────────────
@bp.route('/restablecer-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def restablecer_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    # Validar token criptográfico
    payload = verificar_token_recuperacion(token)

    if payload is None:
        current_app.logger.warning('Intento de restablecimiento con token invalido/expirado')
        flash('El enlace de recuperación es inválido o ha expirado. '
              'Solicita uno nuevo desde la página de inicio de sesión.', 'danger')
        return redirect(url_for('auth.recuperar_password'))

    correo = payload.get('correo')
    ph_fragment = payload.get('ph')

    usuario = Usuario.query.filter_by(correo=correo).first()

    if usuario is None:
        current_app.logger.warning('Restablecimiento: usuario no encontrado para %s', correo)
        flash('No se encontró una cuenta asociada a este enlace.', 'danger')
        return redirect(url_for('auth.login'))

    # Anti-replay: comparar fragmento del hash con el actual
    if usuario.password[:16] != ph_fragment:
        current_app.logger.warning(
            'Token de recuperacion reutilizado (password ya cambiada) para: %s', correo
        )
        flash('Este enlace de recuperación ya fue utilizado. '
              'Si necesitas restablecer tu contraseña nuevamente, solicita un nuevo enlace.', 'warning')
        return redirect(url_for('auth.recuperar_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Validaciones
        errors = []
        if not password:
            errors.append('La contraseña es obligatoria.')
        elif len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres.')
        elif not any(c.isupper() for c in password):
            errors.append('La contraseña debe contener al menos una letra mayúscula.')
        elif not any(c.isdigit() for c in password):
            errors.append('La contraseña debe contener al menos un número.')

        if password != password_confirm:
            errors.append('Las contraseñas no coinciden.')

        if errors:
            return render_template('restablecer_password.html', errors=errors, token=token)

        # Cambiar contraseña
        usuario.set_password(password)
        db.session.commit()

        current_app.logger.info(
            'Contrasena restablecida exitosamente para: %s (ID: %s)',
            usuario.correo, usuario.id_usuario
        )
        flash('¡Tu contraseña ha sido restablecida exitosamente! Ya puedes iniciar sesión con tu nueva contraseña.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('restablecer_password.html', errors=[], token=token)


# ── Logout (acepta GET y POST para sendBeacon) ────────────────────────────
@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if current_user.is_authenticated:
        current_app.logger.info('Logout: %s (ID: %s)', current_user.correo, current_user.id_usuario)
        logout_user()
    # Si es sendBeacon (POST sin redirección esperada), retornar 204
    if request.method == 'POST':
        return '', 204
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))
