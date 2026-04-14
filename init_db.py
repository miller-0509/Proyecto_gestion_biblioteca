"""
Script para inicializar la base de datos
"""
from app import create_app, db
from app.models.usuarios import Usuario
from app.models.equipos import Equipo
from app.models.prestamos import Prestamo

app = create_app()

with app.app_context():
    # Crear todas las tablas
    db.create_all()
    print("✓ Base de datos inicializada correctamente")
    print("✓ Tablas creadas: usuarios, equipos, prestamos")
