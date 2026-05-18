import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load env
load_dotenv()

db_url = os.environ.get("DATABASE_URL")
print(f"Connecting to database: {db_url}")

from sqlalchemy import create_engine, text

engine = create_engine(db_url)

with engine.connect() as conn:
    # Get table info for usuarios
    print("\n--- Columns in 'usuarios' table ---")
    columns_query = text("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'usuarios';
    """)
    res = conn.execute(columns_query)
    for col in res:
        print(f"Column: {col[0]} | Type: {col[1]} | Max Length: {col[2]}")

    # Get recent users
    print("\n--- Recent Users in DB ---")
    users_query = text("SELECT id_usuario, nombres, correo, password, rol, estado FROM usuarios ORDER BY id_usuario DESC LIMIT 5;")
    res = conn.execute(users_query)
    for user in res:
        pw_hash = user[3]
        pw_len = len(pw_hash) if pw_hash else 0
        print(f"ID: {user[0]} | Name: {user[1]} | Email: {user[2]} | Role: {user[4]} | Status: {user[5]}")
        print(f"  Password Hash: {pw_hash} (Length: {pw_len})")
        
        # Test a couple of standard passwords against this hash
        test_passwords = ["12345678Ab", "12345678ab", "Password123", "password", "Admin123", "Admin123*"]
        matched = False
        for p in test_passwords:
            if pw_hash and check_password_hash(pw_hash, p):
                print(f"  --> MATCH FOUND! Password is: '{p}'")
                matched = True
                break
        if not matched:
            print("  --> No match found for standard test passwords.")

print("\n--- Direct hash check test ---")
test_plain = "12345678Ab"
hash_val = generate_password_hash(test_plain)
print(f"Plain: {test_plain}")
print(f"Generated Hash: {hash_val} (Length: {len(hash_val)})")
print(f"Check Hash: {check_password_hash(hash_val, test_plain)}")
