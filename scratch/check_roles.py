
from app import create_app, db
from app.models.usuarios import Usuario

app = create_app()
with app.app_context():
    u = Usuario.query.filter_by(correo='admin@biblioteca.com').first()
    if u:
        print(f"User: {u.correo}")
        print(f"Rol Value: {u.rol}")
        print(f"Rol Type: {type(u.rol)}")
        print(f"Comparison (u.rol == 'administrador'): {u.rol == 'administrador'}")
        
    u2 = Usuario.query.filter_by(correo='instructor@gmail.com').first()
    if u2:
        print(f"User: {u2.correo}")
        print(f"Rol Value: {u2.rol}")
        print(f"Rol Type: {type(u2.rol)}")
        print(f"Comparison (u2.rol == 'administrador'): {u2.rol == 'administrador'}")
