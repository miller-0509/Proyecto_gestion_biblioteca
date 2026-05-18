from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.libros import Libro, HistorialEstadoLibro
from app import db
from app.decorators import gestion_libros_required

bp = Blueprint('libros', __name__, url_prefix='/libros')

# ── Lista de Libros ────────────────────────────────────────────────────────
@bp.route('/', methods=['GET'])
@login_required
def lista_libros():
    """Mostrar lista de todos los libros con búsqueda y filtros"""
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    estado = request.args.get('estado', '')
    genero = request.args.get('genero', '')

    query = Libro.query.filter_by(eliminado=False)

    if busqueda:
        query = query.filter(
            (Libro.titulo.ilike(f'%{busqueda}%')) |
            (Libro.autor.ilike(f'%{busqueda}%')) |
            (Libro.codigo_unico.ilike(f'%{busqueda}%'))
        )

    if estado:
        query = query.filter_by(estado=estado)

    if genero:
        query = query.filter_by(genero=genero)

    libros = query.paginate(page=page, per_page=10)
    generos = db.session.query(Libro.genero).distinct().all()

    return render_template('libros/lista.html',
                           libros=libros,
                           busqueda=busqueda,
                           estado=estado,
                           genero=genero,
                           generos=generos)

# ── Crear Nuevo Libro ──────────────────────────────────────────────────────
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@gestion_libros_required
def crear_libro():
    """Crear un nuevo libro"""
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        genero = request.form.get('genero', '').strip()
        codigo_unico = request.form.get('codigo_unico', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        fecha_compra_str = request.form.get('fecha_compra', '').strip()
        proveedor = request.form.get('proveedor', '').strip()
        responsable = request.form.get('responsable', '').strip()
        disponible_prestamo = request.form.get('disponible_prestamo') == 'on'
        tiempo_max_prestamo = request.form.get('tiempo_max_prestamo', '')
        descripcion = request.form.get('descripcion', '').strip()

        fecha_compra = None
        if fecha_compra_str:
            from datetime import datetime
            try:
                fecha_compra = datetime.strptime(fecha_compra_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        errors = Libro.validate_libro(titulo, autor, genero, codigo_unico)
        if errors:
            return render_template('libros/form.html',
                                   errors=errors,
                                   libro=None,
                                   accion='crear')

        libro = Libro(
            titulo=titulo,
            autor=autor,
            genero=genero,
            codigo_unico=codigo_unico,
            ubicacion=ubicacion or None,
            fecha_compra=fecha_compra,
            proveedor=proveedor or None,
            responsable=responsable or None,
            disponible_prestamo=disponible_prestamo,
            descripcion=descripcion or None,
        )

        if tiempo_max_prestamo:
            try:
                val = int(tiempo_max_prestamo)
                if val <= 0:
                    raise ValueError('El tiempo debe ser mayor a 0')
                libro.tiempo_max_prestamo = val
            except ValueError:
                flash('Tiempo máximo de préstamo inválido: debe ser un número entero positivo.', 'warning')

        libro.save()
        db.session.commit()
        flash(f'Libro "{libro.titulo}" registrado exitosamente.', 'success')
        return redirect(url_for('libros.lista_libros'))

    return render_template('libros/form.html',
                           errors=[],
                           libro=None,
                           accion='crear')

# ── Editar Libro ───────────────────────────────────────────────────────────
@bp.route('/<int:id_libro>/editar', methods=['GET', 'POST'])
@login_required
@gestion_libros_required
def editar_libro(id_libro):
    """Editar un libro existente"""
    libro = Libro.query.get_or_404(id_libro)

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        genero = request.form.get('genero', '').strip()
        codigo_unico = request.form.get('codigo_unico', '').strip()
        estado = request.form.get('estado', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        fecha_compra_str = request.form.get('fecha_compra', '').strip()
        proveedor = request.form.get('proveedor', '').strip()
        responsable = request.form.get('responsable', '').strip()
        disponible_prestamo = request.form.get('disponible_prestamo') == 'on'
        tiempo_max_prestamo = request.form.get('tiempo_max_prestamo', '')
        descripcion = request.form.get('descripcion', '').strip()
        
        fecha_compra = None
        if fecha_compra_str:
            from datetime import datetime
            try:
                fecha_compra = datetime.strptime(fecha_compra_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Validar que el código único sea único si cambió
        if codigo_unico != libro.codigo_unico:
            if Libro.query.filter_by(codigo_unico=codigo_unico).first():
                flash('Ya existe un libro con ese código único.', 'danger')
                return render_template('libros/form.html',
                                       errors=[],
                                       libro=libro,
                                       accion='editar')

        libro.titulo = titulo
        libro.autor = autor
        libro.genero = genero
        libro.codigo_unico = codigo_unico
        
        # Fix #5: Impedir cambio a 'disponible' si tiene préstamo activo
        if estado == 'disponible' and libro.estado != 'disponible' and libro.tiene_prestamo_activo:
            flash('No se puede marcar como disponible: el libro tiene un préstamo activo.', 'danger')
            return render_template('libros/form.html', errors=[], libro=libro, accion='editar')
        
        libro.estado = estado
        libro.ubicacion = ubicacion or None
        libro.fecha_compra = fecha_compra
        libro.proveedor = proveedor or None
        libro.responsable = responsable or None
        libro.disponible_prestamo = disponible_prestamo
        libro.descripcion = descripcion or None

        if tiempo_max_prestamo:
            try:
                val = int(tiempo_max_prestamo)
                if val <= 0:
                    raise ValueError('El tiempo debe ser mayor a 0')
                libro.tiempo_max_prestamo = val
            except ValueError:
                flash('Tiempo máximo de préstamo inválido: debe ser un número entero positivo.', 'warning')

        db.session.commit()
        flash(f'Libro "{libro.titulo}" actualizado exitosamente.', 'success')
        return redirect(url_for('libros.lista_libros'))

    return render_template('libros/form.html',
                           errors=[],
                           libro=libro,
                           accion='editar')

# ── Eliminar Libro ─────────────────────────────────────────────────────────
@bp.route('/<int:id_libro>/eliminar', methods=['POST'])
@login_required
@gestion_libros_required
def eliminar_libro(id_libro):
    """Eliminar un libro"""
    libro = Libro.query.get_or_404(id_libro)

    titulo = libro.titulo
    try:
        # Eliminación lógica
        libro.eliminado = True
        db.session.commit()
        flash(f'Libro "{titulo}" eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al intentar eliminar el libro: {str(e)}', 'danger')
        current_app.logger.error(f"Error al eliminar libro {id_libro}: {str(e)}")
            
    return redirect(url_for('libros.lista_libros'))

# ── Ver Detalles del Libro ─────────────────────────────────────────────────
@bp.route('/<int:id_libro>')
@login_required
def detalle_libro(id_libro):
    """Ver detalles de un libro"""
    libro = Libro.query.get_or_404(id_libro)
    
    # Obtener historial de estados ordenado de más reciente a más antiguo
    historial_estados = []
    if current_user.rol in ['administrador', 'bibliotecario']:
        historial_estados = HistorialEstadoLibro.query.filter_by(id_libro=id_libro).order_by(HistorialEstadoLibro.fecha.desc()).all()
        
    return render_template('libros/detalle.html', libro=libro, historial_estados=historial_estados)


# ── Actualizar Estado (Manual) ──────────────────────────────────────────────
@bp.route('/<int:id_libro>/estado', methods=['POST'])
@login_required
@gestion_libros_required
def actualizar_estado(id_libro):
    """Actualizar el estado del libro manualmente (Admin)"""
    libro = Libro.query.get_or_404(id_libro)
    
    nuevo_estado = request.form.get('estado', '').strip()
    observacion = request.form.get('observacion', '').strip()
    
    estados_permitidos = ['disponible', 'mantenimiento', 'dañado', 'perdido', 'eliminado']
    
    if not observacion:
        flash('Debe proporcionar una observación para cambiar el estado.', 'danger')
        return redirect(url_for('libros.lista_libros'))
        
    if nuevo_estado not in estados_permitidos:
        flash('Estado inválido o no permitido manualmente.', 'danger')
        return redirect(url_for('libros.lista_libros'))
        
    if nuevo_estado == 'disponible' and libro.tiene_prestamo_activo:
        flash('No se puede cambiar a "disponible" porque el libro tiene préstamos activos.', 'danger')
        return redirect(url_for('libros.lista_libros'))
        
    if nuevo_estado == 'eliminado' and libro.tiene_prestamo_activo:
        flash('No se puede eliminar el libro porque tiene préstamos activos.', 'danger')
        return redirect(url_for('libros.lista_libros'))
        
    estado_anterior = libro.estado
    
    if estado_anterior == nuevo_estado:
        flash('El libro ya se encuentra en ese estado.', 'warning')
        return redirect(url_for('libros.lista_libros'))
        
    try:
        # Registrar en el historial
        historial = HistorialEstadoLibro(
            id_libro=libro.id_libro,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            observacion=observacion,
            id_administrador=current_user.id_usuario
        )
        db.session.add(historial)
        
        # Actualizar el libro
        libro.estado = nuevo_estado
        if nuevo_estado == 'eliminado':
            libro.eliminado = True
            
        db.session.commit()
        
        current_app.logger.info(
            'Estado libro actualizado manualmente: libro_id=%s, estado_anterior=%s, estado_nuevo=%s, admin_id=%s',
            id_libro, estado_anterior, nuevo_estado, current_user.id_usuario
        )
        flash(f'Estado del libro actualizado a "{nuevo_estado}".', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error al actualizar estado del libro %s: %s', id_libro, str(e))
        flash('Ocurrió un error al actualizar el estado.', 'danger')
        
    # Redirect back to where the request came from (list or detail)
    referrer = request.referrer
    if referrer and 'libros/' in referrer and str(id_libro) in referrer:
        return redirect(url_for('libros.detalle_libro', id_libro=id_libro))
    return redirect(url_for('libros.lista_libros'))

# ── API: Obtener libros disponibles ─────────────────────────────────────────
@bp.route('/api/disponibles', methods=['GET'])
@login_required
def api_libros_disponibles():
    """API para obtener libros disponibles para préstamo (usado por JS)"""
    libros = Libro.query.filter_by(
        estado='disponible',
        disponible_prestamo=True,
        eliminado=False
    ).all()
    return jsonify([libro.to_dict() for libro in libros])
