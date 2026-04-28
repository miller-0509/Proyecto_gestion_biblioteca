from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models.usuarios import Usuario
from app.decorators import admin_required
from app import db

bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@bp.route('/')
@login_required
@admin_required
def lista_usuarios():
    # Obtener todos los usuarios de la base de datos
    usuarios = Usuario.query.all()
    return render_template('usuarios/lista.html', usuarios=usuarios)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    if request.method == 'POST':
        nombres   = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        correo    = request.form.get('correo', '').strip()
        password  = request.form.get('password', '')
        rol       = request.form.get('rol', '').strip()
        estado    = request.form.get('estado', 'activo').strip()

        errors = Usuario.validate_registro(nombres, apellidos, correo, password, rol, is_admin=True)
        if errors:
            return render_template('usuarios/crear_admin.html',
                                   errors=errors,
                                   nombres=nombres, apellidos=apellidos, correo=correo, rol=rol, estado=estado)

        nuevo_usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            rol=rol,
            estado=estado
        )
        nuevo_usuario.set_password(password)
        nuevo_usuario.save()

        flash('Usuario creado exitosamente.', 'success')
        return redirect(url_for('usuarios.lista_usuarios'))

    return render_template('usuarios/crear_admin.html', errors=[])

@bp.route('/editar/<int:id_usuario>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)

    if request.method == 'POST':
        nombres   = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        correo    = request.form.get('correo', '').strip()
        rol       = request.form.get('rol', '').strip()
        estado    = request.form.get('estado', '').strip()
        password  = request.form.get('password', '')

        errors = Usuario.validate_edicion(nombres, apellidos, correo, rol, estado, current_correo=usuario.correo)
        
        # Validar contraseña solo si se intenta cambiar
        if password and len(password) < 6:
            errors.append('La nueva contraseña debe tener al menos 6 caracteres.')

        if errors:
            return render_template('usuarios/editar.html',
                                   usuario=usuario, errors=errors)

        # Actualizar datos
        usuario.nombres = nombres
        usuario.apellidos = apellidos
        usuario.correo = correo
        usuario.rol = rol
        usuario.estado = estado

        if password:
            usuario.set_password(password)

        db.session.commit()
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('usuarios.lista_usuarios'))

    return render_template('usuarios/editar.html', usuario=usuario, errors=[])

@bp.route('/eliminar/<int:id_usuario>', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    
    if usuario.id_usuario == current_user.id_usuario:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('usuarios.lista_usuarios'))
        
    db.session.delete(usuario)
    db.session.commit()
    flash(f'Usuario {usuario.nombres} eliminado exitosamente.', 'success')
    return redirect(url_for('usuarios.lista_usuarios'))
