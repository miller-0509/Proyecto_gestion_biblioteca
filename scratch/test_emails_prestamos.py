import logging
import time
from datetime import datetime, timezone, timedelta
from app import create_app, db, mail
from app.models.usuarios import Usuario
from app.models.equipos import Equipo
from app.models.prestamos import Prestamo
from app.services.email_service import enviar_notificacion_prestamo, _generar_html_notificacion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestEmails')

def test_notificaciones():
    app = create_app()
    with app.app_context():
        # Deshabilitar el envío real temporalmente si queremos solo validar, 
        # pero para probar la funcionalidad entera dejaremos que lo intente enviar o falle de manera segura.
        # Si las credenciales SMTP están bien, enviará un correo.
        
        # Obtener un usuario de prueba (admin_test u otro)
        usuario = Usuario.query.filter_by(correo='admin_test@biblioteca.com').first()
        if not usuario:
            usuario = Usuario.query.first()
            
        if not usuario:
            logger.error("No hay usuarios en la base de datos para probar.")
            return

        # Asegurarnos que tenga un correo válido temporalmente
        original_email = usuario.correo
        usuario.correo = 'test_notifications@biblioteca.com' # Email dummy o real
        
        # Obtener un equipo
        equipo = Equipo.query.first()
        if not equipo:
            logger.error("No hay equipos en la base de datos para probar.")
            return

        # Crear un préstamo dummy
        prestamo = Prestamo(
            id_usuario=usuario.id_usuario,
            id_equipo=equipo.id_equipo,
            fecha_devolucion_esperada=datetime.now(timezone.utc) + timedelta(days=5),
            estado='pendiente',
            observaciones='Test de notificaciones automáticas'
        )
        
        # Guardar en DB temporalmente (con un rollback luego)
        db.session.add(prestamo)
        db.session.commit()
        
        try:
            logger.info("--- PRUEBA 1: GENERACIÓN DE HTML ---")
            tipos = ['pendiente', 'aprobado', 'rechazado', 'devuelto', 'proximo_vencer', 'vencido']
            for tipo in tipos:
                asunto, html = _generar_html_notificacion(prestamo, tipo, es_libro=False)
                if html and asunto:
                    logger.info(f"[OK] Generado correctamente el HTML para estado: {tipo} | Asunto: {asunto}")
                else:
                    logger.error(f"[ERROR] No se generó el HTML para estado: {tipo}")
            
            logger.info("--- PRUEBA 2: ENVÍO ASÍNCRONO ---")
            logger.info("Simulando notificación 'pendiente'...")
            resultado = enviar_notificacion_prestamo(prestamo, 'pendiente', mail, es_libro=False)
            logger.info(f"Retorno de la función de envío asíncrono: {resultado}")
            
            # Esperar un momento para ver si el hilo secundario arroja errores
            time.sleep(2)
            
        finally:
            # Restaurar estado original
            usuario.correo = original_email
            db.session.delete(prestamo)
            db.session.commit()
            logger.info("Base de datos restaurada. Prueba finalizada.")

if __name__ == '__main__':
    test_notificaciones()
