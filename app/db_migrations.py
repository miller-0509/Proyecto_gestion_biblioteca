"""
Migraciones ligeras e idempotentes para bases PostgreSQL con tipos ENUM.
Se ejecutan de forma segura al arrancar la app (ver run.py) y no requieren
Flask-Migrate ni afectan a bases nuevas (no existe el tipo -> no-op).
"""
from flask import current_app
from sqlalchemy import text

from app import db

# Valores adicionales que los enums de la BD deben soportar para que
# coincidan con los estados que la aplicación utiliza.
ENUMS_ESTADOS = {
    'estado_equipo': ['no_disponible'],
    'estado_libro': ['no_disponible'],
}


def migrar_enums_estado(app):
    """Agrega de forma idempotente los valores faltantes a los enums."""
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '') or ''
    if not uri.startswith('postgres'):
        return

    with app.app_context():
        try:
            with db.engine.begin() as conn:
                for tipo, valores in ENUMS_ESTADOS.items():
                    existe = conn.execute(
                        text("SELECT 1 FROM pg_type WHERE typname = :t"),
                        {'t': tipo}
                    ).scalar()
                    if not existe:
                        continue
                    for valor in valores:
                        conn.execute(
                            text(f"ALTER TYPE {tipo} ADD VALUE IF NOT EXISTS '{valor}'")
                        )
            current_app.logger.info('Migración de enums de estado aplicada correctamente.')
        except Exception as e:
            current_app.logger.warning(
                'No se pudo migrar los enums de estado (probablemente ya existen): %s', str(e)
            )