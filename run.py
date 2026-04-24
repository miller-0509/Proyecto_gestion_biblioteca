from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    print("✓ Base de datos inicializada correctamente.")

@app.teardown_appcontext
def shutdown_session(exception=None):

    if exception is None:
        db.session.commit()
    db.session.remove()

if __name__ == '__main__':
    print("🚀 Iniciando servidor en http://0.0.0.0:81")
    app.run(debug=True, host='0.0.0.0', port=81)
