import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run import app
from app import db
from app.models.usuarios import Usuario

print("Starting Flask Auth Context Test...")

with app.app_context():
    # 1. Clean previous test user if exists
    test_email = "flask_test_user@example.com"
    existing = Usuario.query.filter_by(correo=test_email).first()
    if existing:
        print(f"Removing existing test user: {test_email}")
        db.session.delete(existing)
        db.session.commit()

    # 2. Create new user
    print("Creating new test user...")
    test_password = "Password123*"
    new_user = Usuario(
        nombres="Flask",
        apellidos="Tester",
        correo=test_email,
        rol="aprendiz",
        estado="activo"
    )
    new_user.set_password(test_password)
    db.session.add(new_user)
    db.session.commit()
    print("Test user saved to DB.")

    # 3. Retrieve user from DB (fresh query)
    db.session.expire_all() # Expire to force reload from DB
    retrieved = Usuario.query.filter_by(correo=test_email).first()
    
    if not retrieved:
        print("ERROR: Failed to retrieve user from DB!")
        sys.exit(1)

    print("\n--- Retrieved User Details ---")
    print(f"ID: {retrieved.id_usuario}")
    print(f"Email: '{retrieved.correo}'")
    print(f"Role: '{retrieved.rol}' (type: {type(retrieved.rol)})")
    print(f"Status (estado): '{retrieved.estado}' (type: {type(retrieved.estado)})")
    print(f"Password Hash in DB: '{retrieved.password}' (length: {len(retrieved.password) if retrieved.password else 0})")
    
    # 4. Run authentication checks
    is_active_val = retrieved.is_active
    print(f"Property is_active: {is_active_val}")
    
    pw_check_correct = retrieved.check_password(test_password)
    print(f"Password check with CORRECT password ('{test_password}'): {pw_check_correct}")
    
    pw_check_wrong = retrieved.check_password("WrongPassword")
    print(f"Password check with WRONG password: {pw_check_wrong}")

    # 5. Let's inspect the older truncated passwords
    print("\n--- Checking why older hashes are 'pbkdf2:sha256:1000000' ---")
    res = db.session.execute(db.text("SELECT id_usuario, correo, password FROM usuarios WHERE LENGTH(password) <= 30 LIMIT 3;"))
    for row in res:
        print(f"User ID: {row[0]} | Email: {row[1]} | Password Hash: '{row[2]}'")
