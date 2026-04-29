from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    print("✓ Base de datos inicializada correctamente.")



if __name__ == '__main__':
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"🚀 Iniciando servidor en http://0.0.0.0:81 (debug={'ON' if debug_mode else 'OFF'})")
    app.run(debug=debug_mode, host='0.0.0.0', port=81)



