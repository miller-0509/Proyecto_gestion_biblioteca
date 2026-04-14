from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.equipos import Equipo
from app import db
from functools import wraps

bp = Blueprint('equipos', __name__, url_prefix='/equipos')


def admin_required(f):
    """Decorador para requerer permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'administrador':
            flash('No tienes permisos para acceder a esta sección. Solo administrador.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ── Lista de Equipos ────────────────────────────────────────────────────────
@bp.route('/', methods=['GET'])
@login_required
def lista_equipos():
    """Mostrar lista de todos los equipos con búsqueda y filtros (accesible para todos)"""
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    estado = request.args.get('estado', '')
    tipo = request.args.get('tipo', '')

    query = Equipo.query

    if busqueda:
        query = query.filter(
            (Equipo.nombre.ilike(f'%{busqueda}%')) |
            (Equipo.numero_serie.ilike(f'%{busqueda}%')) |
            (Equipo.marca.ilike(f'%{busqueda}%'))
        )

    if estado:
        query = query.filter_by(estado=estado)

    if tipo:
        query = query.filter_by(tipo_equipo=tipo)

    equipos = query.paginate(page=page, per_page=10)
    tipos = db.session.query(Equipo.tipo_equipo).distinct().all()

    return render_template('equipos/lista.html',
                          equipos=equipos,
                          busqueda=busqueda,
                          estado=estado,
                          tipo=tipo,
                          tipos=tipos)


# ── Crear Nuevo Equipo ──────────────────────────────────────────────────────
@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_equipo():
    """Crear un nuevo equipo"""
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        tipo_equipo = request.form.get('tipo_equipo', '').strip()
        marca = request.form.get('marca', '').strip()
        modelo = request.form.get('modelo', '').strip()
        numero_serie = request.form.get('numero_serie', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        fecha_compra = request.form.get('fecha_compra', '')
        proveedor = request.form.get('proveedor', '').strip()
        responsable = request.form.get('responsable', '').strip()
        disponible_prestamo = request.form.get('disponible_prestamo') == 'on'
        tiempo_max_prestamo = request.form.get('tiempo_max_prestamo', '')
        descripcion = request.form.get('descripcion', '').strip()

        errors = Equipo.validate_equipo(nombre, tipo_equipo, numero_serie)
        if errors:
            return render_template('equipos/form.html',
                                  errors=errors,
                                  equipo=None,
                                  accion='crear')

        equipo = Equipo(
            nombre=nombre,
            tipo_equipo=tipo_equipo,
            marca=marca or None,
            modelo=modelo or None,
            numero_serie=numero_serie,
            ubicacion=ubicacion or None,
            proveedor=proveedor or None,
            responsable=responsable or None,
            disponible_prestamo=disponible_prestamo,
            descripcion=descripcion or None,
        )

        if fecha_compra:
            try:
                from datetime import datetime
                equipo.fecha_compra = datetime.strptime(fecha_compra, '%Y-%m-%d').date()
            except:
                pass

        if tiempo_max_prestamo:
            try:
                equipo.tiempo_max_prestamo = int(tiempo_max_prestamo)
            except:
                pass

        equipo.save()
        flash(f'Equipo "{equipo.nombre}" registrado exitosamente.', 'success')
        return redirect(url_for('equipos.lista_equipos'))

    return render_template('equipos/form.html',
                          errors=[],
                          equipo=None,
                          accion='crear')


# ── Editar Equipo ───────────────────────────────────────────────────────────
@bp.route('/<int:id_equipo>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_equipo(id_equipo):
    """Editar un equipo existente"""
    equipo = Equipo.query.get_or_404(id_equipo)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        tipo_equipo = request.form.get('tipo_equipo', '').strip()
        marca = request.form.get('marca', '').strip()
        modelo = request.form.get('modelo', '').strip()
        numero_serie = request.form.get('numero_serie', '').strip()
        estado = request.form.get('estado', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        fecha_compra = request.form.get('fecha_compra', '')
        proveedor = request.form.get('proveedor', '').strip()
        responsable = request.form.get('responsable', '').strip()
        disponible_prestamo = request.form.get('disponible_prestamo') == 'on'
        tiempo_max_prestamo = request.form.get('tiempo_max_prestamo', '')
        descripcion = request.form.get('descripcion', '').strip()

        # Validar que el número de serie sea único (si cambió)
        if numero_serie != equipo.numero_serie:
            if Equipo.query.filter_by(numero_serie=numero_serie).first():
                flash('Ya existe un equipo con ese número de serie.', 'danger')
                return render_template('equipos/form.html',
                                      errors=[],
                                      equipo=equipo,
                                      accion='editar')

        equipo.nombre = nombre
        equipo.tipo_equipo = tipo_equipo
        equipo.marca = marca or None
        equipo.modelo = modelo or None
        equipo.numero_serie = numero_serie
        equipo.estado = estado
        equipo.ubicacion = ubicacion or None
        equipo.proveedor = proveedor or None
        equipo.responsable = responsable or None
        equipo.disponible_prestamo = disponible_prestamo
        equipo.descripcion = descripcion or None

        if fecha_compra:
            try:
                from datetime import datetime
                equipo.fecha_compra = datetime.strptime(fecha_compra, '%Y-%m-%d').date()
            except:
                pass

        if tiempo_max_prestamo:
            try:
                equipo.tiempo_max_prestamo = int(tiempo_max_prestamo)
            except:
                pass

        db.session.commit()
        flash(f'Equipo "{equipo.nombre}" actualizado exitosamente.', 'success')
        return redirect(url_for('equipos.lista_equipos'))

    return render_template('equipos/form.html',
                          errors=[],
                          equipo=equipo,
                          accion='editar')


# ── Eliminar Equipo ─────────────────────────────────────────────────────────
@bp.route('/<int:id_equipo>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_equipo(id_equipo):
    """Eliminar un equipo"""
    equipo = Equipo.query.get_or_404(id_equipo)
    nombre = equipo.nombre
    db.session.delete(equipo)
    db.session.commit()
    flash(f'Equipo "{nombre}" eliminado exitosamente.', 'success')
    return redirect(url_for('equipos.lista_equipos'))


# ── Ver Detalles del Equipo ─────────────────────────────────────────────────
@bp.route('/<int:id_equipo>')
@login_required
def detalle_equipo(id_equipo):
    """Ver detalles de un equipo (accesible para todos)"""
    equipo = Equipo.query.get_or_404(id_equipo)
    return render_template('equipos/detalle.html', equipo=equipo)


# ── API: Obtener equipos disponibles ─────────────────────────────────────────
@bp.route('/api/disponibles', methods=['GET'])
@login_required
def api_equipos_disponibles():
    """API para obtener equipos disponibles para préstamo (usado por JS)"""
    equipos = Equipo.query.filter_by(
        estado='disponible',
        disponible_prestamo=True
    ).all()
    return jsonify([equipo.to_dict() for equipo in equipos])
