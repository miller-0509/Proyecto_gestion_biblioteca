"""
Script para crear un usuario administrador
"""
from app import create_app, db
from app.models.usuarios import Usuario

app = create_app()

with app.app_context():
    # Verificar si el admin ya existe
    admin_existente = Usuario.query.filter_by(correo='admin@biblioteca.com').first()
    
    if admin_existente:
        print("⚠ El usuario administrador ya existe.")
        print(f"Correo: {admin_existente.correo}")
        print(f"Rol: {admin_existente.rol}")
    else:
        # Crear un nuevo usuario admin
        admin = Usuario(
            nombres='Administrador',
            apellidos='Sistema',
            correo='admin@biblioteca.com',
            rol='administrador',
            estado='activo'
        )
        admin.set_password('admin123')
        admin.save()
        
        print("✓ Usuario administrador creado exitosamente")
        print(f"Correo: admin@biblioteca.com")
        print(f"Contraseña: admin123")
        print(f"Rol: administrador")
        print("⚠ Por favor cambiar la contraseña después del primer login")
