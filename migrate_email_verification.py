"""
Script de migracion para agregar columnas de verificacion de email.

Agrega las columnas 'email_verificado' y 'fecha_verificacion' a la tabla
'usuarios' en PostgreSQL. Los administradores existentes se marcan como
verificados automaticamente.

Uso:
    python migrate_email_verification.py
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from run import app
from app import db
from app.models.usuarios import Usuario
from datetime import datetime, timezone


def migrar():
    """Agrega las columnas de verificacion de email y marca admins como verificados."""
    print("=" * 60)
    print("  MIGRACION: Verificacion de Email")
    print("=" * 60)

    try:
        # 1. Verificar si las columnas ya existen
        result = db.session.execute(db.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'usuarios' AND column_name = 'email_verificado'"
        ))
        columna_existe = result.fetchone() is not None

        if columna_existe:
            print("[INFO] La columna 'email_verificado' ya existe. Verificando datos...")
        else:
            # 2. Agregar columna email_verificado
            print("[1/3] Agregando columna 'email_verificado'...")
            db.session.execute(db.text(
                "ALTER TABLE usuarios ADD COLUMN email_verificado BOOLEAN NOT NULL DEFAULT false"
            ))
            print("  [OK] Columna 'email_verificado' creada correctamente.")

            # 3. Agregar columna fecha_verificacion
            print("[2/3] Agregando columna 'fecha_verificacion'...")
            db.session.execute(db.text(
                "ALTER TABLE usuarios ADD COLUMN fecha_verificacion TIMESTAMP"
            ))
            print("  [OK] Columna 'fecha_verificacion' creada correctamente.")

        # 4. Marcar administradores existentes como verificados automaticamente
        print("[3/3] Verificando administradores existentes automaticamente...")
        ahora = datetime.now(timezone.utc)
        admins = Usuario.query.filter_by(rol='administrador').all()
        for admin in admins:
            if not admin.email_verificado:
                admin.email_verificado = True
                admin.fecha_verificacion = ahora
                print(f"  [OK] Admin verificado: {admin.correo}")

        db.session.commit()
        print("")
        print("[EXITO] Migracion completada exitosamente.")
        
        # 5. Resumen
        total = Usuario.query.count()
        verificados = Usuario.query.filter_by(email_verificado=True).count()
        sin_verificar = total - verificados
        print(f"")
        print(f"Resumen:")
        print(f"  - Total de usuarios: {total}")
        print(f"  - Verificados: {verificados}")
        print(f"  - Pendientes de verificacion: {sin_verificar}")

    except Exception as e:
        db.session.rollback()
        print(f"")
        print(f"[ERROR] La migracion fallo: {e}")
        raise

    print("=" * 60)


if __name__ == "__main__":
    with app.app_context():
        migrar()
