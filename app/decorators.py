from functools import wraps
from datetime import datetime
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'administrador':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
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
        ahora = datetime.now()
        fecha_dev = prestamo.fecha_devolucion_esperada
        if fecha_dev.tzinfo is not None:
            fecha_dev = fecha_dev.replace(tzinfo=None)
        return (fecha_dev - ahora).days
    except Exception:
        return None
