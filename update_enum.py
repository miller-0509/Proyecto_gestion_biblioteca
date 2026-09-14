from app import create_app, db

app = create_app()
app.app_context().push()

try:
    # "rol_usuario" es el ENUM
    db.session.execute(db.text("ALTER TYPE rol_usuario ADD VALUE IF NOT EXISTS 'bibliotecario';"))
    db.session.execute(db.text("ALTER TYPE rol_usuario ADD VALUE IF NOT EXISTS 'almacenista';"))

    # Estados adicionales usados por el flujo de devoluciones
    db.session.execute(db.text("ALTER TYPE estado_equipo ADD VALUE IF NOT EXISTS 'no_disponible';"))
    db.session.execute(db.text("ALTER TYPE estado_libro ADD VALUE IF NOT EXISTS 'no_disponible';"))

    db.session.commit()
    print("Enum actualizado exitosamente.")
except Exception as e:
    print("Error:", str(e))
    db.session.rollback()
