from app import create_app, db
from app.models.usuarios import Usuario

app = create_app()

with app.app_context():
    if Usuario.query.filter_by(correo='admin@biblioteca.com').first():
        print("[WARN] El usuario administrador ya existe.")
    else:
        admin = Usuario(
            nombres='Administrador',
            apellidos='Principal',
            correo='admin@biblioteca.com',
            rol='administrador',
            estado='activo'
        )
        admin.set_password('Admin2024*')
        admin.save()
        db.session.commit()
        print("[OK] Usuario administrador creado exitosamente.")
        print("     Correo:     admin@biblioteca.com")
        print("     Contraseña: Admin2024*")