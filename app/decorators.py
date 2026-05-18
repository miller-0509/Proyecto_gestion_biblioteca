from functools import wraps
from datetime import datetime, timezone
from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Decorador reutilizable para restringir acceso por rol(es).
    
    Uso:
        @role_required('administrador')
        @role_required('administrador', 'instructor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.rol not in roles:
                flash('Acceso denegado. No tienes los permisos necesarios.', 'danger')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Atajo para role_required('administrador')."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'administrador':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def bibliotecario_required(f):
    """Permite acceso a bibliotecarios y administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol not in ['administrador', 'bibliotecario']:
            flash('Acceso denegado. Se requieren permisos de bibliotecario o administrador.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def almacenista_required(f):
    """Permite acceso a almacenistas y administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol not in ['administrador', 'almacenista']:
            flash('Acceso denegado. Se requieren permisos de almacenista o administrador.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def gestion_libros_required(f):
    """Protege rutas exclusivas de gestión de biblioteca."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol not in ['administrador', 'bibliotecario']:
            flash('Acceso denegado. Módulo de biblioteca restringido.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def gestion_equipos_required(f):
    """Protege rutas exclusivas de gestión de almacén."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol not in ['administrador', 'almacenista']:
            flash('Acceso denegado. Módulo de almacén restringido.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def calcular_dias_restantes(prestamo):
    """Calcula los días restantes de un préstamo aceptado.

    Retorna un entero (días) o None si no aplica.
    Maneja de forma segura fechas naive y aware.
    """
    if prestamo.estado != 'aceptado' or not prestamo.fecha_devolucion_esperada:
        return None
    try:
        ahora = datetime.now(timezone.utc)
        fecha_dev = prestamo.fecha_devolucion_esperada
        if fecha_dev.tzinfo is None:
            fecha_dev = fecha_dev.replace(tzinfo=timezone.utc)
        return (fecha_dev - ahora).days
    except Exception:
        return None
