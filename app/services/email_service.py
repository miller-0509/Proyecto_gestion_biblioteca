"""
Servicio de correo electrónico profesional para verificación y notificaciones.

Arquitectura modular: este servicio centraliza la generación de tokens,
el envío de correos y las plantillas HTML, reutilizable para futuras
funcionalidades como recuperación de contraseña y notificaciones.
"""
import logging
import threading
from datetime import datetime, timezone
from flask import url_for, current_app, render_template
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────
TOKEN_SALT_VERIFICACION = 'verificacion-email-v1'
TOKEN_SALT_RECUPERACION = 'recuperar-password-v1'  # Preparado para futuro uso
TOKEN_EXPIRACION_SEGUNDOS = 3600  # 1 hora


def _get_serializer():
    """Obtiene el serializador criptográfico usando la SECRET_KEY de la app."""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


# ── Generación y Validación de Tokens ─────────────────────────────────────

def generar_token_verificacion(correo):
    """Genera un token firmado criptográficamente para verificación de email.
    
    El token contiene el correo cifrado y un timestamp. Es imposible de 
    falsificar sin conocer la SECRET_KEY del servidor.
    """
    s = _get_serializer()
    token = s.dumps(correo, salt=TOKEN_SALT_VERIFICACION)
    logger.info('Token de verificación generado para: %s', correo)
    return token


def verificar_token(token, max_age=TOKEN_EXPIRACION_SEGUNDOS):
    """Valida un token de verificación.
    
    Returns:
        str: El correo electrónico si el token es válido.
        None: Si el token es inválido o expiró.
    """
    s = _get_serializer()
    try:
        correo = s.loads(token, salt=TOKEN_SALT_VERIFICACION, max_age=max_age)
        logger.info('Token verificado exitosamente para: %s', correo)
        return correo
    except SignatureExpired:
        logger.warning('Token expirado (max_age=%ds)', max_age)
        return None
    except BadSignature:
        logger.warning('Token inválido o manipulado detectado')
        return None
    except Exception as e:
        logger.error('Error inesperado verificando token: %s', str(e))
        return None


# ── Envío de Correos ──────────────────────────────────────────────────────

def enviar_correo_verificacion(usuario, mail_instance):
    """Envía el correo de verificación con diseño HTML profesional.
    
    Args:
        usuario: Instancia del modelo Usuario.
        mail_instance: Instancia de Flask-Mail inicializada.
    
    Returns:
        bool: True si se envió correctamente, False si falló.
    """
    try:
        token = generar_token_verificacion(usuario.correo)
        enlace = url_for('auth.verificar_email', token=token, _external=True)
        
        msg = Message(
            subject='✉️ Verifica tu correo - Sistema SENA Biblioteca',
            recipients=[usuario.correo],
            html=_generar_html_verificacion(usuario, enlace),
        )
        
        mail_instance.send(msg)
        
        logger.info(
            'Email de verificación enviado exitosamente a: %s (ID: %s)',
            usuario.correo, usuario.id_usuario
        )
        return True
        
    except Exception as e:
        logger.error(
            'Error enviando email de verificación a %s: %s',
            usuario.correo, str(e),
            exc_info=True
        )
        return False


# ── Plantilla HTML del Correo ─────────────────────────────────────────────

def _generar_html_verificacion(usuario, enlace):
    """Genera el HTML profesional del correo de verificación.
    
    Compatible con Gmail, Outlook, Apple Mail y clientes móviles.
    Utiliza tablas para máxima compatibilidad con clientes de correo.
    """
    expiracion_minutos = TOKEN_EXPIRACION_SEGUNDOS // 60
    año_actual = datetime.now(timezone.utc).year
    
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación de Correo - SENA</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: 'Segoe UI', Arial, Helvetica, sans-serif; -webkit-font-smoothing: antialiased;">
    
    <!-- Contenedor principal -->
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f6f9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                
                <!-- Card del email -->
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">
                    
                    <!-- Header verde SENA -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); padding: 36px 32px; text-align: center;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Sena_Colombia_logo.svg" alt="SENA" width="56" style="display: inline-block; margin-bottom: 16px; filter: brightness(10);">
                            <h1 style="color: #ffffff; font-size: 22px; font-weight: 700; margin: 0; letter-spacing: -0.02em;">
                                Verificación de Correo
                            </h1>
                            <p style="color: rgba(255,255,255,0.85); font-size: 14px; margin: 8px 0 0;">
                                Sistema de Biblioteca y Almacén SENA
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Cuerpo del mensaje -->
                    <tr>
                        <td style="padding: 36px 32px 24px;">
                            <p style="color: #374151; font-size: 16px; margin: 0 0 8px; font-weight: 600;">
                                ¡Hola, {usuario.nombres}! 👋
                            </p>
                            <p style="color: #6B7280; font-size: 14px; line-height: 1.7; margin: 0 0 28px;">
                                Gracias por registrarte en el Sistema SENA de Biblioteca y Almacén. Para completar tu registro y acceder al sistema, por favor verifica tu correo electrónico haciendo clic en el siguiente botón:
                            </p>
                            
                            <!-- Botón de verificación -->
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center" style="padding: 8px 0 28px;">
                                        <a href="{enlace}" 
                                           target="_blank"
                                           style="display: inline-block; background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 10px; font-size: 15px; font-weight: 700; letter-spacing: 0.02em; box-shadow: 0 4px 14px rgba(34, 197, 94, 0.35);">
                                            ✅ Verificar Mi Correo
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Enlace alternativo -->
                            <div style="background-color: #F9FAFB; border-radius: 10px; padding: 16px; margin-bottom: 24px;">
                                <p style="color: #6B7280; font-size: 12px; margin: 0 0 8px;">
                                    Si el botón no funciona, copia y pega este enlace en tu navegador:
                                </p>
                                <p style="color: #22C55E; font-size: 11px; word-break: break-all; margin: 0; font-family: monospace;">
                                    {enlace}
                                </p>
                            </div>
                            
                            <!-- Advertencia de seguridad -->
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="border-left: 3px solid #F59E0B; padding: 12px 16px; background: #FFFBEB; border-radius: 0 8px 8px 0;">
                                        <p style="color: #92400E; font-size: 12px; margin: 0; line-height: 1.6;">
                                            <strong>⚠️ Seguridad:</strong> Este enlace expira en <strong>{expiracion_minutos} minutos</strong>. 
                                            Si no solicitaste esta verificación, ignora este mensaje. Nunca compartas este enlace con nadie.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F9FAFB; padding: 20px 32px; text-align: center; border-top: 1px solid #E5E7EB;">
                            <p style="color: #9CA3AF; font-size: 11px; margin: 0; line-height: 1.6;">
                                © {año_actual} Sistema SENA - Biblioteca y Almacén<br>
                                Este es un correo automático, por favor no respondas.
                            </p>
                        </td>
                    </tr>
                    
                </table>
                
            </td>
        </tr>
    </table>
    
</body>
</html>'''


# ══════════════════════════════════════════════════════════════════════════════
#  RECUPERACIÓN DE CONTRASEÑA
# ══════════════════════════════════════════════════════════════════════════════

def generar_token_recuperacion(correo, password_hash):
    """Genera un token firmado para recuperación de contraseña.

    Incluye un fragmento del hash actual de la contraseña para que el token
    se invalide automáticamente si la contraseña ya fue cambiada (anti-replay).
    """
    s = _get_serializer()
    # Incluir fragmento del hash para invalidación automática tras cambio
    payload = {'correo': correo, 'ph': password_hash[:16]}
    token = s.dumps(payload, salt=TOKEN_SALT_RECUPERACION)
    logger.info('Token de recuperacion generado para: %s', correo)
    return token


def verificar_token_recuperacion(token, max_age=TOKEN_EXPIRACION_SEGUNDOS):
    """Valida un token de recuperación de contraseña.

    Returns:
        dict: {'correo': str, 'ph': str} si el token es válido.
        None: Si el token es inválido, expirado o manipulado.
    """
    s = _get_serializer()
    try:
        payload = s.loads(token, salt=TOKEN_SALT_RECUPERACION, max_age=max_age)
        logger.info('Token de recuperacion verificado para: %s', payload.get('correo'))
        return payload
    except SignatureExpired:
        logger.warning('Token de recuperacion expirado (max_age=%ds)', max_age)
        return None
    except BadSignature:
        logger.warning('Token de recuperacion invalido o manipulado')
        return None
    except Exception as e:
        logger.error('Error inesperado verificando token de recuperacion: %s', str(e))
        return None


def enviar_correo_recuperacion(usuario, mail_instance):
    """Envía el correo de recuperación de contraseña con diseño HTML profesional.

    Args:
        usuario: Instancia del modelo Usuario.
        mail_instance: Instancia de Flask-Mail inicializada.

    Returns:
        bool: True si se envió correctamente, False si falló.
    """
    try:
        token = generar_token_recuperacion(usuario.correo, usuario.password)
        enlace = url_for('auth.restablecer_password', token=token, _external=True)

        msg = Message(
            subject='🔐 Recupera tu contraseña - Sistema SENA Biblioteca',
            recipients=[usuario.correo],
            html=_generar_html_recuperacion(usuario, enlace),
        )

        mail_instance.send(msg)

        logger.info(
            'Email de recuperacion enviado exitosamente a: %s (ID: %s)',
            usuario.correo, usuario.id_usuario
        )
        return True

    except Exception as e:
        logger.error(
            'Error enviando email de recuperacion a %s: %s',
            usuario.correo, str(e),
            exc_info=True
        )
        return False


def _generar_html_recuperacion(usuario, enlace):
    """Genera el HTML profesional del correo de recuperación de contraseña.

    Compatible con Gmail, Outlook, Apple Mail y clientes móviles.
    Utiliza tablas para máxima compatibilidad con clientes de correo.
    """
    expiracion_minutos = TOKEN_EXPIRACION_SEGUNDOS // 60
    year = datetime.now(timezone.utc).year

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recuperar Contrasena - SENA</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: 'Segoe UI', Arial, Helvetica, sans-serif; -webkit-font-smoothing: antialiased;">

    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f6f9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">

                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); padding: 36px 32px; text-align: center;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Sena_Colombia_logo.svg" alt="SENA" width="56" style="display: inline-block; margin-bottom: 16px; filter: brightness(10);">
                            <h1 style="color: #ffffff; font-size: 22px; font-weight: 700; margin: 0; letter-spacing: -0.02em;">
                                Recuperar Contrasena
                            </h1>
                            <p style="color: rgba(255,255,255,0.85); font-size: 14px; margin: 8px 0 0;">
                                Sistema de Biblioteca y Almacen SENA
                            </p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 36px 32px 24px;">
                            <p style="color: #374151; font-size: 16px; margin: 0 0 8px; font-weight: 600;">
                                Hola, {usuario.nombres}
                            </p>
                            <p style="color: #6B7280; font-size: 14px; line-height: 1.7; margin: 0 0 28px;">
                                Recibimos una solicitud para restablecer la contrasena de tu cuenta en el Sistema SENA de Biblioteca y Almacen. Si tu realizaste esta solicitud, haz clic en el siguiente boton para crear una nueva contrasena:
                            </p>

                            <!-- Button -->
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center" style="padding: 8px 0 28px;">
                                        <a href="{enlace}"
                                           target="_blank"
                                           style="display: inline-block; background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 10px; font-size: 15px; font-weight: 700; letter-spacing: 0.02em; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);">
                                            Restablecer Mi Contrasena
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Alternative link -->
                            <div style="background-color: #F9FAFB; border-radius: 10px; padding: 16px; margin-bottom: 24px;">
                                <p style="color: #6B7280; font-size: 12px; margin: 0 0 8px;">
                                    Si el boton no funciona, copia y pega este enlace en tu navegador:
                                </p>
                                <p style="color: #3B82F6; font-size: 11px; word-break: break-all; margin: 0; font-family: monospace;">
                                    {enlace}
                                </p>
                            </div>

                            <!-- Security warning -->
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="border-left: 3px solid #EF4444; padding: 12px 16px; background: #FEF2F2; border-radius: 0 8px 8px 0;">
                                        <p style="color: #991B1B; font-size: 12px; margin: 0; line-height: 1.6;">
                                            <strong>Seguridad:</strong> Este enlace expira en <strong>{expiracion_minutos} minutos</strong> y solo puede usarse una vez.
                                            Si no solicitaste este cambio, ignora este mensaje. Tu contrasena actual permanecera sin cambios.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F9FAFB; padding: 20px 32px; text-align: center; border-top: 1px solid #E5E7EB;">
                            <p style="color: #9CA3AF; font-size: 11px; margin: 0; line-height: 1.6;">
                                &copy; {year} Sistema SENA - Biblioteca y Almacen<br>
                                Este es un correo automatico, por favor no respondas.
                            </p>
                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>

</body>
</html>'''

# ══════════════════════════════════════════════════════════════════════════════
#  NOTIFICACIONES DE PRÉSTAMOS
# ══════════════════════════════════════════════════════════════════════════════

def _enviar_correo_async(app, mail_instance, msg):
    """Ejecuta el envío de correo de forma asíncrona dentro del contexto de la app."""
    with app.app_context():
        try:
            mail_instance.send(msg)
            logger.info('Correo asincrono enviado exitosamente a: %s', msg.recipients)
        except Exception as e:
            logger.error('Error asincrono enviando correo a %s: %s', msg.recipients, str(e), exc_info=True)

def enviar_notificacion_prestamo(prestamo, tipo_notificacion, mail_instance, es_libro=False):
    """
    Envía una notificación de correo asíncrona sobre el estado de un préstamo.
    
    Args:
        prestamo: Instancia de Prestamo o PrestamoLibro.
        tipo_notificacion: str ('pendiente', 'aprobado', 'rechazado', 'devuelto', 'proximo_vencer', 'vencido')
        mail_instance: Instancia de Flask-Mail.
        es_libro: bool, indica si es un préstamo de libro (True) o de equipo (False).
    """
    try:
        usuario = prestamo.usuario
        if not usuario or not usuario.correo:
            logger.warning("No se puede enviar notificacion: usuario no tiene correo.")
            return False
            
        asunto, html_body = _generar_html_notificacion(prestamo, tipo_notificacion, es_libro)
        if not html_body:
            return False
            
        msg = Message(
            subject=asunto,
            recipients=[usuario.correo],
            html=html_body
        )
        
        # Obtener la app real para pasarla al hilo
        app = current_app._get_current_object()
        thread = threading.Thread(target=_enviar_correo_async, args=(app, mail_instance, msg))
        thread.start()
        
        logger.info('Hilo iniciado para notificacion %s a %s', tipo_notificacion, usuario.correo)
        return True
    except Exception as e:
        logger.error('Error preparando notificacion de prestamo: %s', str(e), exc_info=True)
        return False

def _generar_html_notificacion(prestamo, tipo_notificacion, es_libro):
    """Genera el HTML y el asunto para notificaciones de préstamos."""
    recurso_nombre = prestamo.libro.titulo if es_libro else prestamo.equipo.nombre
    tipo_recurso = 'Libro' if es_libro else 'Equipo'
    prestamo_id = prestamo.id_prestamo_libro if es_libro else prestamo.id_prestamo
    
    año_actual = datetime.now(timezone.utc).year
    
    # Textos por tipo de notificación
    if tipo_notificacion == 'pendiente':
        asunto = f'📚 Solicitud de Préstamo Recibida - {recurso_nombre}'
        titulo = 'Solicitud Recibida'
        color_header = 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)' # Azul
        color_sombra = 'rgba(59, 130, 246, 0.35)'
        mensaje_principal = 'Tu solicitud fue recibida correctamente y está pendiente de aprobación.'
        detalles_extra = ''
        
    elif tipo_notificacion == 'aprobado':
        asunto = f'✅ Préstamo Aprobado - {recurso_nombre}'
        titulo = 'Préstamo Aprobado'
        color_header = 'linear-gradient(135deg, #22C55E 0%, #16A34A 100%)' # Verde
        color_sombra = 'rgba(34, 197, 94, 0.35)'
        mensaje_principal = '¡Buenas noticias! Tu solicitud de préstamo ha sido aprobada.'
        
        fecha_dev = prestamo.fecha_devolucion_esperada.strftime('%d/%m/%Y') if prestamo.fecha_devolucion_esperada else 'N/A'
        admin_nom = prestamo.administrador.nombre_completo() if prestamo.administrador else 'Administrador'
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Fecha de devolución:</strong> {fecha_dev}</p>
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Aprobado por:</strong> {admin_nom}</p>
        '''
        
    elif tipo_notificacion == 'rechazado':
        asunto = f'❌ Solicitud Rechazada - {recurso_nombre}'
        titulo = 'Solicitud Rechazada'
        color_header = 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)' # Rojo
        color_sombra = 'rgba(239, 68, 68, 0.35)'
        mensaje_principal = 'Lo sentimos, tu solicitud de préstamo no pudo ser aprobada en esta ocasión.'
        motivo = prestamo.razon_rechazo or 'No especificado.'
        detalles_extra = f'''
        <div style="background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 12px; margin-top: 16px;">
            <p style="color: #991B1B; font-size: 13px; margin: 0;"><strong>Motivo:</strong> {motivo}</p>
        </div>
        '''
        
    elif tipo_notificacion == 'devuelto':
        asunto = f'🔄 Devolución Registrada - {recurso_nombre}'
        titulo = 'Devolución Registrada'
        color_header = 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)' # Morado
        color_sombra = 'rgba(139, 92, 246, 0.35)'
        mensaje_principal = 'Hemos registrado exitosamente la devolución de tu préstamo. ¡Gracias por usar nuestros servicios!'
        fecha_real = prestamo.fecha_devolucion_real.strftime('%d/%m/%Y') if prestamo.fecha_devolucion_real else 'N/A'
        obs = prestamo.observaciones or 'Ninguna'
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Fecha de devolución:</strong> {fecha_real}</p>
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Observaciones:</strong> {obs}</p>
        '''
        
    elif tipo_notificacion == 'proximo_vencer':
        asunto = f'⚠️ Préstamo Próximo a Vencer - {recurso_nombre}'
        titulo = 'Préstamo Próximo a Vencer'
        color_header = 'linear-gradient(135deg, #F59E0B 0%, #B45309 100%)' # Naranja
        color_sombra = 'rgba(245, 158, 11, 0.35)'
        mensaje_principal = 'Te recordamos que tu préstamo está próximo a vencer. Por favor, asegúrate de realizar la devolución a tiempo.'
        fecha_dev = prestamo.fecha_devolucion_esperada.strftime('%d/%m/%Y') if prestamo.fecha_devolucion_esperada else 'N/A'
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Vence el:</strong> {fecha_dev}</p>
        '''
        
    elif tipo_notificacion == 'vencido':
        asunto = f'🚨 Préstamo Vencido - {recurso_nombre}'
        titulo = 'Préstamo Vencido'
        color_header = 'linear-gradient(135deg, #DC2626 0%, #991B1B 100%)' # Rojo oscuro
        color_sombra = 'rgba(220, 38, 38, 0.35)'
        mensaje_principal = 'Tu préstamo se encuentra actualmente vencido. Por favor, devuelve el recurso lo antes posible para evitar sanciones.'
        fecha_dev = prestamo.fecha_devolucion_esperada.strftime('%d/%m/%Y') if prestamo.fecha_devolucion_esperada else 'N/A'
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Debió devolverse el:</strong> {fecha_dev}</p>
        '''
        
    elif tipo_notificacion == 'renovacion_solicitada':
        asunto = f'🔄 Solicitud de Renovación Recibida - {recurso_nombre}'
        titulo = 'Renovación Solicitada'
        color_header = 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)' # Azul
        color_sombra = 'rgba(59, 130, 246, 0.35)'
        mensaje_principal = 'Tu solicitud de renovación de préstamo ha sido recibida correctamente y está en espera de aprobación.'
        
        renovacion = prestamo.historial_renovaciones[0] if getattr(prestamo, 'historial_renovaciones', None) else None
        fecha_prop = renovacion.fecha_esperada_nueva.strftime('%d/%m/%Y') if renovacion and renovacion.fecha_esperada_nueva else 'N/A'
        motivo = renovacion.motivo_solicitud if renovacion else 'No especificado.'
        
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Fecha de devolución propuesta:</strong> {fecha_prop}</p>
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Motivo de solicitud:</strong> {motivo}</p>
        '''
        
    elif tipo_notificacion == 'renovado':
        asunto = f'🔄 Préstamo Renovado Exitosamente - {recurso_nombre}'
        titulo = 'Préstamo Renovado'
        color_header = 'linear-gradient(135deg, #10B981 0%, #059669 100%)' # Verde esmeralda
        color_sombra = 'rgba(16, 185, 129, 0.35)'
        mensaje_principal = '¡Buenas noticias! Tu solicitud de renovación ha sido aprobada. Tu nueva fecha de vencimiento ha sido actualizada.'
        
        fecha_dev = prestamo.fecha_devolucion_esperada.strftime('%d/%m/%Y') if prestamo.fecha_devolucion_esperada else 'N/A'
        veces = prestamo.renovaciones_aplicadas
        
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Nueva fecha de vencimiento:</strong> {fecha_dev}</p>
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Renovaciones aplicadas:</strong> {veces}</p>
        '''
        
    elif tipo_notificacion == 'renovacion_rechazada':
        asunto = f'❌ Solicitud de Renovación Rechazada - {recurso_nombre}'
        titulo = 'Renovación Rechazada'
        color_header = 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)' # Rojo
        color_sombra = 'rgba(239, 68, 68, 0.35)'
        mensaje_principal = 'Lo sentimos, tu solicitud de renovación de préstamo no pudo ser aprobada en esta ocasión. Por favor, realiza la entrega del recurso en la fecha programada.'
        
        renovacion = prestamo.historial_renovaciones[0] if getattr(prestamo, 'historial_renovaciones', None) else None
        motivo = renovacion.motivo_rechazo if renovacion and renovacion.motivo_rechazo else 'No especificado.'
        fecha_dev = prestamo.fecha_devolucion_esperada.strftime('%d/%m/%Y') if prestamo.fecha_devolucion_esperada else 'N/A'
        
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Fecha de vencimiento original:</strong> {fecha_dev}</p>
        <div style="background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 12px; margin-top: 16px;">
            <p style="color: #991B1B; font-size: 13px; margin: 0;"><strong>Motivo del rechazo:</strong> {motivo}</p>
        </div>
        '''
    else:
        return None, None

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: 'Segoe UI', Arial, sans-serif;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f6f9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background: {color_header}; padding: 36px 32px; text-align: center;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Sena_Colombia_logo.svg" alt="SENA" width="56" style="display: inline-block; margin-bottom: 16px; filter: brightness(10);">
                            <h1 style="color: #ffffff; font-size: 22px; font-weight: 700; margin: 0;">{titulo}</h1>
                            <p style="color: rgba(255,255,255,0.85); font-size: 14px; margin: 8px 0 0;">Sistema de Biblioteca y Almacén SENA</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 36px 32px 24px;">
                            <p style="color: #374151; font-size: 16px; margin: 0 0 8px; font-weight: 600;">¡Hola, {prestamo.usuario.nombres}!</p>
                            <p style="color: #6B7280; font-size: 14px; line-height: 1.6; margin: 0 0 20px;">{mensaje_principal}</p>
                            
                            <div style="background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px; padding: 16px; margin-bottom: 24px;">
                                <h3 style="color: #111827; font-size: 15px; margin: 0 0 12px; border-bottom: 1px solid #E5E7EB; padding-bottom: 8px;">Detalles del Préstamo</h3>
                                <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>{tipo_recurso}:</strong> {recurso_nombre}</p>
                                <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>ID Préstamo:</strong> #{prestamo_id}</p>
                                {detalles_extra}
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #F9FAFB; padding: 20px 32px; text-align: center; border-top: 1px solid #E5E7EB;">
                            <p style="color: #9CA3AF; font-size: 11px; margin: 0; line-height: 1.6;">
                                &copy; {año_actual} Sistema SENA - Biblioteca y Almacén<br>
                                Este es un correo automático, por favor no respondas.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    return asunto, html


# ══════════════════════════════════════════════════════════════════════════════
#  NOTIFICACIONES DE MULTAS / SUSPENSIONES
# ══════════════════════════════════════════════════════════════════════════════

def enviar_notificacion_multa(multa, tipo_notificacion, mail_instance):
    """
    Envía una notificación asíncrona sobre una sanción/suspensión.
    
    Args:
        multa: Instancia de Multa.
        tipo_notificacion: str ('acumulando', 'activa', 'condonada')
        mail_instance: Instancia de Flask-Mail.
    """
    try:
        usuario = multa.usuario
        if not usuario or not usuario.correo:
            logger.warning("No se puede enviar notificacion de multa: usuario sin correo.")
            return False
            
        asunto, html_body = _generar_html_multa(multa, tipo_notificacion)
        if not html_body:
            return False
            
        msg = Message(
            subject=asunto,
            recipients=[usuario.correo],
            html=html_body
        )
        
        app = current_app._get_current_object()
        thread = threading.Thread(target=_enviar_correo_async, args=(app, mail_instance, msg))
        thread.start()
        
        logger.info('Notificacion de multa %s enviada asincronamente a %s', tipo_notificacion, usuario.correo)
        return True
    except Exception as e:
        logger.error('Error enviando notificacion de multa: %s', str(e), exc_info=True)
        return False

def _generar_html_multa(multa, tipo_notificacion):
    año_actual = datetime.now(timezone.utc).year
    recurso_nombre = "Desconocido"
    if multa.tipo_recurso == 'libro' and multa.prestamo_libro:
        recurso_nombre = multa.prestamo_libro.libro.titulo
    elif multa.tipo_recurso == 'equipo' and multa.prestamo_equipo:
        recurso_nombre = multa.prestamo_equipo.equipo.nombre
        
    if tipo_notificacion == 'acumulando':
        asunto = f'⚠️ Alerta: Préstamo Vencido y Suspensión en curso - {recurso_nombre}'
        titulo = 'Préstamo Vencido'
        color_header = 'linear-gradient(135deg, #F59E0B 0%, #B45309 100%)' # Naranja
        mensaje_principal = 'Tu préstamo está vencido. Actualmente tienes una suspensión temporal calculándose. Debes devolver el recurso de inmediato.'
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Días de retraso acumulados:</strong> {multa.dias_retraso}</p>
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Suspensión proyectada:</strong> {multa.dias_suspension} días</p>
        '''
    elif tipo_notificacion == 'activa':
        asunto = f'🚨 Suspensión Activa - {recurso_nombre}'
        titulo = 'Suspensión Activa'
        color_header = 'linear-gradient(135deg, #DC2626 0%, #991B1B 100%)' # Rojo
        mensaje_principal = 'Hemos recibido la devolución del recurso fuera de la fecha límite. Tu cuenta estará suspendida para realizar nuevos préstamos durante este tiempo.'
        fecha_fin = multa.fecha_fin_suspension.strftime('%d/%m/%Y') if multa.fecha_fin_suspension else 'N/A'
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Días de suspensión aplicados:</strong> {multa.dias_suspension}</p>
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Suspendido hasta:</strong> {fecha_fin}</p>
        '''
    elif tipo_notificacion == 'condonada':
        asunto = f'✅ Suspensión Condonada - {recurso_nombre}'
        titulo = 'Suspensión Levantada'
        color_header = 'linear-gradient(135deg, #10B981 0%, #059669 100%)' # Verde
        mensaje_principal = 'Un administrador ha revisado tu caso y ha condonado tu suspensión. Ya puedes volver a solicitar préstamos.'
        obs = multa.observacion or 'Ninguna'
        detalles_extra = f'''
        <p style="color: #4B5563; font-size: 14px; margin: 4px 0;"><strong>Observación:</strong> {obs}</p>
        '''
    else:
        return None, None

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: 'Segoe UI', Arial, sans-serif;">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f6f9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background: {color_header}; padding: 36px 32px; text-align: center;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Sena_Colombia_logo.svg" alt="SENA" width="56" style="display: inline-block; margin-bottom: 16px; filter: brightness(10);">
                            <h1 style="color: #ffffff; font-size: 22px; font-weight: 700; margin: 0;">{titulo}</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 36px 32px 24px;">
                            <p style="color: #374151; font-size: 16px; margin: 0 0 8px; font-weight: 600;">¡Hola, {multa.usuario.nombres}!</p>
                            <p style="color: #6B7280; font-size: 14px; line-height: 1.6; margin: 0 0 20px;">{mensaje_principal}</p>
                            <div style="background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px; padding: 16px;">
                                {detalles_extra}
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #F9FAFB; padding: 20px 32px; text-align: center; border-top: 1px solid #E5E7EB;">
                            <p style="color: #9CA3AF; font-size: 11px; margin: 0;">&copy; {año_actual} Sistema SENA - Biblioteca y Almacén</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    return asunto, html
