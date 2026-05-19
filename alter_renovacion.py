import psycopg2
from config import get_config

config = get_config()
conn = psycopg2.connect(config.SQLALCHEMY_DATABASE_URI)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE prestamos ADD COLUMN renovaciones_aplicadas INTEGER DEFAULT 0;")
    cur.execute("ALTER TABLE prestamos ADD COLUMN estado_renovacion VARCHAR(20);")
    cur.execute("ALTER TABLE prestamos_libros ADD COLUMN renovaciones_aplicadas INTEGER DEFAULT 0;")
    cur.execute("ALTER TABLE prestamos_libros ADD COLUMN estado_renovacion VARCHAR(20);")
    conn.commit()
    print("Columnas agregadas con éxito.")
except Exception as e:
    conn.rollback()
    print("Error:", e)
finally:
    cur.close()
    conn.close()
