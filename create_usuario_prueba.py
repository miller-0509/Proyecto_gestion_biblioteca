"""
Script para crear usuarios de prueba (aprendiz e instructor)
"""
from app import create_app, db
from app.models.usuarios import Usuario

app = create_app()

with app.app_context():
    usuarios_prueba = [
        {
            'correo': 'aprendiz@biblioteca.com',
            'nombres': 'Juan',
            'apellidos': 'Aprendiz',
            'rol': 'aprendiz',
            'password': 'aprendiz123'
        },
        {
            'correo': 'instructor@biblioteca.com',
            'nombres': 'María',
            'apellidos': 'Instructor',
            'rol': 'instructor',
            'password': 'instructor123'
        }
    ]
    
    for datos_usuario in usuarios_prueba:
        usuario_existente = Usuario.query.filter_by(correo=datos_usuario['correo']).first()
        
        if usuario_existente:
            print(f"⚠ El usuario {datos_usuario['correo']} ya existe.")
        else:
            usuario = Usuario(
                nombres=datos_usuario['nombres'],
                apellidos=datos_usuario['apellidos'],
                correo=datos_usuario['correo'],
                rol=datos_usuario['rol'],
                estado='activo'
            )
            usuario.set_password(datos_usuario['password'])
            usuario.save()
            
            print(f"✓ Usuario {datos_usuario['rol']} creado exitosamente")
            print(f"  Correo: {datos_usuario['correo']}")
            print(f"  Contraseña: {datos_usuario['password']}")
            print()
