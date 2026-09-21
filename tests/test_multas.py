"""
Pruebas unitarias y de integración para el módulo de Multas/Sanciones.

Cubre:
1. Blueprint /multas (lista con filtros por rol y condonación).
2. Servicio multas_service (activar_suspension y actualizar_multas_diarias).
"""
from datetime import UTC, datetime, timedelta

from app import db
from app.models.multas import Multa
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro
from app.services.multas_service import activar_suspension, actualizar_multas_diarias

# ─────────────────────────────────────────────────────────────────────────────
# BLUEPRINT: LISTADO DE MULTAS
# ─────────────────────────────────────────────────────────────────────────────

def test_lista_multas_aprendiz_solo_las_suyas(aprendiz_client, aprendiz_user, sample_prestamo_equipo):
    """Un aprendiz solo debe ver sus propias multas."""
    multa_propia = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=3,
        dias_suspension=3,
        estado='activa'
    )
    multa_propia.save()
    db.session.commit()

    response = aprendiz_client.get('/multas/')
    assert response.status_code == 200
    assert len(aprendiz_user.multas) == 1


def test_lista_multas_bibliotecario_solo_libros(bibliotecario_client, aprendiz_user, sample_prestamo_libro):
    """Un bibliotecario solo ve multas de tipo libro."""
    multa = Multa(
        tipo_recurso='libro',
        id_prestamo_libro=sample_prestamo_libro.id_prestamo_libro,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=2,
        dias_suspension=2,
        estado='acumulando'
    )
    multa.save()
    db.session.commit()

    response = bibliotecario_client.get('/multas/')
    assert response.status_code == 200
    assert len(Multa.query.filter_by(tipo_recurso='libro').all()) == 1


def test_lista_multas_almacenista_solo_equipos(almacenista_client, aprendiz_user, sample_prestamo_equipo):
    """Un almacenista solo ve multas de tipo equipo."""
    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=4,
        dias_suspension=4,
        estado='activa'
    )
    multa.save()
    db.session.commit()

    response = almacenista_client.get('/multas/')
    assert response.status_code == 200
    assert len(Multa.query.filter_by(tipo_recurso='equipo').all()) == 1


def test_lista_multas_filtro_estado(admin_client, aprendiz_user, sample_prestamo_equipo):
    """El filtro por estado debe devolver solo las multas con ese estado."""
    multa_activa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=3,
        dias_suspension=3,
        estado='activa'
    )
    multa_activa.save()
    db.session.commit()

    response = admin_client.get('/multas/?estado=activa')
    assert response.status_code == 200
    assert len(Multa.query.filter_by(estado='activa').all()) == 1


# ─────────────────────────────────────────────────────────────────────────────
# BLUEPRINT: CONDONACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def test_condonar_multa_admin(admin_client, admin_user, aprendiz_user, sample_prestamo_equipo):
    """POST /multas/<id>/condonar por admin condona la multa con observación."""
    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=5,
        dias_suspension=5,
        estado='activa'
    )
    multa.save()
    db.session.commit()

    response = admin_client.post(f'/multas/{multa.id_multa}/condonar', data={
        'observacion': 'Se condona por buen comportamiento del aprendiz.'
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/multas/' in response.headers.get('Location', '')

    db.session.refresh(multa)
    assert multa.estado == 'condonada'
    assert multa.observacion == 'Se condona por buen comportamiento del aprendiz.'
    assert multa.id_administrador_resolucion == admin_user.id_usuario
    assert multa.fecha_fin_suspension is not None


def test_condonar_multa_requiere_observacion(admin_client, aprendiz_user, sample_prestamo_equipo):
    """Condonar sin observación debe ser rechazado."""
    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=2,
        dias_suspension=2,
        estado='activa'
    )
    multa.save()
    db.session.commit()

    response = admin_client.post(f'/multas/{multa.id_multa}/condonar', data={
        'observacion': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(multa)
    assert multa.estado == 'activa'


def test_condonar_multa_bibliotecario_no_equipos(bibliotecario_client, aprendiz_user, sample_prestamo_equipo):
    """Un bibliotecario no puede condonar multas de equipos."""
    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=3,
        dias_suspension=3,
        estado='activa'
    )
    multa.save()
    db.session.commit()

    response = bibliotecario_client.post(f'/multas/{multa.id_multa}/condonar', data={
        'observacion': 'Intento no autorizado.'
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(multa)
    assert multa.estado == 'activa'


def test_condonar_multa_aprendiz_denegado(aprendiz_client, aprendiz_user, sample_prestamo_equipo):
    """Un aprendiz nunca puede condonar multas."""
    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=2,
        dias_suspension=2,
        estado='activa'
    )
    multa.save()
    db.session.commit()

    response = aprendiz_client.post(f'/multas/{multa.id_multa}/condonar', data={
        'observacion': 'Intento de auto-condonación.'
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(multa)
    assert multa.estado == 'activa'


def test_condonar_multa_ya_cumplida(admin_client, aprendiz_user, sample_prestamo_equipo):
    """Condonar una multa ya cumplida debe ser rechazado."""
    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=sample_prestamo_equipo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=2,
        dias_suspension=2,
        estado='cumplida'
    )
    multa.save()
    db.session.commit()

    response = admin_client.post(f'/multas/{multa.id_multa}/condonar', data={
        'observacion': 'Demasiado tarde.'
    }, follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(multa)
    assert multa.estado == 'cumplida'


# ─────────────────────────────────────────────────────────────────────────────
# SERVICIO: ACTIVAR SUSPENSIÓN
# ─────────────────────────────────────────────────────────────────────────────

def test_activar_suspension_por_retraso(app, aprendiz_user, sample_equipo):
    """activar_suspension debe crear una multa activa cuando hay retraso real."""
    ahora = datetime.now(UTC)
    prestamo = Prestamo(
        id_equipo=sample_equipo.id_equipo,
        id_usuario=aprendiz_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora - timedelta(days=5)
    )
    prestamo.save()
    db.session.commit()

    multa = activar_suspension(prestamo, es_libro=False)
    db.session.commit()

    assert multa is not None
    assert multa.estado == 'activa'
    assert multa.tipo_recurso == 'equipo'
    assert multa.dias_retraso >= 5
    assert multa.dias_suspension == multa.dias_retraso
    assert multa.fecha_inicio_suspension is not None
    assert multa.fecha_fin_suspension is not None


def test_activar_suspension_dentro_de_gracia(app, aprendiz_user, sample_equipo):
    """activar_suspension no debe generar multa si se devolvió dentro de la gracia."""
    ahora = datetime.now(UTC)
    prestamo = Prestamo(
        id_equipo=sample_equipo.id_equipo,
        id_usuario=aprendiz_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora
    )
    prestamo.save()
    db.session.commit()

    multa = activar_suspension(prestamo, es_libro=False)
    db.session.commit()

    assert multa is None
    assert Multa.query.count() == 0


def test_activar_suspension_libro(app, aprendiz_user, sample_libro):
    """activar_suspension debe funcionar para préstamos de libros."""
    ahora = datetime.now(UTC)
    prestamo = PrestamoLibro(
        id_libro=sample_libro.id_libro,
        id_usuario=aprendiz_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora - timedelta(days=10)
    )
    prestamo.save()
    db.session.commit()

    multa = activar_suspension(prestamo, es_libro=True)
    db.session.commit()

    assert multa is not None
    assert multa.estado == 'activa'
    assert multa.tipo_recurso == 'libro'
    assert multa.dias_retraso >= 10


# ─────────────────────────────────────────────────────────────────────────────
# SERVICIO: CRON DE MULTAS DIARIAS
# ─────────────────────────────────────────────────────────────────────────────

def test_cron_crea_multa_acumulando_para_prestamo_vencido(app, aprendiz_user, sample_equipo):
    """El cron debe crear una multa 'acumulando' para préstamos vencidos."""
    ahora = datetime.now(UTC)
    prestamo = Prestamo(
        id_equipo=sample_equipo.id_equipo,
        id_usuario=aprendiz_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora - timedelta(days=6)
    )
    prestamo.save()
    db.session.commit()

    actualizar_multas_diarias(app)

    multa = Multa.query.filter_by(id_prestamo_equipo=prestamo.id_prestamo).first()
    assert multa is not None
    assert multa.estado == 'acumulando'
    assert multa.tipo_recurso == 'equipo'
    assert multa.dias_retraso >= 5


def test_cron_marca_cumplidas_multas_vencidas(app, aprendiz_user, sample_equipo):
    """El cron debe marcar como 'cumplida' las multas activas cuyo tiempo ya terminó."""
    ahora = datetime.now(UTC)
    prestamo = Prestamo(
        id_equipo=sample_equipo.id_equipo,
        id_usuario=aprendiz_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora - timedelta(days=2)
    )
    prestamo.save()

    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=prestamo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=2,
        dias_suspension=2,
        estado='activa',
        fecha_generacion=ahora - timedelta(days=10),
        fecha_inicio_suspension=ahora - timedelta(days=10),
        fecha_fin_suspension=ahora - timedelta(days=8)
    )
    multa.save()
    db.session.commit()

    actualizar_multas_diarias(app)

    db.session.refresh(multa)
    assert multa.estado == 'cumplida'


def test_cron_no_toca_multas_activas_en_vigencia(app, aprendiz_user, sample_equipo):
    """El cron no debe marcar como cumplida una multa activa que aún está en vigencia."""
    ahora = datetime.now(UTC)
    prestamo = Prestamo(
        id_equipo=sample_equipo.id_equipo,
        id_usuario=aprendiz_user.id_usuario,
        estado='aceptado',
        fecha_solicitud=ahora,
        fecha_aprobacion=ahora,
        fecha_devolucion_esperada=ahora - timedelta(days=2)
    )
    prestamo.save()

    multa = Multa(
        tipo_recurso='equipo',
        id_prestamo_equipo=prestamo.id_prestamo,
        id_usuario=aprendiz_user.id_usuario,
        dias_retraso=2,
        dias_suspension=2,
        estado='activa',
        fecha_generacion=ahora,
        fecha_inicio_suspension=ahora,
        fecha_fin_suspension=ahora + timedelta(days=2)
    )
    multa.save()
    db.session.commit()

    actualizar_multas_diarias(app)

    db.session.refresh(multa)
    assert multa.estado == 'activa'