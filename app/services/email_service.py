"""
Servicio de correo electrónico profesional para verificación y notificaciones.

Arquitectura modular: este servicio centraliza la generación de tokens,
el envío de correos y las plantillas HTML, reutilizable para futuras
funcionalidades como recuperación de contraseña y notificaciones.
"""
import logging
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
