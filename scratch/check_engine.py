
from app import create_app, db

app = create_app()
with app.app_context():
    print(f"Engine: {db.engine.name}")
    print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
