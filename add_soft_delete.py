import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def update_db():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL no encontrada en .env")
        return

    # Ajustar driver para psycopg2 si es necesario para el script
    if database_url.startswith("postgresql+psycopg://"):
        database_url = database_url.replace("postgresql+psycopg://", "postgresql://")

    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        print("Añadiendo columna 'eliminado' a la tabla 'equipos'...")
        try:
            conn.execute(text("ALTER TABLE equipos ADD COLUMN eliminado BOOLEAN DEFAULT FALSE;"))
            conn.commit()
            print("Columna añadida a 'equipos'.")
        except Exception as e:
            print(f"Nota: No se pudo añadir a 'equipos' (tal vez ya existe): {e}")
            conn.rollback()

        print("Añadiendo columna 'eliminado' a la tabla 'libros'...")
        try:
            conn.execute(text("ALTER TABLE libros ADD COLUMN eliminado BOOLEAN DEFAULT FALSE;"))
            conn.commit()
            print("Columna añadida a 'libros'.")
        except Exception as e:
            print(f"Nota: No se pudo añadir a 'libros' (tal vez ya existe): {e}")
            conn.rollback()

        print("Proceso finalizado.")

if __name__ == "__main__":
    update_db()
