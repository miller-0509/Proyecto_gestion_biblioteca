from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuarios import Usuario
from app import db

bp = Blueprint('auth', __name__)


# ── Login ──────────────────────────────────────────────────────────────────
@bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '')

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario is None or not usuario.check_password(password):
            flash('Correo o contraseña incorrectos.', 'danger')
            return render_template('login.html', correo=correo)

        if usuario.estado != 'activo':
            flash('Tu cuenta está inactiva o bloqueada. Contacta al administrador.', 'warning')
            return render_template('login.html', correo=correo)

        login_user(usuario)
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
def registro():
    if request.method == 'POST':
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

        flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('usuarios/register.html',
                           errors=[],
                           nombres='', apellidos='', correo='', rol='')


# ── Logout ─────────────────────────────────────────────────────────────────
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))
