from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
from app import db, mail
from app.models.prestamos import Prestamo
from app.services.email_service import enviar_notificacion_prestamo
from app.models.equipos import Equipo, HistorialEstadoEquipo
from app.models.usuarios import Usuario
from app.decorators import admin_required, gestion_equipos_required, calcular_dias_restantes

bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')


@bp.route('/lista')
@login_required
def lista_prestamos():
    """Lista de préstamos del usuario o todos si es admin"""
    page = request.args.get('page', 1, type=int)
    
    if current_user.rol in ['administrador', 'almacenista']:
        # Admin/Almacenista ve todos los préstamos (con joinedload para evitar N+1)
        query = Prestamo.query.options(
            joinedload(Prestamo.usuario),
            joinedload(Prestamo.equipo)
        ).order_by(Prestamo.fecha_solicitud.desc())
        titulo = 'Gestión de Préstamos'
    else:
        # Usuario ve solo sus préstamos
        query = Prestamo.query.options(
            joinedload(Prestamo.equipo)
        ).filter_by(id_usuario=current_user.id_usuario).order_by(
            Prestamo.fecha_solicitud.desc()
        )
        titulo = 'Mis Préstamos'
        
    pagination = query.paginate(page=page, per_page=15)
    prestamos = pagination.items
    
    # Precalcular días restantes usando función compartida
    prestamos_con_dias = []
    for prestamo in prestamos:
        prestamos_con_dias.append({
            'prestamo': prestamo,
            'dias_restantes': calcular_dias_restantes(prestamo)
        })
    
    return render_template('prestamos/lista.html', prestamos=prestamos_con_dias, titulo=titulo, pagination=pagination)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_prestamo():
    """Crear nuevo préstamo"""
    
    if current_user.rol in ['administrador', 'almacenista']:
        # Admin/Almacenista puede seleccionar equipo y usuario
        if request.method == 'GET':
            equipos = Equipo.query.filter_by(disponible_prestamo=True, estado='disponible').limit(100).all()
            usuarios = Usuario.query.filter(Usuario.rol.in_(['aprendiz', 'instructor'])).limit(100).all()
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
            
            # Re-verificar disponibilidad del equipo (protección contra race condition)
            equipo = Equipo.query.get(id_equipo)
            if not equipo or equipo.estado != 'disponible':
                flash('El equipo ya no está disponible. Otro usuario pudo haberlo solicitado.', 'danger')
                return redirect(url_for('prestamos.crear_prestamo'))
            
            # Crear préstamo y marcar equipo como prestado
            equipo.estado = 'prestado'
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
            db.session.add(prestamo)
            db.session.commit()
            
            # Notificar aprobación inmediata
            enviar_notificacion_prestamo(prestamo, 'aprobado', mail, es_libro=False)
            
            current_app.logger.info('Préstamo equipo creado (admin): equipo_id=%s, usuario_id=%s, admin_id=%s', id_equipo, id_usuario, current_user.id_usuario)
            flash(f'Préstamo creado exitosamente por {dias_prestamo} días. Se ha notificado al usuario.', 'success')
            return redirect(url_for('prestamos.lista_prestamos'))
    
    else:
        # Usuario (aprendiz/instructor) puede solicitar préstamo desde aquí o desde equipos
        if request.method == 'GET':
            id_equipo = request.args.get('id_equipo', type=int)
            equipos = Equipo.query.filter_by(disponible_prestamo=True, estado='disponible').limit(100).all()
            
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
            
            # Fix #9: Verificar límite de préstamos activos del usuario
            if current_user.prestamos_activos_count() >= current_user.limite_prestamos:
                flash(f'Has alcanzado el límite de {current_user.limite_prestamos} préstamos activos permitidos para tu rol.', 'warning')
                return redirect(url_for('prestamos.lista_prestamos'))
            
            # Fix #4: Usar tiempo_max_prestamo del equipo si está definido
            equipo = Equipo.query.get(id_equipo)
            dias_prestamo = equipo.tiempo_max_prestamo or 7
            fecha_devolucion_esperada = datetime.now(timezone.utc) + timedelta(days=dias_prestamo)
            prestamo = Prestamo(
                id_usuario=current_user.id_usuario,
                id_equipo=id_equipo,
                fecha_devolucion_esperada=fecha_devolucion_esperada,
                estado='pendiente',  # Usuario crea en estado pendiente
                observaciones=observaciones
            )
            prestamo.save()
            db.session.commit()
            
            # Notificar solicitud recibida
            enviar_notificacion_prestamo(prestamo, 'pendiente', mail, es_libro=False)
            
            flash('Solicitud de préstamo enviada. Se te ha notificado por correo. El administrador la revisará pronto.', 'info')
            return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>/aceptar', methods=['POST'])
@login_required
@gestion_equipos_required
def aceptar_prestamo(id_prestamo):
    """Aceptar solicitud de préstamo"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    # Re-verificar estado actual del equipo (protección contra race condition)
    equipo = Equipo.query.get(prestamo.id_equipo)
    if not equipo or equipo.estado != 'disponible':
        flash('El equipo ya no está disponible. Puede haber sido prestado a otro usuario.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    prestamo.estado = 'aceptado'
    prestamo.fecha_aprobacion = datetime.now(timezone.utc)
    prestamo.id_administrador = current_user.id_usuario
    equipo.estado = 'prestado'
    db.session.commit()
    
    # Notificar aprobación
    enviar_notificacion_prestamo(prestamo, 'aprobado', mail, es_libro=False)
    
    current_app.logger.info('Préstamo aceptado: id=%s, equipo=%s, por admin=%s', id_prestamo, equipo.nombre, current_user.id_usuario)
    flash(f'Préstamo del usuario {prestamo.usuario.nombre_completo()} aceptado y notificado.', 'success')
    return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>/rechazar', methods=['POST'])
@login_required
@gestion_equipos_required
def rechazar_prestamo(id_prestamo):
    """Rechazar solicitud de préstamo"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    razon = request.form.get('razon_rechazo', '')
    
    # Fix #8: Validar longitud de razón de rechazo
    if len(razon) > 255:
        flash('La razón de rechazo no puede exceder 255 caracteres.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    prestamo.estado = 'rechazado'
    prestamo.razon_rechazo = razon
    prestamo.id_administrador = current_user.id_usuario
    prestamo.save()
    db.session.commit()
    
    # Notificar rechazo
    enviar_notificacion_prestamo(prestamo, 'rechazado', mail, es_libro=False)
    
    current_app.logger.info('Préstamo rechazado: id=%s, razón=%s', id_prestamo, razon)
    flash('Préstamo rechazado y notificación enviada.', 'success')
    return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>/devolver', methods=['POST'])
@login_required
@gestion_equipos_required
def devolver_prestamo(id_prestamo):
    """Marcar préstamo como devuelto"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    if prestamo.estado != 'aceptado':
        flash('Este préstamo no está en estado aceptado.', 'warning')
        return redirect(url_for('prestamos.lista_prestamos'))
        
    estado_fisico = request.form.get('estado_fisico')
    estado_final = request.form.get('estado_final')
    observacion_devolucion = request.form.get('observacion_devolucion')
    
    if not observacion_devolucion or observacion_devolucion.strip() == '':
        flash('Debes ingresar una observación para la devolución.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
        
    if not estado_fisico or not estado_final:
        flash('Debes seleccionar el estado físico y la acción final.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
        
    estados_fisicos_validos = ['excelente', 'bueno', 'regular', 'dañado', 'incompleto']
    if estado_fisico not in estados_fisicos_validos:
        flash('Estado físico inválido.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
        
    estados_finales_validos = ['disponible', 'mantenimiento', 'no_disponible']
    if estado_final not in estados_finales_validos:
        flash('Estado final inválido.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    estado_anterior = prestamo.equipo.estado
    
    prestamo.estado = 'devuelto'
    prestamo.fecha_devolucion_real = datetime.now(timezone.utc)
    prestamo.observacion_devolucion = observacion_devolucion
    prestamo.estado_fisico_devolucion = estado_fisico
    
    prestamo.equipo.estado = estado_final
    prestamo.save()
    
    # Registro en historial de estados del equipo
    if estado_anterior != estado_final:
        historial = HistorialEstadoEquipo(
            id_equipo=prestamo.id_equipo,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_final,
            observacion=f"Cambio por devolución. Físico: {estado_fisico}. Obs: {observacion_devolucion}",
            id_administrador=current_user.id_usuario
        )
        db.session.add(historial)
        
    db.session.commit()
    
    # Notificar devolución
    enviar_notificacion_prestamo(prestamo, 'devuelto', mail, es_libro=False)
    
    current_app.logger.info('Préstamo devuelto: id=%s, equipo=%s, estado_fisico=%s, estado_final=%s', id_prestamo, prestamo.equipo.nombre, estado_fisico, estado_final)
    flash(f'Préstamo marcado como devuelto. El equipo pasó a estado {estado_final}.', 'success')
    return redirect(url_for('prestamos.lista_prestamos'))


@bp.route('/<int:id_prestamo>')
@login_required
def detalle_prestamo(id_prestamo):
    """Detalles de un préstamo"""
    
    prestamo = Prestamo.query.get_or_404(id_prestamo)
    
    # Validar acceso
    if current_user.rol not in ['administrador', 'almacenista'] and prestamo.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para ver este préstamo.', 'danger')
        return redirect(url_for('prestamos.lista_prestamos'))
    
    dias_restantes = calcular_dias_restantes(prestamo)
    
    return render_template('prestamos/detalle.html', prestamo=prestamo, dias_restantes=dias_restantes)
