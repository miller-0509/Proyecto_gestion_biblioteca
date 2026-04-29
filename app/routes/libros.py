from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.libros import Libro
from app import db
from app.decorators import admin_required

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

    query = Libro.query

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
@admin_required
def crear_libro():
    """Crear un nuevo libro"""
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        genero = request.form.get('genero', '').strip()
        codigo_unico = request.form.get('codigo_unico', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        disponible_prestamo = request.form.get('disponible_prestamo') == 'on'
        tiempo_max_prestamo = request.form.get('tiempo_max_prestamo', '')
        descripcion = request.form.get('descripcion', '').strip()

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
        flash(f'Libro "{libro.titulo}" registrado exitosamente.', 'success')
        return redirect(url_for('libros.lista_libros'))

    return render_template('libros/form.html',
                           errors=[],
                           libro=None,
                           accion='crear')

# ── Editar Libro ───────────────────────────────────────────────────────────
@bp.route('/<int:id_libro>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
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
        disponible_prestamo = request.form.get('disponible_prestamo') == 'on'
        tiempo_max_prestamo = request.form.get('tiempo_max_prestamo', '')
        descripcion = request.form.get('descripcion', '').strip()

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
        libro.estado = estado
        libro.ubicacion = ubicacion or None
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
@admin_required
def eliminar_libro(id_libro):
    """Eliminar un libro"""
    libro = Libro.query.get_or_404(id_libro)

    # Fix 6: No eliminar si tiene préstamos activos
    if libro.tiene_prestamo_activo:
        flash(f'No se puede eliminar "{libro.titulo}": tiene préstamos activos en curso.', 'danger')
        return redirect(url_for('libros.lista_libros'))

    titulo = libro.titulo
    db.session.delete(libro)
    db.session.commit()
    flash(f'Libro "{titulo}" eliminado exitosamente.', 'success')
    return redirect(url_for('libros.lista_libros'))

# ── Ver Detalles del Libro ─────────────────────────────────────────────────
@bp.route('/<int:id_libro>')
@login_required
def detalle_libro(id_libro):
    """Ver detalles de un libro"""
    libro = Libro.query.get_or_404(id_libro)
    return render_template('libros/detalle.html', libro=libro)

# ── API: Obtener libros disponibles ─────────────────────────────────────────
@bp.route('/api/disponibles', methods=['GET'])
@login_required
def api_libros_disponibles():
    """API para obtener libros disponibles para préstamo (usado por JS)"""
    libros = Libro.query.filter_by(
        estado='disponible',
        disponible_prestamo=True
    ).all()
    return jsonify([libro.to_dict() for libro in libros])
