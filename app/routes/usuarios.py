from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app.models.usuarios import Usuario
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro
from app.decorators import admin_required
from app import db
from datetime import datetime, timezone

bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@bp.route('/')
@login_required
@admin_required
def lista_usuarios():
    page = request.args.get('page', 1, type=int)
    usuarios = Usuario.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('usuarios/lista.html', usuarios=usuarios)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    if request.method == 'POST':
        nombres   = request.form.get('nombres', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        correo    = request.form.get('correo', '').strip().lower()
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
        db.session.commit()

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
        correo    = request.form.get('correo', '').strip().lower()
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
        
    try:
        # 1. Eliminar o desvincular renovaciones donde el usuario sea solicitante o aprobador
        from app.models.renovaciones import RenovacionEquipo, RenovacionLibro
        RenovacionEquipo.query.filter((RenovacionEquipo.id_usuario == id_usuario) | (RenovacionEquipo.id_administrador == id_usuario)).delete()
        RenovacionLibro.query.filter((RenovacionLibro.id_usuario == id_usuario) | (RenovacionLibro.id_administrador == id_usuario)).delete()

        # 2. Desvincular préstamos gestionados si el usuario era administrador (llave foránea anulable)
        Prestamo.query.filter_by(id_administrador=id_usuario).update({Prestamo.id_administrador: None})
        PrestamoLibro.query.filter_by(id_administrador=id_usuario).update({PrestamoLibro.id_administrador: None})
        
        # 3. Eliminar préstamos de equipos y libros del usuario (llave foránea no anulable)
        # Primero eliminar renovaciones asociadas a estos préstamos de forma preventiva
        prestamos_ids = [p.id_prestamo for p in Prestamo.query.filter_by(id_usuario=id_usuario).all()]
        prestamos_libros_ids = [pl.id_prestamo_libro for pl in PrestamoLibro.query.filter_by(id_usuario=id_usuario).all()]
        if prestamos_ids:
            RenovacionEquipo.query.filter(RenovacionEquipo.id_prestamo.in_(prestamos_ids)).delete(synchronize_session=False)
        if prestamos_libros_ids:
            RenovacionLibro.query.filter(RenovacionLibro.id_prestamo_libro.in_(prestamos_libros_ids)).delete(synchronize_session=False)

        Prestamo.query.filter_by(id_usuario=id_usuario).delete()
        PrestamoLibro.query.filter_by(id_usuario=id_usuario).delete()
        
        # 4. Eliminar al usuario físicamente
        db.session.delete(usuario)
        db.session.commit()
        
        flash(f'Usuario {usuario.nombres} {usuario.apellidos} y todo su historial de préstamos fueron eliminados permanentemente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al eliminar el usuario: {str(e)}', 'danger')
        
    return redirect(url_for('usuarios.lista_usuarios'))

@bp.route('/historial/<int:id_usuario>')
@login_required
def historial_prestamos(id_usuario):
    # Seguridad: Solo admin o el propio usuario pueden ver este historial
    if current_user.rol != 'administrador' and current_user.id_usuario != id_usuario:
        flash('No tienes permiso para ver este historial.', 'danger')
        return redirect(url_for('auth.dashboard'))
        
    usuario = Usuario.query.get_or_404(id_usuario)
    now = datetime.now(timezone.utc)
    
    # Obtener préstamos de equipos
    prestamos_equipos = Prestamo.query.filter_by(id_usuario=id_usuario).all()
    # Obtener préstamos de libros
    prestamos_libros = PrestamoLibro.query.filter_by(id_usuario=id_usuario).all()
    
    historial = []
    
    def calcular_estado(prestamo):
        """Determina si un préstamo activo está atrasado."""
        if prestamo.estado in ('pendiente', 'aceptado') and prestamo.fecha_devolucion_esperada:
            fecha_esp = prestamo.fecha_devolucion_esperada
            # Asegurar que la fecha sea timezone-aware para comparación segura
            if fecha_esp.tzinfo is None:
                fecha_esp = fecha_esp.replace(tzinfo=timezone.utc)
            if fecha_esp < now:
                return 'atrasado'
        return prestamo.estado

    # Unificar equipos
    for p in prestamos_equipos:
        historial.append({
            'tipo': 'Equipo',
            'recurso': p.equipo.nombre if p.equipo else 'Equipo Eliminado',
            'fecha_solicitud': p.fecha_solicitud,
            'fecha_devolucion_esperada': p.fecha_devolucion_esperada,
            'fecha_devolucion_real': p.fecha_devolucion_real,
            'estado': calcular_estado(p),
            'observaciones': p.observaciones,
            'razon_rechazo': p.razon_rechazo,
            'observacion_devolucion': p.observacion_devolucion,
            'estado_fisico_devolucion': p.estado_fisico_devolucion,
            'estado_renovacion': p.estado_renovacion
        })
        
    # Unificar libros
    for p in prestamos_libros:
        historial.append({
            'tipo': 'Libro',
            'recurso': p.libro.titulo if p.libro else 'Libro Eliminado',
            'fecha_solicitud': p.fecha_solicitud,
            'fecha_devolucion_esperada': p.fecha_devolucion_esperada,
            'fecha_devolucion_real': p.fecha_devolucion_real,
            'estado': calcular_estado(p),
            'observaciones': p.observaciones,
            'razon_rechazo': p.razon_rechazo,
            'observacion_devolucion': p.observacion_devolucion,
            'estado_fisico_devolucion': p.estado_fisico_devolucion,
            'estado_renovacion': p.estado_renovacion
        })
        
    # Ordenar por fecha de solicitud (más recientes primero)
    historial.sort(key=lambda x: x['fecha_solicitud'] if x['fecha_solicitud'] else datetime.min, reverse=True)
    
    # Calcular estadísticas
    stats = {
        'total': len(historial),
        'activos': sum(1 for h in historial if h['estado'] in ('pendiente', 'aceptado')),
        'atrasados': sum(1 for h in historial if h['estado'] == 'atrasado'),
        'devueltos': sum(1 for h in historial if h['estado'] == 'devuelto'),
    }
    
    return render_template('usuarios/historial.html', historial=historial, usuario_obj=usuario, stats=stats)
