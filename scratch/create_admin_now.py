import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app import db
from app.models.usuarios import Usuario

print("Starting Admin Programmatic Creation Script...")

with app.app_context():
    admin_email = "admin_sena@biblioteca.com"
    admin_password = "SenaAdmin2026*"
    
    # Check if exists
    existing = Usuario.query.filter_by(correo=admin_email).first()
    if existing:
        print(f"User {admin_email} already exists. Upgrading to admin and setting password...")
        existing.nombres = "Administrador"
        existing.apellidos = "SENA"
        existing.rol = "administrador"
        existing.estado = "activo"
        existing.set_password(admin_password)
        db.session.commit()
        print("Existing user updated successfully.")
    else:
        print(f"Creating new admin user {admin_email}...")
        new_admin = Usuario(
            nombres="Administrador",
            apellidos="SENA",
            correo=admin_email,
            rol="administrador",
            estado="activo"
        )
        new_admin.set_password(admin_password)
        db.session.add(new_admin)
        db.session.commit()
        print("New admin user created successfully.")

print("Process finished successfully!")
