import logging
from datetime import datetime, timezone, timedelta
from app import create_app, db, mail
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro
from app.services.email_service import enviar_notificacion_prestamo

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Recordatorios')

def procesar_recordatorios():
    """
    Busca préstamos activos (equipos y libros) próximos a vencer o vencidos
    y envía las notificaciones automáticas correspondientes por correo.
    """
    app = create_app()
    with app.app_context():
        logger.info("Iniciando proceso de revisión de recordatorios...")
        ahora = datetime.now(timezone.utc)
        un_dia_despues = ahora + timedelta(days=1)
        
        prestamos_procesados = 0
        errores = 0

        # Mapeo de los modelos para iterar limpiamente
        modelos_prestamos = [
            (Prestamo, False),       # Modelo Equipos, es_libro=False
            (PrestamoLibro, True)    # Modelo Libros, es_libro=True
        ]

        for Modelo, es_libro in modelos_prestamos:
            tipo = "Libros" if es_libro else "Equipos"
            logger.info(f"Revisando préstamos de {tipo}...")
            
            # Buscar préstamos aceptados que no hayan sido devueltos
            activos = Modelo.query.filter_by(estado='aceptado').all()
            
            for prestamo in activos:
                if not prestamo.fecha_devolucion_esperada:
                    continue
                    
                # Si la fecha de devolución no tiene zona horaria, se la asignamos (UTC)
                fecha_limite = prestamo.fecha_devolucion_esperada
                if fecha_limite.tzinfo is None:
                    fecha_limite = fecha_limite.replace(tzinfo=timezone.utc)
                
                try:
                    # 1. Verificar si está vencido
                    if fecha_limite < ahora and not prestamo.notificacion_vencido_enviada:
                        logger.info(f"Enviando aviso de VENCIDO para préstamo ID {prestamo.id_prestamo}")
                        enviado = enviar_notificacion_prestamo(prestamo, 'vencido', mail, es_libro)
                        if enviado:
                            prestamo.notificacion_vencido_enviada = True
                            # Si ya se venció, asumimos que no necesita la notificación de "próximo a vencer"
                            prestamo.notificacion_vencimiento_enviada = True 
                            db.session.commit()
                            prestamos_procesados += 1
                            
                    # 2. Verificar si está próximo a vencer (menos de 24h restantes)
                    elif ahora <= fecha_limite <= un_dia_despues and not prestamo.notificacion_vencimiento_enviada:
                        logger.info(f"Enviando aviso PROXIMO A VENCER para préstamo ID {prestamo.id_prestamo}")
                        enviado = enviar_notificacion_prestamo(prestamo, 'proximo_vencer', mail, es_libro)
                        if enviado:
                            prestamo.notificacion_vencimiento_enviada = True
                            db.session.commit()
                            prestamos_procesados += 1

                except Exception as e:
                    logger.error(f"Error procesando préstamo {prestamo.id_prestamo}: {str(e)}")
                    db.session.rollback()
                    errores += 1

        logger.info(f"Proceso finalizado. Notificaciones enviadas: {prestamos_procesados}. Errores: {errores}")

if __name__ == '__main__':
    procesar_recordatorios()
