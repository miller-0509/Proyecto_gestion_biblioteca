import os
from flask import current_app
from run import app
from app.services.multas_service import actualizar_multas_diarias
import logging

# Configurar logging específico para el cron
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cron_multas')

def main():
    logger.info("Iniciando cron job de multas...")
    try:
        # Importante: usar app para tener el contexto de aplicación y BD
        actualizar_multas_diarias(app)
        logger.info("Cron job finalizado con éxito.")
    except Exception as e:
        logger.error(f"Fallo en cron job de multas: {e}")

if __name__ == "__main__":
    main()
