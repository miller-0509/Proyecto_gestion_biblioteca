
from app import create_app, db
from app.models.usuarios import Usuario
from sqlalchemy import func

app = create_app()
with app.app_context():
    dupes = db.session.query(Usuario.correo, func.count(Usuario.id_usuario)).group_by(Usuario.correo).having(func.count(Usuario.id_usuario) > 1).all()
    print(f"Duplicates: {dupes}")
    
    # Check for any user with empty password
    empty_pass = Usuario.query.filter((Usuario.password == None) | (Usuario.password == '')).all()
    print(f"Empty passwords: {[u.correo for u in empty_pass]}")
