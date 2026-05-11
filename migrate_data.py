import os
from sqlalchemy import create_engine, MetaData, Table, select
from app import create_app, db
from app.models.usuarios import Usuario
from app.models.equipos import Equipo
from app.models.libros import Libro
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro

def migrate():
    # 1. Configuración de orígenes
    sqlite_uri = "sqlite:///instance/almacendb.sqlite"
    sqlite_engine = create_engine(sqlite_uri)
    
    # 2. Inicializar App Flask para el destino (Postgres)
    app = create_app()
    
    models = [
        (Usuario, 'usuarios'),
        (Equipo, 'equipos'),
        (Libro, 'libros'),
        (Prestamo, 'prestamos'),
        (PrestamoLibro, 'prestamos_libros')
    ]
    
    with app.app_context():
        print("--- Iniciando Migración de Datos ---")
        
        for model_class, table_name in models:
            print(f"Migrando tabla: {table_name}...")
            
            # Leer datos de SQLite
            with sqlite_engine.connect() as conn:
                metadata = MetaData()
                table = Table(table_name, metadata, autoload_with=sqlite_engine)
                results = conn.execute(select(table)).fetchall()
                
                count = 0
                for row in results:
                    # Convertir fila a diccionario
                    data = dict(row._mapping)
                    
                    # Verificar si ya existe en el destino para evitar duplicados si se corre dos veces
                    # Usamos la PK (asumimos que es el primer campo o lo buscamos)
                    pk_name = model_class.__table__.primary_key.columns.keys()[0]
                    pk_val = data[pk_name]
                    
                    if not model_class.query.get(pk_val):
                        # Crear instancia del modelo
                        instance = model_class(**data)
                        db.session.add(instance)
                        count += 1
            
            try:
                db.session.commit()
                print(f"  OK: {count} registros migrados.")
            except Exception as e:
                db.session.rollback()
                print(f"  ERROR en {table_name}: {str(e)}")

        # 3. Resetear secuencias en Postgres (Importante para evitar errores de ID duplicado luego)
        print("\nActualizando secuencias en Postgres...")
        try:
            # Usuarios
            db.session.execute(db.text("SELECT setval('usuarios_id_usuario_seq', (SELECT MAX(id_usuario) FROM usuarios))"))
            # Equipos
            db.session.execute(db.text("SELECT setval('equipos_id_equipo_seq', (SELECT MAX(id_equipo) FROM equipos))"))
            # Libros
            db.session.execute(db.text("SELECT setval('libros_id_libro_seq', (SELECT MAX(id_libro) FROM libros))"))
            # Prestamos
            db.session.execute(db.text("SELECT setval('prestamos_id_prestamo_seq', (SELECT MAX(id_prestamo) FROM prestamos))"))
            # Prestamos Libros
            db.session.execute(db.text("SELECT setval('prestamos_libros_id_prestamo_libro_seq', (SELECT MAX(id_prestamo_libro) FROM prestamos_libros))"))
            
            db.session.commit()
            print("  OK: Secuencias actualizadas.")
        except Exception as e:
            print(f"  Aviso: No se pudieron actualizar algunas secuencias (esto es normal si la tabla estaba vacía): {str(e)}")

        print("\n--- Migración Finalizada ---")

if __name__ == "__main__":
    migrate()
