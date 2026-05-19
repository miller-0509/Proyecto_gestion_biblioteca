import logging
from datetime import datetime, timezone, timedelta
from flask import current_app
from app import db
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro
from app.models.multas import Multa

logger = logging.getLogger(__name__)

def _now():
    """Retorna la fecha y hora actual en la misma zona horaria que la DB (UTC)."""
    return datetime.now(timezone.utc)

def activar_suspension(prestamo, es_libro=False):
    """
    Se llama al momento de registrar la devolución de un préstamo.
    Calcula los días de retraso finales y activa la suspensión si aplica.
    Nota: Esta función NO hace db.session.commit(), delega la responsabilidad a quien la llama.
    """
    ahora = _now()
    fecha_esperada = prestamo.fecha_devolucion_esperada.replace(tzinfo=timezone.utc) if prestamo.fecha_devolucion_esperada.tzinfo is None else prestamo.fecha_devolucion_esperada
    
    # Calcular retraso usando fechas para evitar off-by-one errors (horas)
    dias_gracia = current_app.config.get('DIAS_GRACIA_MULTA', 1)
    factor_dias = current_app.config.get('MULTA_DIAS_POR_RETRASO_LIBRO', 1) if es_libro else current_app.config.get('MULTA_DIAS_POR_RETRASO_EQUIPO', 1)
    
    retraso_total = (ahora.date() - fecha_esperada.date()).days
    
    # Buscar si ya existe una multa para este préstamo (sin importar el estado para evitar duplicados)
    multa = Multa.query.filter_by(
        id_prestamo_libro=prestamo.id_prestamo if es_libro else None,
        id_prestamo_equipo=None if es_libro else prestamo.id_prestamo
    ).first()

    if retraso_total > dias_gracia:
        dias_retraso = retraso_total
        dias_suspension = dias_retraso * factor_dias
        
        # Si la multa existe y fue condonada, se ignora
        if multa and multa.estado in ['condonada', 'cumplida']:
            return None
            
        if not multa:
            # Crear nueva si no existía (ej. devolvió tarde pero el cron no alcanzó a correr)
            multa = Multa(
                tipo_recurso='libro' if es_libro else 'equipo',
                id_prestamo_libro=prestamo.id_prestamo if es_libro else None,
                id_prestamo_equipo=None if es_libro else prestamo.id_prestamo,
                id_usuario=prestamo.id_usuario,
                fecha_generacion=ahora
            )
            db.session.add(multa)
        
        # Activar la suspensión
        multa.dias_retraso = dias_retraso
        multa.dias_suspension = dias_suspension
        multa.estado = 'activa'
        multa.fecha_inicio_suspension = ahora
        multa.fecha_fin_suspension = ahora + timedelta(days=dias_suspension)
        
        return multa
    elif multa and multa.estado == 'acumulando':
        # Tenía multa acumulando pero devolvió dentro de gracia (raro, pero posible si el cron corre en medio del día de gracia)
        # O se le perdonó el retraso modificando la fecha esperada. La eliminamos.
        db.session.delete(multa)
        
    return None

def actualizar_multas_diarias(app):
    """
    Función para ser llamada por el Cron.
    1. Revisa préstamos vencidos y crea multas 'acumulando'.
    2. Actualiza los días en multas 'acumulando'.
    3. Marca como 'cumplida' las multas 'activas' que ya terminaron su tiempo.
    """
    with app.app_context():
        ahora = _now()
        dias_gracia = current_app.config.get('DIAS_GRACIA_MULTA', 1)
        factor_libro = current_app.config.get('MULTA_DIAS_POR_RETRASO_LIBRO', 1)
        factor_equipo = current_app.config.get('MULTA_DIAS_POR_RETRASO_EQUIPO', 1)
        
        logger.info(f"--- Iniciando actualización de multas ({ahora}) ---")
        
        nuevas = 0
        actualizadas = 0
        cumplidas = 0
        errores = 0
        
        # 1 y 2. Préstamos de Equipos vencidos sin devolver
        prestamos_vencidos = Prestamo.query.filter(
            Prestamo.estado.in_(['pendiente', 'aceptado']),
            Prestamo.fecha_devolucion_esperada < (ahora - timedelta(days=dias_gracia))
        ).all()
        
        for p in prestamos_vencidos:
            try:
                # Usar nested transaction para evitar que un error rompa el ciclo completo
                with db.session.begin_nested():
                    fecha_esperada = p.fecha_devolucion_esperada.replace(tzinfo=timezone.utc) if p.fecha_devolucion_esperada.tzinfo is None else p.fecha_devolucion_esperada
                    retraso = (ahora.date() - fecha_esperada.date()).days
                    suspension_proyectada = retraso * factor_equipo
                    
                    multa = Multa.query.filter_by(id_prestamo_equipo=p.id_prestamo).first()
                    
                    if multa:
                        if multa.estado != 'acumulando':
                            # Si ya fue condonada, ignoramos
                            continue
                        actualizadas += 1
                    else:
                        multa = Multa(
                            tipo_recurso='equipo',
                            id_prestamo_equipo=p.id_prestamo,
                            id_usuario=p.id_usuario,
                            estado='acumulando',
                            fecha_generacion=ahora
                        )
                        db.session.add(multa)
                        nuevas += 1
                    
                    multa.dias_retraso = retraso
                    multa.dias_suspension = suspension_proyectada
            except Exception as e:
                errores += 1
                logger.error(f"Error procesando préstamo equipo {p.id_prestamo}: {e}")
            
        # 1 y 2. Préstamos de Libros vencidos sin devolver
        libros_vencidos = PrestamoLibro.query.filter(
            PrestamoLibro.estado.in_(['pendiente', 'aceptado']),
            PrestamoLibro.fecha_devolucion_esperada < (ahora - timedelta(days=dias_gracia))
        ).all()
        
        for l in libros_vencidos:
            try:
                with db.session.begin_nested():
                    fecha_esperada = l.fecha_devolucion_esperada.replace(tzinfo=timezone.utc) if l.fecha_devolucion_esperada.tzinfo is None else l.fecha_devolucion_esperada
                    retraso = (ahora.date() - fecha_esperada.date()).days
                    suspension_proyectada = retraso * factor_libro
                    
                    multa = Multa.query.filter_by(id_prestamo_libro=l.id_prestamo_libro).first()
                    
                    if multa:
                        if multa.estado != 'acumulando':
                            continue
                        actualizadas += 1
                    else:
                        multa = Multa(
                            tipo_recurso='libro',
                            id_prestamo_libro=l.id_prestamo_libro,
                            id_usuario=l.id_usuario,
                            estado='acumulando',
                            fecha_generacion=ahora
                        )
                        db.session.add(multa)
                        nuevas += 1
                        
                    multa.dias_retraso = retraso
                    multa.dias_suspension = suspension_proyectada
            except Exception as e:
                errores += 1
                logger.error(f"Error procesando préstamo libro {l.id_prestamo_libro}: {e}")
            
        # 3. Revisar multas activas cuyo tiempo ya pasó
        multas_activas = Multa.query.filter(
            Multa.estado == 'activa',
            Multa.fecha_fin_suspension <= ahora
        ).all()
        
        for m in multas_activas:
            try:
                with db.session.begin_nested():
                    m.estado = 'cumplida'
                    cumplidas += 1
            except Exception as e:
                errores += 1
                logger.error(f"Error al marcar multa {m.id_multa} como cumplida: {e}")
            
        try:
            db.session.commit()
            logger.info(f"Multas procesadas: Nuevas={nuevas}, Actualizadas={actualizadas}, Cumplidas={cumplidas}, Errores={errores}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error crítico en el commit final del cron: {e}")
