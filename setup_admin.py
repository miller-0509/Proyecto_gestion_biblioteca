import sys
from app import create_app, db
from app.models.usuarios import Usuario

def create_admin(nombres, apellidos, correo, password):
    app = create_app()
    with app.app_context():
        # Verificar si el usuario ya existe
        existing_user = Usuario.query.filter_by(correo=correo).first()
        if existing_user:
            print(f"\n[!] Error: El correo '{correo}' ya está registrado.")
            print(f"    Usuario: {existing_user.nombres} {existing_user.apellidos} (Rol: {existing_user.rol})")
            return False

        try:
            # Crear el nuevo administrador
            nuevo_admin = Usuario(
                nombres=nombres,
                apellidos=apellidos,
                correo=correo,
                rol='administrador',
                estado='activo'
            )
            nuevo_admin.set_password(password)
            
            db.session.add(nuevo_admin)
            db.session.commit()
            
            print("\n" + "="*40)
            print("🚀 ADMINISTRADOR CREADO EXITOSAMENTE")
            print("="*40)
            print(f"👤 Nombre:     {nombres} {apellidos}")
            print(f"📧 Correo:     {correo}")
            print(f"🔑 Contraseña: {password}")
            print(f"🛡️ Rol:        Administrador")
            print("="*40)
            print("\nYa puedes iniciar sesión en la plataforma.")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[!] Error al crear el administrador: {str(e)}")
            return False

if __name__ == "__main__":
    # Datos por defecto o via argumentos si se desea extender
    DEFAULT_NOMBRES = "Admin"
    DEFAULT_APELLIDOS = "Biblioteca"
    DEFAULT_CORREO = "admin@biblioteca.com"
    DEFAULT_PASSWORD = "AdminPassword2024*"

    print("--- Creación de Usuario Administrador ---")
    
    # Podríamos usar input() pero para automatización es mejor tener valores fijos 
    # o permitir pasarlos por consola. Por simplicidad usamos los defaults.
    
    create_admin(
        nombres=DEFAULT_NOMBRES,
        apellidos=DEFAULT_APELLIDOS,
        correo=DEFAULT_CORREO,
        password=DEFAULT_PASSWORD
    )
