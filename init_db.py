"""
Script para inicializar la base de datos
"""
from app import create_app, db
from app.models.usuarios import Usuario
from app.models.equipos import Equipo
from app.models.prestamos import Prestamo
from app.models.libros import Libro
from app.models.prestamos_libros import PrestamoLibro
import os

app = create_app()

def init_database():
    """Inicializa la base de datos y crea todas las tablas"""
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            
            # Verificar si las tablas se crearon
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("✓ Base de datos inicializada correctamente")
            print(f"✓ Tablas creadas: {', '.join(tables)}")
            print("\n📍 Ruta de base de datos: ", end="")
            
            # Mostrar ruta de la BD
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                from flask import current_app
                db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
                if db_path:
                    print(db_path)
                else:
                    print("instance/almacendb.sqlite")
            
            print("\n✅ La base de datos está lista para usar.")
            print("   Ejecuta 'python run.py' para iniciar la aplicación\n")
            
        except Exception as e:
            print(f"❌ Error al inicializar la base de datos: {e}")
            print("   Asegúrate de que todas las dependencias estén instaladas.")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_database()
