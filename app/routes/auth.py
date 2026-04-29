from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuarios import Usuario
from app import db, limiter

bp = Blueprint('auth', __name__)


# ── Login ──────────────────────────────────────────────────────────────────
@bp.route('/', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '')

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario is None or not usuario.check_password(password):
            current_app.logger.warning('Intento de login fallido para correo: %s desde IP: %s', correo, request.remote_addr)
            # Mensaje genérico para evitar enumeración de usuarios
            flash('Credenciales incorrectas. Verifica tus datos e intenta de nuevo.', 'danger')
            return render_template('login.html', correo=correo)

        if usuario.estado != 'activo':
            current_app.logger.warning('Login bloqueado (cuenta %s) para: %s', usuario.estado, correo)
            flash('Tu cuenta no está activa. Contacta al administrador.', 'warning')
            return render_template('login.html', correo=correo)

        login_user(usuario)
        current_app.logger.info('Login exitoso: %s (ID: %s)', usuario.correo, usuario.id_usuario)
        flash(f'¡Bienvenido, {usuario.nombres}!', 'success')
        return redirect(url_for('auth.dashboard'))

    return render_template('login.html', correo='')


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
            flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

        nombres   = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        correo    = request.form.get('correo', '').strip()
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
        )
        nuevo.set_password(password)
        nuevo.save()

        current_app.logger.info('Nuevo usuario registrado: %s (rol: %s)', correo, rol)
        flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('usuarios/register.html',
                           errors=[],
                           nombres='', apellidos='', correo='', rol='')


# ── Logout ─────────────────────────────────────────────────────────────────
@bp.route('/logout')
@login_required
def logout():
    current_app.logger.info('Logout: %s (ID: %s)', current_user.correo, current_user.id_usuario)
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))
