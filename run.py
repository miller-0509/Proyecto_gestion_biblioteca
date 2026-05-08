from app import create_app, db

app = create_app()

with app.app_context():
    try:
        db.create_all()
        print("[OK] Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"[WARN] db.create_all() omitido (probablemente ya existe): {e}")

if __name__ == '__main__':
    import os
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    print(f"[START] Iniciando servidor en http://0.0.0.0:81 ({'produccion' if is_prod else 'desarrollo'})")
    app.run(debug=not is_prod, host='0.0.0.0', port=81)