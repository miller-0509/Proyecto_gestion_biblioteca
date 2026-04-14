from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from app import db
from app.models.prestamos import Prestamo
from app.models.equipos import Equipo
from app.models.usuarios import Usuario

bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')


def admin_required(f):
    """Decorator para rutas que requieren ser administrador"""
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
    """Lista de préstamos del usuario o todos si es admin"""
    
    if current_user.rol == 'administrador':
        # Admin ve todos los préstamos
        prestamos = Prestamo.query.order_by(Prestamo.fecha_solicitud.desc()).all()
        titulo = 'Gestión de Préstamos'
    else:
        # Usuario ve solo sus préstamos
        prestamos = Prestamo.query.filter_by(id_usuario=current_user.id_usuario).order_by(
            Prestamo.fecha_solicitud.desc()
        ).all()
        titulo = 'Mis Préstamos'
    
    # Precalcular días restantes para cada préstamo (sin timezone)
    from datetime import datetime as dt
    ahora = dt.now()  # Naive datetime
    prestamos_con_dias = []
    for prestamo in prestamos:
        datos_prestamo = {
            'prestamo': prestamo,
            'dias_restantes': None
        }
        
        if prestamo.estado == 'aceptado' and prestamo.fecha_devolucion_esperada:
            try:
                # Asegurar que ambos son naive (sin timezone)
                fecha_dev = prestamo.fecha_devolucion_esperada
                if fecha_dev.tzinfo is not None:
                    fecha_dev = fecha_dev.replace(tzinfo=None)
                
                dias_restantes = (fecha_dev - ahora).days
                datos_prestamo['dias_restantes'] = dias_restantes
            except Exception:
                # Si hay error en el cálculo, dejar como None
                pass
        
        prestamos_con_dias.append(datos_prestamo)
    
    return render_template('prestamos/lista.html', prestamos=prestamos_con_dias, titulo=titulo)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_prestamo():
    """Crear nuevo préstamo"""
    
    if current_user.rol == 'administrador':
        # Admin puede seleccionar equipo y usuario
        if request.method == 'GET':
            equipos = Equipo.query.filter_by(disponible_prestamo=True, estado='disponible').all()
            usuarios = Usuario.query.filter(Usuario.rol.in_(['aprendiz', 'instructor'])).all()
            return render_template('prestamos/crear.html', equipos=equipos, usuarios=usuarios, modo='admin')
        
        else:  # POST
            id_equipo = request.form.get('id_equipo', type=int)
            id_usuario = request.form.get('id_usuario', type=int)
            dias_prestamo = request.form.get('dias_prestamo', type=int, default=7)
            observaciones = request.form.get('observaciones', '')
            
            # Validar
            errors = Prestamo.validate_crear_prestamo(id_usuario, id_equipo, observaciones)
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return redirect(url_for('prestamos.crear_prestamo'))
            
            # Crear préstamo
            fecha_devolucion_esperada = datetime.now(timezone.utc) + timedelta(days=dias_prestamo)
            prestamo = Prestamo(
                id_usuario=id_usuario,
                id_equipo=id_equipo,
                id_administrador=current_user.id_usuario,
                fecha_devolucion_esperada=fecha_devolucion_esperada,
                estado='aceptado',  # El admin crea directamente aceptado
                fecha_aprobacion=datetime.now(timezone.utc),
                observaciones=observaciones
            )
            prestamo.save()
            
            flash(f'Préstamo creado exitosamente por {dias_prestamo} días.', 'success')
            return redirect(url_for('prestamos.lista_prestamos'))
    
    else:
        # Usuario (aprendiz/instructor) puede solicitar préstamo desde aquí o desde equipos
        if request.method == 'GET':
            id_equipo = request.args.get('id_equipo', type=int)
            equipos = Equipo.query.filter_by(disponible_prestamo=True, estado='disponible').all()
            
            equipo_seleccionado = None
            if id_equipo:
                equipo_seleccionado = Equipo.query.get(id_equipo)
            
            return render_template(
                'prestamos/crear.html',
                equipos=equipos,
                equipo_seleccionado=equipo_seleccionado,
                modo='usuario'
            )
        
        else:  # POST
            id_equipo = request.form.get('id_equipo', type=int)
            observaciones = request.form.get('observaciones', '')
            
            # Validar
            errors = Prestamo.validate_crear_prestamo(current_user.id_usuario, id_equipo, observaciones)
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return redirect(url_for('prestamos.crear_prestamo'))
            
            # Crear préstamo en estado pendiente
            dias_prestamo = 7  # Valor por defecto
            fecha_devolucion_esperada = datetime.now(timezone.utc) + timedelta(days=dias_prestamo)
            prestamo = Prestamo(
                id_usuario=current_user.id_usuario,
                id_equipo=id_equipo,
                fecha_devolucion_esperada=fecha_devolucion_esperada,
                estado='pendiente',  # Usuario crea en estado pendiente
                observaciones=observaciones
            )
            prestamo.save()
            
            flash('Solicitud de préstamo enviada. El administrador la revisará pronto.', 'info')
            return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>/aceptar', methods=['POST'])
@login_required
@admin_required
def aceptar_prestamo(id_prestamo):
    """Aceptar solicitud de préstamo"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    prestamo.estado = 'aceptado'
    prestamo.fecha_aprobacion = datetime.now(timezone.utc)
    prestamo.id_administrador = current_user.id_usuario
    prestamo.save()
    
    flash(f'Préstamo del usuario {prestamo.usuario.nombre_completo()} aceptado.', 'success')
    return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>/rechazar', methods=['POST'])
@login_required
@admin_required
def rechazar_prestamo(id_prestamo):
    """Rechazar solicitud de préstamo"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    razon = request.form.get('razon_rechazo', '')
    
    prestamo.estado = 'rechazado'
    prestamo.razon_rechazo = razon
    prestamo.id_administrador = current_user.id_usuario
    prestamo.save()
    
    flash(f'Préstamo rechazado.', 'success')
    return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>/devolver', methods=['POST'])
@login_required
@admin_required
def devolver_prestamo(id_prestamo):
    """Marcar préstamo como devuelto"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    if prestamo.estado != 'aceptado':
        flash('Este préstamo no está en estado aceptado.', 'warning')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    prestamo.estado = 'devuelto'
    prestamo.fecha_devolucion_real = datetime.now(timezone.utc)
    prestamo.save()
    
    flash(f'Préstamo del usuario {prestamo.usuario.nombre_completo()} marcado como devuelto.', 'success')
    return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>')
@login_required
def detalle_prestamo(id_prestamo):
    """Detalles de un préstamo"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    # Validar acceso
    if current_user.rol != 'administrador' and prestamo.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para ver este préstamo.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    # Calcular días restantes (sin timezone)
    dias_restantes = None
    if prestamo.estado == 'aceptado' and prestamo.fecha_devolucion_esperada:
        try:
            from datetime import datetime as dt
            ahora = dt.now()  # Naive datetime
            fecha_dev = prestamo.fecha_devolucion_esperada
            if fecha_dev.tzinfo is not None:
                fecha_dev = fecha_dev.replace(tzinfo=None)
            dias_restantes = (fecha_dev - ahora).days
        except Exception:
            pass
    
    return render_template('prestamos/detalle.html', prestamo=prestamo, dias_restantes=dias_restantes)
