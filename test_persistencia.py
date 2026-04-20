#!/usr/bin/env python3
"""
Script de prueba para verificar que la base de datos guarda datos correctamente.
Esto te ayudará a diagnosticar si el problema está resuelto.
"""

from app import create_app, db
from app.models.usuarios import Usuario
from app.models.equipos import Equipo
from datetime import datetime
import os

app = create_app()

def test_persistencia():
    """Prueba si los datos se guardan correctamente en la BD"""
    
    with app.app_context():
        print("=" * 60)
        print("🧪 PRUEBA DE PERSISTENCIA DE BASE DE DATOS")
        print("=" * 60)
        
        # Verificar que la BD existe
        print("\n1️⃣  Verificando que las tablas existan...")
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            if tables:
                print(f"   ✓ Tablas encontradas: {', '.join(tables)}")
            else:
                print("   ❌ No hay tablas en la base de datos")
                print("   Ejecuta 'python init_db.py' primero")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        
        # Contar usuarios actuales
        print("\n2️⃣  Contando usuarios en la BD...")
        try:
            usuarios_antes = Usuario.query.count()
            print(f"   Usuarios existentes: {usuarios_antes}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        
        # Crear un usuario de prueba
        print("\n3️⃣  Creando usuario de prueba...")
        try:
            usuario_prueba = Usuario(
                nombres="Test",
                apellidos="Usuario",
                correo=f"test_{datetime.now().timestamp()}@prueba.com",
                rol="aprendiz"
            )
            usuario_prueba.set_password("testpass123")
            usuario_prueba.save()
            print(f"   ✓ Usuario creado con ID: {usuario_prueba.id_usuario}")
            user_id = usuario_prueba.id_usuario
        except Exception as e:
            print(f"   ❌ Error al crear usuario: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Crear un equipo de prueba
        print("\n4️⃣  Creando equipo de prueba...")
        try:
            equipo_prueba = Equipo(
                nombre="Laptop Prueba",
                tipo_equipo="Computadora",
                numero_serie=f"PRUEBA{datetime.now().timestamp()}",
                descripcion="Equipo de prueba"
            )
            equipo_prueba.save()
            print(f"   ✓ Equipo creado con ID: {equipo_prueba.id_equipo}")
            equipo_id = equipo_prueba.id_equipo
        except Exception as e:
            print(f"   ❌ Error al crear equipo: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Contar usuarios después
        print("\n5️⃣  Verificando que los datos se guardaron...")
        try:
            usuarios_despues = Usuario.query.count()
            equipos_totales = Equipo.query.count()
            print(f"   Usuarios: {usuarios_antes} → {usuarios_despues}")
            print(f"   Equipos totales: {equipos_totales}")
            
            if usuarios_despues > usuarios_antes:
                print("   ✓ Usuarios guardados correctamente")
            else:
                print("   ❌ Los usuarios NO se guardaron")
                return False
                
            if equipos_totales > 0:
                print("   ✓ Equipos guardados correctamente")
            else:
                print("   ❌ Los equipos NO se guardaron")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        
        # Recuperar el usuario de prueba
        print("\n6️⃣  Recuperando el usuario de prueba...")
        try:
            usuario_recuperado = Usuario.query.get(user_id)
            if usuario_recuperado:
                print(f"   ✓ Usuario recuperado: {usuario_recuperado.nombre_completo()}")
            else:
                print("   ❌ No se pudo recuperar el usuario")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        
        # Recuperar el equipo de prueba
        print("\n7️⃣  Recuperando el equipo de prueba...")
        try:
            equipo_recuperado = Equipo.query.get(equipo_id)
            if equipo_recuperado:
                print(f"   ✓ Equipo recuperado: {equipo_recuperado.nombre}")
            else:
                print("   ❌ No se pudo recuperar el equipo")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
        
        return True

if __name__ == '__main__':
    success = test_persistencia()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ¡PRUEBA EXITOSA! La base de datos está funcionando.")
        print("   Los datos se guardarán correctamente.")
    else:
        print("❌ PRUEBA FALLIDA - Hay un problema con la base de datos.")
        print("   Revisa los mensajes de error arriba.")
    print("=" * 60 + "\n")
