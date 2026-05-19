from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db, mail
from app.models.multas import Multa
from app.services.email_service import enviar_notificacion_multa
from app.decorators import role_required
from datetime import datetime, timezone

bp = Blueprint('multas', __name__, url_prefix='/multas')

@bp.route('/')
@login_required
def lista_multas():
    page = request.args.get('page', 1, type=int)
    estado_filtro = request.args.get('estado', '')
    
    from sqlalchemy.orm import joinedload
    query = Multa.query.options(
        joinedload(Multa.usuario),
        joinedload(Multa.prestamo_equipo),
        joinedload(Multa.prestamo_libro)
    )

    # Filtros por rol
    if current_user.rol in ['aprendiz', 'instructor']:
        # Solo ve sus propias multas
        query = query.filter(Multa.id_usuario == current_user.id_usuario)
    elif current_user.rol == 'bibliotecario':
        # Solo ve multas de libros
        query = query.filter(Multa.tipo_recurso == 'libro')
    elif current_user.rol == 'almacenista':
        # Solo ve multas de equipos
        query = query.filter(Multa.tipo_recurso == 'equipo')
    
    # Filtro por estado
    if estado_filtro:
        query = query.filter(Multa.estado == estado_filtro)
        
    query = query.order_by(Multa.fecha_generacion.desc())
    multas_paginadas = query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('multas/lista.html', multas=multas_paginadas, estado_filtro=estado_filtro)

@bp.route('/<int:id_multa>/condonar', methods=['POST'])
@login_required
def condonar_multa(id_multa):
    multa = Multa.query.get_or_404(id_multa)
    
    # Validar permisos
    if current_user.rol not in ['administrador', 'bibliotecario', 'almacenista']:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('multas.lista_multas'))
        
    if current_user.rol == 'bibliotecario' and multa.tipo_recurso != 'libro':
        flash('Solo puedes condonar suspensiones relacionadas con libros.', 'danger')
        return redirect(url_for('multas.lista_multas'))
        
    if current_user.rol == 'almacenista' and multa.tipo_recurso != 'equipo':
        flash('Solo puedes condonar suspensiones relacionadas con equipos.', 'danger')
        return redirect(url_for('multas.lista_multas'))
        
    if multa.estado not in ['acumulando', 'activa']:
        flash('Esta sanción ya no está activa o ya fue condonada.', 'warning')
        return redirect(url_for('multas.lista_multas'))
        
    observacion = request.form.get('observacion', '').strip()
    if not observacion:
        flash('Debes ingresar una observación para condonar la sanción.', 'warning')
        return redirect(url_for('multas.lista_multas'))
        
    # Condonar
    multa.estado = 'condonada'
    multa.observacion = observacion
    multa.id_administrador_resolucion = current_user.id_usuario
    multa.fecha_fin_suspension = datetime.now(timezone.utc) # Termina ahora
    
    try:
        db.session.commit()
        enviar_notificacion_multa(multa, 'condonada', mail)
        flash('La sanción ha sido condonada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error al condonar multa {id_multa}: {e}')
        flash('Ocurrió un error al intentar condonar la sanción.', 'danger')
        
    return redirect(url_for('multas.lista_multas'))
