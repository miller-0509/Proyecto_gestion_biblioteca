import os
import sys
import getpass
from run import app
from app import db
from app.models.usuarios import Usuario

def main():
    print("=" * 60)
    print("  SENA - CREACIÓN DE USUARIO ADMINISTRADOR DE RESPALDO")
    print("=" * 60)

    # Asegurar que estamos cargando la configuración adecuada
    env = os.environ.get("FLASK_ENV", "development")
    print(f"Entorno detectado: {env}")
    
    # Solicitar datos del administrador
    nombres = input("Nombres del Administrador: ").strip()
    if not nombres:
        print("ERROR: El nombre es obligatorio.")
        return

    apellidos = input("Apellidos del Administrador: ").strip()
    if not apellidos:
        print("ERROR: Los apellidos son obligatorios.")
        return

    correo = input("Correo electrónico: ").strip().lower()
    if not correo or "@" not in correo:
        print("ERROR: Correo electrónico inválido.")
        return

    password = getpass.getpass("Contraseña (oculta en pantalla, mínimo 8 caracteres): ").strip()
    if len(password) < 8:
        print("ERROR: La contraseña debe tener al menos 8 caracteres.")
        return

    confirm_password = getpass.getpass("Confirmar Contraseña: ").strip()
    if password != confirm_password:
        print("ERROR: Las contraseñas no coinciden.")
        return

    # Ejecutar dentro del contexto de Flask
    with app.app_context():
        try:
            # Verificar si el usuario ya existe
            usuario = Usuario.query.filter_by(correo=correo).first()
            
            if usuario:
                print(f"\n[INFO] El usuario con correo '{correo}' ya existe en la base de datos.")
                confirmar = input("¿Deseas actualizarlo y asignarle el rol de ADMINISTRADOR? (s/n): ").strip().lower()
                if confirmar != 's':
                    print("Operación cancelada.")
                    return
                
                usuario.nombres = nombres
                usuario.apellidos = apellidos
                usuario.rol = "administrador"
                usuario.estado = "activo"
                usuario.set_password(password)
                print("[PROCESO] Actualizando datos del usuario y re-hasheando contraseña...")
            else:
                # Crear nuevo usuario administrador
                usuario = Usuario(
                    nombres=nombres,
                    apellidos=apellidos,
                    correo=correo,
                    rol="administrador",
                    estado="activo"
                )
                usuario.set_password(password)
                db.session.add(usuario)
                print("[PROCESO] Creando nueva cuenta de administrador...")

            # Guardar en base de datos
            db.session.commit()
            print("\n" + "=" * 60)
            print("  ¡ÉXITO! Usuario Administrador guardado correctamente en la DB.")
            print(f"  - Nombre: {usuario.nombre_completo()}")
            print(f"  - Correo: {usuario.correo}")
            print(f"  - Rol: {usuario.rol}")
            print(f"  - Estado: {usuario.estado}")
            print("=" * 60)

        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR CRÍTICO] No se pudo guardar el usuario en la base de datos: {e}")

if __name__ == "__main__":
    main()
