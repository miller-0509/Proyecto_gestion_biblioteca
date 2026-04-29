"""
Configuración centralizada de logging para la aplicación.
Logs a consola y archivo rotativo.
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """Configura logging estructurado para la aplicación Flask."""
    log_level = logging.DEBUG if app.debug else logging.WARNING

    # Formato estructurado
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ── Log a archivo rotativo ──────────────────────────────────────
    log_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=1_048_576,  # 1 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # ── Log a consola ───────────────────────────────────────────────
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    # Aplicar al logger de la app
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(log_level)

    app.logger.info('Logging configurado correctamente (nivel: %s)', logging.getLevelName(log_level))
