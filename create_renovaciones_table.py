from app import create_app, db
from app.models.renovaciones import RenovacionEquipo, RenovacionLibro

app = create_app()

with app.app_context():
    db.create_all()
    print("Tablas de renovaciones creadas correctamente.")
