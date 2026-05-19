import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add columns to prestamos
        db.session.execute(text("ALTER TABLE prestamos ADD COLUMN observacion_devolucion TEXT;"))
        db.session.execute(text("ALTER TABLE prestamos ADD COLUMN estado_fisico_devolucion VARCHAR(20);"))
        print("Columnas agregadas a prestamos.")
    except Exception as e:
        print(f"Error en prestamos (pueden ya existir): {e}")
        db.session.rollback()

    try:
        # Add columns to prestamos_libros
        db.session.execute(text("ALTER TABLE prestamos_libros ADD COLUMN observacion_devolucion TEXT;"))
        db.session.execute(text("ALTER TABLE prestamos_libros ADD COLUMN estado_fisico_devolucion VARCHAR(20);"))
        print("Columnas agregadas a prestamos_libros.")
    except Exception as e:
        print(f"Error en prestamos_libros (pueden ya existir): {e}")
        db.session.rollback()
        
    db.session.commit()
    print("Migracion completada.")
