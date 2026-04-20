from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from app import db
from app.models.prestamos_libros import PrestamoLibro
from app.models.libros import Libro
from app.models.usuarios import Usuario

bp = Blueprint('prestamos_libros', __name__, url_prefix='/prestamos-libros')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'administrador':
            flash('No tienes permisos para acceder a esta sección.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/lista')
@login_required
def lista_prestamos():
    if current_user.rol == 'administrador':
        prestamos = PrestamoLibro.query.order_by(PrestamoLibro.fecha_solicitud.desc()).all()
        titulo = 'Gestión de Préstamos de Libros'
    else:
        prestamos = PrestamoLibro.query.filter_by(id_usuario=current_user.id_usuario).order_by(
            PrestamoLibro.fecha_solicitud.desc()
        ).all()
        titulo = 'Mis Préstamos de Libros'
    
    from datetime import datetime as dt
    ahora = dt.now()
    prestamos_con_dias = []
    for prestamo in prestamos:
        datos_prestamo = {
            'prestamo': prestamo,
            'dias_restantes': None
        }
        if prestamo.estado == 'aceptado' and prestamo.fecha_devolucion_esperada:
            try:
                fecha_dev = prestamo.fecha_devolucion_esperada
                if fecha_dev.tzinfo is not None:
                    fecha_dev = fecha_dev.replace(tzinfo=None)
                datos_prestamo['dias_restantes'] = (fecha_dev - ahora).days
            except Exception:
                pass
        prestamos_con_dias.append(datos_prestamo)
    
    return render_template('prestamos_libros/lista.html', prestamos=prestamos_con_dias, titulo=titulo)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_prestamo():
    if current_user.rol == 'administrador':
        if request.method == 'GET':
            libros = Libro.query.filter_by(disponible_prestamo=True, estado='disponible').all()
            usuarios = Usuario.query.filter(Usuario.rol.in_(['aprendiz', 'instructor'])).all()
            return render_template('prestamos_libros/crear.html', libros=libros, usuarios=usuarios, modo='admin')
        else:
            id_libro = request.form.get('id_libro', type=int)
            id_usuario = request.form.get('id_usuario', type=int)
            dias_prestamo = request.form.get('dias_prestamo', type=int, default=15)
            observaciones = request.form.get('observaciones', '')
            
            errors = PrestamoLibro.validate_crear_prestamo(id_usuario, id_libro, observaciones)
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return redirect(url_for('prestamos_libros.crear_prestamo'))
            
            fecha_devolucion_esperada = datetime.now(timezone.utc) + timedelta(days=dias_prestamo)
            prestamo = PrestamoLibro(
                id_usuario=id_usuario,
                id_libro=id_libro,
                id_administrador=current_user.id_usuario,
                fecha_devolucion_esperada=fecha_devolucion_esperada,
                estado='aceptado',
                fecha_aprobacion=datetime.now(timezone.utc),
                observaciones=observaciones
            )
            prestamo.save()
            flash(f'Préstamo de libro creado exitosamente por {dias_prestamo} días.', 'success')
            return redirect(url_for('prestamos_libros.lista_prestamos'))
    else:
        if request.method == 'GET':
            id_libro = request.args.get('id_libro', type=int)
            libros = Libro.query.filter_by(disponible_prestamo=True, estado='disponible').all()
            libro_seleccionado = Libro.query.get(id_libro) if id_libro else None
            return render_template('prestamos_libros/crear.html', libros=libros, libro_seleccionado=libro_seleccionado, modo='usuario')
        else:
            id_libro = request.form.get('id_libro', type=int)
            observaciones = request.form.get('observaciones', '')
            
            errors = PrestamoLibro.validate_crear_prestamo(current_user.id_usuario, id_libro, observaciones)
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return redirect(url_for('prestamos_libros.crear_prestamo'))
            
            dias_prestamo = Libro.query.get(id_libro).tiempo_max_prestamo or 15
            fecha_devolucion_esperada = datetime.now(timezone.utc) + timedelta(days=dias_prestamo)
            prestamo = PrestamoLibro(
                id_usuario=current_user.id_usuario,
                id_libro=id_libro,
                fecha_devolucion_esperada=fecha_devolucion_esperada,
                estado='pendiente',
                observaciones=observaciones
            )
            prestamo.save()
            flash('Solicitud de préstamo de libro enviada. El administrador la revisará.', 'info')
            return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>/aceptar', methods=['POST'])
@login_required
@admin_required
def aceptar_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    prestamo.estado = 'aceptado'
    prestamo.fecha_aprobacion = datetime.now(timezone.utc)
    prestamo.id_administrador = current_user.id_usuario
    prestamo.save()
    flash('Préstamo aceptado.', 'success')
    return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>/rechazar', methods=['POST'])
@login_required
@admin_required
def rechazar_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    prestamo.estado = 'rechazado'
    prestamo.razon_rechazo = request.form.get('razon_rechazo', '')
    prestamo.id_administrador = current_user.id_usuario
    prestamo.save()
    flash('Préstamo rechazado.', 'success')
    return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>/devolver', methods=['POST'])
@login_required
@admin_required
def devolver_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if prestamo.estado != 'aceptado':
        flash('Este préstamo no está en estado aceptado.', 'warning')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    prestamo.estado = 'devuelto'
    prestamo.fecha_devolucion_real = datetime.now(timezone.utc)
    prestamo.save()
    flash('Préstamo marcado como devuelto.', 'success')
    return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>')
@login_required
def detalle_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if current_user.rol != 'administrador' and prestamo.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para ver este préstamo.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    dias_restantes = None
    if prestamo.estado == 'aceptado' and prestamo.fecha_devolucion_esperada:
        try:
            from datetime import datetime as dt
            ahora = dt.now()
            fecha_dev = prestamo.fecha_devolucion_esperada
            if fecha_dev.tzinfo is not None:
                fecha_dev = fecha_dev.replace(tzinfo=None)
            dias_restantes = (fecha_dev - ahora).days
        except Exception:
            pass
    return render_template('prestamos_libros/detalle.html', prestamo=prestamo, dias_restantes=dias_restantes)
