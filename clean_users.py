import os
import sys
import argparse
from sqlalchemy.exc import IntegrityError

# Asegurar que la raíz del proyecto está en el PATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from run import app
from app import db
from app.models.usuarios import Usuario
from app.models.prestamos import Prestamo
from app.models.prestamos_libros import PrestamoLibro

def run_diagnostico():
    """Realiza un diagnóstico de seguridad antes de cualquier acción."""
    print("=" * 60)
    print("  DIAGNÓSTICO PREVIO DE SEGURIDAD - BASE DE DATOS")
    print("=" * 60)
    
    # 1. Conteo por roles
    total_usuarios = Usuario.query.count()
    admins = Usuario.query.filter_by(rol='administrador').all()
    aprendices = Usuario.query.filter_by(rol='aprendiz').all()
    instructores = Usuario.query.filter_by(rol='instructor').all()
    otros_roles = Usuario.query.filter(Usuario.rol.notin_(['administrador', 'aprendiz', 'instructor'])).all()
    
    print(f"Total de usuarios en la base de datos: {total_usuarios}")
    print(f"  - Administradores (NO SE TOCARÁN): {len(admins)}")
    print(f"  - Aprendices (Candidatos): {len(aprendices)}")
    print(f"  - Instructores (Candidatos): {len(instructores)}")
    if otros_roles:
        print(f"  - Otros roles (Candidatos): {len(otros_roles)}")
        
    print("\nLista de Administradores Protegidos:")
    for admin in admins:
        print(f"  * ID: {admin.id_usuario} | {admin.nombre_completo()} ({admin.correo}) | Estado: {admin.estado}")

    # 2. Análisis de Relaciones con Préstamos
    candidatos = Usuario.query.filter(Usuario.rol != 'administrador').all()
    con_prestamos_equipos = 0
    con_prestamos_libros = 0
    con_ambos = 0
    sin_historial = 0
    
    print("\nAnalizando relaciones y dependencias:")
    for u in candidatos:
        has_equipos = Prestamo.query.filter_by(id_usuario=u.id_usuario).count() > 0
        has_libros = PrestamoLibro.query.filter_by(id_usuario=u.id_usuario).count() > 0
        
        if has_equipos and has_libros:
            con_ambos += 1
        elif has_equipos:
            con_prestamos_equipos += 1
        elif has_libros:
            con_prestamos_libros += 1
        else:
            sin_historial += 1
            
    print(f"  - Usuarios con préstamos de EQUIPOS asociados: {con_prestamos_equipos + con_ambos}")
    print(f"  - Usuarios con préstamos de LIBROS asociados: {con_prestamos_libros + con_ambos}")
    print(f"  - Usuarios con AMBOS tipos de préstamos: {con_ambos}")
    print(f"  - Usuarios SIN NINGÚN historial (100% seguros para DELETE físico): {sin_historial}")
    
    # 3. Detección de Duplicados o Corruptos
    print("\nBuscando anomalías de datos:")
    duplicados = db.session.query(Usuario.correo).group_by(Usuario.correo).having(db.func.count(Usuario.correo) > 1).all()
    if duplicados:
        print(f"  [ALERTA] Se detectaron {len(duplicados)} correos duplicados:")
        for dup in duplicados:
            print(f"    * Correo duplicado: {dup[0]}")
    else:
        print("  - No se detectaron correos duplicados en la base de datos.")
        
    # Verificar usuarios sin contraseñas válidas o campos incompletos
    corruptos = Usuario.query.filter((Usuario.nombres == '') | (Usuario.apellidos == '') | (Usuario.password == None)).all()
    if corruptos:
        print(f"  [ALERTA] Se detectaron {len(corruptos)} usuarios con registros corruptos/incompletos:")
        for corr in corruptos:
            print(f"    * ID: {corr.id_usuario} | {corr.correo}")
    else:
        print("  - No se detectaron registros de usuarios corruptos o incompletos.")
    
    print("=" * 60)
    return sin_historial, len(candidatos) - sin_historial

def desactivacion_masiva():
    """Inactiva de forma masiva a todos los usuarios no administradores."""
    print("\nEjecutando DESACTIVACIÓN MASIVA (Soft-Deactivation)...")
    try:
        # Filtrar usuarios que no sean administradores
        usuarios_afectados = Usuario.query.filter(Usuario.rol != 'administrador').all()
        conteo = 0
        
        for u in usuarios_afectados:
            u.estado = 'inactivo'
            conteo += 1
            
        db.session.commit()
        print(f"[ÉXITO] Se han desactivado {conteo} usuarios de forma segura.")
        print("[INFO] Sus registros e historial de préstamos se conservan intactos en la DB.")
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] No se pudo completar la desactivación: {e}")

def reset_sequences():
    """Resetea las secuencias de autoincremento en PostgreSQL para evitar huecos."""
    print("\nOptimizando y reiniciando secuencias de IDs en PostgreSQL...")
    try:
        # Lista de tablas, sus columnas llave primaria y nombres de secuencia
        secuencias = [
            ('usuarios', 'id_usuario', 'usuarios_id_usuario_seq'),
            ('prestamos', 'id_prestamo', 'prestamos_id_prestamo_seq'),
            ('prestamos_libros', 'id_prestamo_libro', 'prestamos_libros_id_prestamo_libro_seq'),
            ('libros', 'id_libro', 'libros_id_libro_seq'),
            ('equipos', 'id_equipo', 'equipos_id_equipo_seq')
        ]
        
        for tabla, col, seq in secuencias:
            # Obtener el ID máximo actual
            result = db.session.execute(db.text(f"SELECT COALESCE(MAX({col}), 0) FROM {tabla}"))
            max_id = result.scalar()
            
            # Reiniciar la secuencia al ID máximo actual. 
            if max_id == 0:
                db.session.execute(db.text(f"SELECT setval('{seq}', 1, false)"))
            else:
                db.session.execute(db.text(f"SELECT setval('{seq}', {max_id}, true)"))
            print(f"  - Secuencia '{seq}' reiniciada con éxito (Valor actual: {max_id}).")
            
        db.session.commit()
        print("[ÉXITO] Secuencias de IDs sincronizadas y optimizadas correctamente.")
    except Exception as e:
        db.session.rollback()
        # Es normal que falle en SQLite local ya que SQLite no tiene objetos secuencia como PostgreSQL
        print(f"  [INFO] Omitiendo reinicio de secuencias en SQLite local: {e}")

def delete_seguro():
    """Elimina físicamente a los usuarios sin historial y desactiva a los que sí tienen historial."""
    print("\nEjecutando ELIMINACIÓN SEGURA MIXTA...")
    try:
        usuarios_a_revisar = Usuario.query.filter(Usuario.rol != 'administrador').all()
        eliminados = 0
        desactivados = 0
        
        for u in usuarios_a_revisar:
            has_equipos = Prestamo.query.filter_by(id_usuario=u.id_usuario).count() > 0
            has_libros = PrestamoLibro.query.filter_by(id_usuario=u.id_usuario).count() > 0
            
            if has_equipos or has_libros:
                # Si tiene historial, lo desactivamos para evitar violaciones de clave foránea
                u.estado = 'inactivo'
                desactivados += 1
            else:
                # Si no tiene ningún historial, lo eliminamos físicamente de forma segura
                db.session.delete(u)
                eliminados += 1
                
        db.session.commit()
        print(f"[ÉXITO] Limpieza finalizada correctamente:")
        print(f"  - Usuarios ELIMINADOS físicamente (sin historial): {eliminados}")
        print(f"  - Usuarios DESACTIVADOS (con préstamos asociados): {desactivados}")
        print("  - Administradores PROTEGIDOS: Todo el personal administrativo quedó intacto.")
        
        # Reiniciar secuencias de IDs para un entorno limpio
        reset_sequences()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR CRÍTICO] La transacción falló. Se realizó un ROLLBACK automático. Detalles: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gestor de Limpieza Segura de Usuarios - SENA")
    parser.add_argument('--diagnose', action='store_true', help="Ejecutar solo el diagnóstico de seguridad.")
    parser.add_argument('--desactivar', action='store_true', help="Desactivar masivamente a los usuarios (100% seguro).")
    parser.add_argument('--eliminar', action='store_true', help="Eliminar físicamente a usuarios sin historial e inactivar al resto.")
    
    args = parser.parse_args()
    
    # Si no se pasa ningún argumento, por defecto ejecuta el diagnóstico
    if not (args.diagnose or args.desactivar or args.eliminar):
        args.diagnose = True
        
    with app.app_context():
        if args.diagnose:
            run_diagnostico()
            print("\nInstrucciones de uso:")
            print("  - Para DESACTIVAR masivamente (Recomendado): python clean_users.py --desactivar")
            print("  - Para ELIMINAR físicamente (Solo cuentas sin historial): python clean_users.py --eliminar")
            
        elif args.desactivar:
            run_diagnostico()
            confirmacion = input("\n¿ESTÁS COMPLETAMENTE SEGURO de desactivar a todos estos usuarios? (escribe 'SI' para confirmar): ")
            if confirmacion.strip().upper() == 'SI':
                desactivacion_masiva()
            else:
                print("Operación cancelada por el usuario.")
                
        elif args.eliminar:
            sin_historial, con_historial = run_diagnostico()
            print(f"\nATENCIÓN:")
            print(f"  * {sin_historial} usuarios serán eliminados permanentemente (DELETE).")
            print(f"  * {con_historial} usuarios con préstamos asociados serán desactivados (inactivo) para proteger la integridad.")
            confirmacion = input("\n¿ESTÁS COMPLETAMENTE SEGURO de proceder con esta limpieza? (escribe 'SI' para confirmar): ")
            if confirmacion.strip().upper() == 'SI':
                delete_seguro()
            else:
                print("Operación cancelada por el usuario.")

if __name__ == "__main__":
    main()
