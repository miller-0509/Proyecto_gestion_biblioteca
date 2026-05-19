import logging
from app import create_app, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def update_schema():
    with app.app_context():
        with db.engine.connect() as conn:
            # Update prestamos
            try:
                conn.execute(db.text("ALTER TABLE prestamos ADD COLUMN notificacion_vencimiento_enviada BOOLEAN DEFAULT FALSE"))
                logger.info("Added notificacion_vencimiento_enviada to prestamos")
            except Exception as e:
                logger.warning(f"Error adding notificacion_vencimiento_enviada: {e}")
                
            try:
                conn.execute(db.text("ALTER TABLE prestamos ADD COLUMN notificacion_vencido_enviada BOOLEAN DEFAULT FALSE"))
                logger.info("Added notificacion_vencido_enviada to prestamos")
            except Exception as e:
                logger.warning(f"Error adding notificacion_vencido_enviada: {e}")

            # Update prestamos_libros
            try:
                conn.execute(db.text("ALTER TABLE prestamos_libros ADD COLUMN notificacion_vencimiento_enviada BOOLEAN DEFAULT FALSE"))
                logger.info("Added notificacion_vencimiento_enviada to prestamos_libros")
            except Exception as e:
                logger.warning(f"Error adding notificacion_vencimiento_enviada: {e}")
                
            try:
                conn.execute(db.text("ALTER TABLE prestamos_libros ADD COLUMN notificacion_vencido_enviada BOOLEAN DEFAULT FALSE"))
                logger.info("Added notificacion_vencido_enviada to prestamos_libros")
            except Exception as e:
                logger.warning(f"Error adding notificacion_vencido_enviada: {e}")
                
            conn.commit()
            logger.info("Database schema update completed.")

if __name__ == '__main__':
    update_schema()
