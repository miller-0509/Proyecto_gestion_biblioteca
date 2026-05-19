from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
from app import db, mail
from app.models.prestamos_libros import PrestamoLibro
from app.services.email_service import enviar_notificacion_prestamo
from app.models.libros import Libro, HistorialEstadoLibro
from app.models.usuarios import Usuario
from app.decorators import admin_required, gestion_libros_required, calcular_dias_restantes

bp = Blueprint('prestamos_libros', __name__, url_prefix='/prestamos-libros')


@bp.route('/lista')
@login_required
def lista_prestamos():
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    estado = request.args.get('estado', '')

    if current_user.rol in ['administrador', 'bibliotecario']:
        query = PrestamoLibro.query.join(Usuario, PrestamoLibro.id_usuario == Usuario.id_usuario).join(Libro, PrestamoLibro.id_libro == Libro.id_libro).options(
            joinedload(PrestamoLibro.usuario),
            joinedload(PrestamoLibro.libro)
        )
        titulo = 'Gestión de Préstamos de Libros'
    else:
        query = PrestamoLibro.query.join(Libro, PrestamoLibro.id_libro == Libro.id_libro).outerjoin(Usuario, PrestamoLibro.id_usuario == Usuario.id_usuario).options(
            joinedload(PrestamoLibro.libro)
        ).filter(PrestamoLibro.id_usuario == current_user.id_usuario)
        titulo = 'Mis Préstamos de Libros'

    if busqueda:
        query = query.filter(
            (Libro.titulo.ilike(f'%{busqueda}%')) |
            (Usuario.nombres.ilike(f'%{busqueda}%')) |
            (Usuario.apellidos.ilike(f'%{busqueda}%')) |
            (Usuario.correo.ilike(f'%{busqueda}%'))
        )
        
    if estado:
        query = query.filter(PrestamoLibro.estado == estado)

    query = query.order_by(PrestamoLibro.fecha_solicitud.desc())
        
    pagination = query.paginate(page=page, per_page=15)
    prestamos = pagination.items
    
    # Usar función compartida para calcular días restantes
    prestamos_con_dias = []
    for prestamo in prestamos:
        prestamos_con_dias.append({
            'prestamo': prestamo,
            'dias_restantes': calcular_dias_restantes(prestamo)
        })
    
    return render_template('prestamos_libros/lista.html', prestamos=prestamos_con_dias, titulo=titulo, pagination=pagination, busqueda=busqueda, estado=estado)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_prestamo():
    if current_user.rol in ['administrador', 'bibliotecario']:
        if request.method == 'GET':
            libros = Libro.query.filter_by(disponible_prestamo=True, estado='disponible').limit(100).all()
            usuarios = Usuario.query.filter(Usuario.rol.in_(['aprendiz', 'instructor'])).limit(100).all()
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
            
            # Re-verificar disponibilidad del libro (protección contra race condition)
            libro = Libro.query.get(id_libro)
            if not libro or libro.estado != 'disponible':
                flash('El libro ya no está disponible. Otro usuario pudo haberlo solicitado.', 'danger')
                return redirect(url_for('prestamos_libros.crear_prestamo'))
            
            # Crear préstamo y marcar libro como prestado
            libro.estado = 'prestado'
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
            db.session.add(prestamo)
            db.session.commit()
            
            # Notificar aprobación inmediata
            enviar_notificacion_prestamo(prestamo, 'aprobado', mail, es_libro=True)
            
            current_app.logger.info('Préstamo libro creado (admin): libro_id=%s, usuario_id=%s', id_libro, id_usuario)
            flash(f'Préstamo de libro creado exitosamente por {dias_prestamo} días. Se ha notificado al usuario.', 'success')
            return redirect(url_for('prestamos_libros.lista_prestamos'))
    else:
        if request.method == 'GET':
            id_libro = request.args.get('id_libro', type=int)
            libros = Libro.query.filter_by(disponible_prestamo=True, estado='disponible').limit(100).all()
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
            
            # Fix #9: Verificar límite de préstamos activos del usuario
            if current_user.prestamos_activos_count() >= current_user.limite_prestamos:
                flash(f'Has alcanzado el límite de {current_user.limite_prestamos} préstamos activos.', 'warning')
                return redirect(url_for('prestamos_libros.lista_prestamos'))
            
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
            db.session.commit()
            
            # Notificar solicitud recibida
            enviar_notificacion_prestamo(prestamo, 'pendiente', mail, es_libro=True)
            
            flash('Solicitud de préstamo de libro enviada. Se te ha notificado por correo. El administrador la revisará.', 'info')
            return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>/aceptar', methods=['POST'])
@login_required
@gestion_libros_required
def aceptar_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    # Re-verificar estado actual del libro (protección contra race condition)
    libro = Libro.query.get(prestamo.id_libro)
    if not libro or libro.estado != 'disponible':
        flash('El libro ya no está disponible. Puede haber sido prestado a otro usuario.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    prestamo.estado = 'aceptado'
    prestamo.fecha_aprobacion = datetime.now(timezone.utc)
    prestamo.id_administrador = current_user.id_usuario
    libro.estado = 'prestado'
    db.session.commit()
    
    # Notificar aprobación
    enviar_notificacion_prestamo(prestamo, 'aprobado', mail, es_libro=True)
    
    current_app.logger.info('Préstamo libro aceptado: id=%s, libro=%s', id_prestamo, libro.titulo)
    flash('Préstamo aceptado y notificado al usuario.', 'success')
    return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>/rechazar', methods=['POST'])
@login_required
@gestion_libros_required
def rechazar_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if prestamo.estado != 'pendiente':
        flash('Este préstamo no está en estado pendiente.', 'warning')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    prestamo.estado = 'rechazado'
    razon = request.form.get('razon_rechazo', '')
    
    # Fix #8: Validar longitud de razón de rechazo
    if len(razon) > 255:
        flash('La razón de rechazo no puede exceder 255 caracteres.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    prestamo.razon_rechazo = razon
    prestamo.id_administrador = current_user.id_usuario
    prestamo.save()
    db.session.commit()
    
    # Notificar rechazo
    enviar_notificacion_prestamo(prestamo, 'rechazado', mail, es_libro=True)
    
    current_app.logger.info('Préstamo libro rechazado: id=%s', id_prestamo)
    flash('Préstamo rechazado y notificación enviada.', 'success')
    return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>/devolver', methods=['POST'])
@login_required
@gestion_libros_required
def devolver_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if prestamo.estado != 'aceptado':
        flash('Este préstamo no está en estado aceptado.', 'warning')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
        
    estado_fisico = request.form.get('estado_fisico')
    estado_final = request.form.get('estado_final')
    observacion_devolucion = request.form.get('observacion_devolucion')
    
    if not observacion_devolucion or observacion_devolucion.strip() == '':
        flash('Debes ingresar una observación para la devolución.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
        
    if not estado_fisico or not estado_final:
        flash('Debes seleccionar el estado físico y la acción final.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
        
    estados_fisicos_validos = ['excelente', 'bueno', 'regular', 'deteriorado', 'dañado']
    if estado_fisico not in estados_fisicos_validos:
        flash('Estado físico inválido.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
        
    estados_finales_validos = ['disponible', 'mantenimiento', 'no_disponible']
    if estado_final not in estados_finales_validos:
        flash('Estado final inválido.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    estado_anterior = prestamo.libro.estado
    
    prestamo.estado = 'devuelto'
    prestamo.fecha_devolucion_real = datetime.now(timezone.utc)
    prestamo.observacion_devolucion = observacion_devolucion
    prestamo.estado_fisico_devolucion = estado_fisico
    
    prestamo.libro.estado = estado_final
    prestamo.save()
    
    # Registro en historial de estados del libro
    if estado_anterior != estado_final:
        historial = HistorialEstadoLibro(
            id_libro=prestamo.id_libro,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_final,
            observacion=f"Cambio por devolución. Físico: {estado_fisico}. Obs: {observacion_devolucion}",
            id_administrador=current_user.id_usuario
        )
        db.session.add(historial)
        
    # Verificar y activar suspensión si aplica
    from app.services.multas_service import activar_suspension
    multa_generada = activar_suspension(prestamo, es_libro=True)
        
    db.session.commit()
    
    # Notificar devolución
    enviar_notificacion_prestamo(prestamo, 'devuelto', mail, es_libro=True)
    
    if multa_generada:
        from app.services.email_service import enviar_notificacion_multa
        enviar_notificacion_multa(multa_generada, 'activa', mail)
        flash(f'El usuario ha sido suspendido por {multa_generada.dias_suspension} días debido a retraso en la devolución.', 'warning')
    
    current_app.logger.info('Préstamo libro devuelto: id=%s, estado_fisico=%s, estado_final=%s', id_prestamo, estado_fisico, estado_final)
    flash(f'Préstamo marcado como devuelto. El libro pasó a estado {estado_final}.', 'success')
    return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>')
@login_required
def detalle_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if current_user.rol not in ['administrador', 'bibliotecario'] and prestamo.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para ver este préstamo.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    dias_restantes = calcular_dias_restantes(prestamo)
    return render_template('prestamos_libros/detalle.html', prestamo=prestamo, dias_restantes=dias_restantes)

@bp.route('/<int:id_prestamo>/renovar', methods=['POST'])
@login_required
def solicitar_renovacion(id_prestamo):
    """Solicitar renovación de préstamo de libro (Usuario)"""
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    
    if prestamo.id_usuario != current_user.id_usuario and current_user.rol not in ['administrador', 'bibliotecario']:
        flash('No tienes permiso para renovar este préstamo.', 'danger')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))

    if current_user.tiene_multas_pendientes() and current_user.rol not in ['administrador', 'bibliotecario']:
        flash('No puedes renovar préstamos porque tienes una sanción por retraso activa o en proceso.', 'danger')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))

    if prestamo.estado != 'aceptado':
        flash('Solo puedes renovar préstamos activos (aceptados).', 'warning')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))

    if prestamo.fecha_devolucion_esperada and prestamo.fecha_devolucion_esperada < datetime.now(timezone.utc).replace(tzinfo=None):
        flash('No puedes renovar un préstamo vencido.', 'danger')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))

    if prestamo.estado_renovacion == 'pendiente':
        flash('Ya tienes una solicitud de renovación pendiente para este préstamo.', 'warning')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))

    limite = {'aprendiz': 1, 'instructor': 2}.get(current_user.rol, float('inf'))
    if prestamo.renovaciones_aplicadas >= limite:
        flash(f'Has alcanzado el límite máximo de renovaciones permitidas para tu rol ({limite}).', 'danger')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))
    
    motivo = request.form.get('motivo_renovacion')
    if not motivo or not motivo.strip():
        flash('Debes proporcionar un motivo para la renovación.', 'danger')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))

    from app.models.renovaciones import RenovacionLibro
    dias_extra = prestamo.libro.tiempo_max_prestamo or 15
    nueva_esperada = prestamo.fecha_devolucion_esperada + timedelta(days=dias_extra)
    
    renovacion = RenovacionLibro(
        id_prestamo_libro=id_prestamo,
        id_usuario=current_user.id_usuario,
        fecha_esperada_original=prestamo.fecha_devolucion_esperada,
        fecha_esperada_nueva=nueva_esperada,
        motivo_solicitud=motivo,
        estado='pendiente'
    )
    renovacion.save()
    
    prestamo.estado_renovacion = 'pendiente'
    db.session.commit()
    
    # Notificar solicitud de renovación
    enviar_notificacion_prestamo(prestamo, 'renovacion_solicitada', mail, es_libro=True)
    
    current_app.logger.info('Solicitud de renovación libro creada: prestamo_id=%s, usuario_id=%s', id_prestamo, current_user.id_usuario)
    flash('Solicitud de renovación enviada correctamente. Espera la aprobación del administrador/bibliotecario.', 'success')
    return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))

@bp.route('/<int:id_prestamo>/procesar_renovacion', methods=['POST'])
@login_required
@gestion_libros_required
def procesar_renovacion(id_prestamo):
    """Aprobar o rechazar renovación de préstamo de libro (Admin/Bibliotecario)"""
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    
    if prestamo.estado_renovacion != 'pendiente':
        flash('No hay ninguna solicitud de renovación pendiente para este préstamo.', 'warning')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))
        
    accion = request.form.get('accion') # 'aprobar' o 'rechazar'
    motivo_rechazo = request.form.get('motivo_rechazo', '')
    
    from app.models.renovaciones import RenovacionLibro
    renovacion = RenovacionLibro.query.filter_by(id_prestamo_libro=id_prestamo, estado='pendiente').order_by(RenovacionLibro.fecha_solicitud.desc()).first()
    
    if not renovacion:
        prestamo.estado_renovacion = None
        db.session.commit()
        flash('Error: No se encontró la solicitud de renovación.', 'danger')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))
    
    renovacion.id_administrador = current_user.id_usuario
    renovacion.fecha_respuesta = datetime.now(timezone.utc)
    
    if accion == 'aprobar':
        renovacion.estado = 'aprobada'
        prestamo.estado_renovacion = 'aprobada'
        prestamo.fecha_devolucion_esperada = renovacion.fecha_esperada_nueva
        prestamo.renovaciones_aplicadas += 1
        prestamo.notificacion_vencimiento_enviada = False
        prestamo.notificacion_vencido_enviada = False
        flash('Renovación aprobada exitosamente.', 'success')
        enviar_notificacion_prestamo(prestamo, 'renovado', mail, es_libro=True)
    elif accion == 'rechazar':
        if not motivo_rechazo.strip():
            flash('Debes proporcionar un motivo para rechazar la renovación.', 'danger')
            return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))
        renovacion.estado = 'rechazada'
        renovacion.motivo_rechazo = motivo_rechazo
        prestamo.estado_renovacion = 'rechazada'
        flash('Renovación rechazada.', 'info')
        enviar_notificacion_prestamo(prestamo, 'renovacion_rechazada', mail, es_libro=True)
    else:
        flash('Acción inválida.', 'danger')
        return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))
        
    db.session.commit()
    current_app.logger.info('Renovación de libro procesada: prestamo_id=%s, accion=%s, admin_id=%s', id_prestamo, accion, current_user.id_usuario)
    return redirect(url_for('prestamos_libros.detalle_prestamo', id_prestamo=id_prestamo))
