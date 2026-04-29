from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
from app import db
from app.models.prestamos_libros import PrestamoLibro
from app.models.libros import Libro
from app.models.usuarios import Usuario
from app.decorators import admin_required, calcular_dias_restantes

bp = Blueprint('prestamos_libros', __name__, url_prefix='/prestamos-libros')


@bp.route('/lista')
@login_required
def lista_prestamos():
    if current_user.rol == 'administrador':
        prestamos = PrestamoLibro.query.options(
            joinedload(PrestamoLibro.usuario),
            joinedload(PrestamoLibro.libro)
        ).order_by(PrestamoLibro.fecha_solicitud.desc()).limit(100).all()
        titulo = 'Gestión de Préstamos de Libros'
    else:
        prestamos = PrestamoLibro.query.options(
            joinedload(PrestamoLibro.libro)
        ).filter_by(id_usuario=current_user.id_usuario).order_by(
            PrestamoLibro.fecha_solicitud.desc()
        ).limit(100).all()
        titulo = 'Mis Préstamos de Libros'
    
    # Usar función compartida para calcular días restantes
    prestamos_con_dias = []
    for prestamo in prestamos:
        prestamos_con_dias.append({
            'prestamo': prestamo,
            'dias_restantes': calcular_dias_restantes(prestamo)
        })
    
    return render_template('prestamos_libros/lista.html', prestamos=prestamos_con_dias, titulo=titulo)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_prestamo():
    if current_user.rol == 'administrador':
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
            
            current_app.logger.info('Préstamo libro creado (admin): libro_id=%s, usuario_id=%s', id_libro, id_usuario)
            flash(f'Préstamo de libro creado exitosamente por {dias_prestamo} días.', 'success')
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
    
    current_app.logger.info('Préstamo libro aceptado: id=%s, libro=%s', id_prestamo, libro.titulo)
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
    
    current_app.logger.info('Préstamo libro rechazado: id=%s', id_prestamo)
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
    prestamo.libro.estado = 'disponible'
    prestamo.save()
    
    current_app.logger.info('Préstamo libro devuelto: id=%s', id_prestamo)
    flash('Préstamo marcado como devuelto.', 'success')
    return redirect(url_for('prestamos_libros.lista_prestamos'))


@bp.route('/<int:id_prestamo>')
@login_required
def detalle_prestamo(id_prestamo):
    prestamo = PrestamoLibro.query.get_or_404(id_prestamo)
    if current_user.rol != 'administrador' and prestamo.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para ver este préstamo.', 'danger')
        return redirect(url_for('prestamos_libros.lista_prestamos'))
    
    dias_restantes = calcular_dias_restantes(prestamo)
    return render_template('prestamos_libros/detalle.html', prestamo=prestamo, dias_restantes=dias_restantes)
