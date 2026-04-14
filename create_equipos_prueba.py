"""
Script para agregar equipos de prueba
"""
from app import create_app, db
from app.models.equipos import Equipo
from datetime import date, timedelta

app = create_app()

with app.app_context():
    # Equipos de prueba
    equipos_prueba = [
        {
            'nombre': 'Portátil Lenovo ThinkPad',
            'tipo_equipo': 'Laptop',
            'marca': 'Lenovo',
            'modelo': 'ThinkPad E15',
            'numero_serie': 'LP001-2024-0001',
            'estado': 'disponible',
            'ubicacion': 'Biblioteca',
            'fecha_compra': date(2023, 6, 15),
            'proveedor': 'Tech Solutions Inc.',
            'responsable': 'Área de Sistemas',
            'disponible_prestamo': True,
            'tiempo_max_prestamo': 7,
            'descripcion': 'Laptop para consultas en biblioteca'
        },
        {
            'nombre': 'Monitor Dell 27"',
            'tipo_equipo': 'Monitor',
            'marca': 'Dell',
            'modelo': 'U2723DE',
            'numero_serie': 'MON001-2024-0002',
            'estado': 'disponible',
            'ubicacion': 'Sala de Cómputo',
            'fecha_compra': date(2023, 8, 20),
            'proveedor': 'Dell Direct',
            'responsable': 'TI',
            'disponible_prestamo': False,
            'tiempo_max_prestamo': None,
            'descripcion': 'Monitor para estación fija'
        },
        {
            'nombre': 'Teclado Mecánico Corsair',
            'tipo_equipo': 'Teclado',
            'marca': 'Corsair',
            'modelo': 'K95 RGB Platinum',
            'numero_serie': 'KBD001-2024-0003',
            'estado': 'disponible',
            'ubicacion': 'Almacén',
            'fecha_compra': date(2024, 1, 10),
            'proveedor': 'Corsair Store',
            'responsable': 'Almacén',
            'disponible_prestamo': True,
            'tiempo_max_prestamo': 5,
            'descripcion': 'Teclado mecánico para préstamo'
        },
        {
            'nombre': 'Proyector Epson',
            'tipo_equipo': 'Proyector',
            'marca': 'Epson',
            'modelo': 'EB-2250U',
            'numero_serie': 'PROJ001-2024-0004',
            'estado': 'mantenimiento',
            'ubicacion': 'Almacén',
            'fecha_compra': date(2022, 12, 5),
            'proveedor': 'Epson Oficial',
            'responsable': 'Mantenimiento',
            'disponible_prestamo': False,
            'tiempo_max_prestamo': None,
            'descripcion': 'En mantenimiento - cambio de lámpara'
        },
        {
            'nombre': 'Tablet Samsung Galaxy Tab S6',
            'tipo_equipo': 'Tablet',
            'marca': 'Samsung',
            'modelo': 'Galaxy Tab S6',
            'numero_serie': 'TAB001-2024-0005',
            'estado': 'disponible',
            'ubicacion': 'Biblioteca',
            'fecha_compra': date(2023, 9, 15),
            'proveedor': 'Samsung Colombia',
            'responsable': 'Área Infantil',
            'disponible_prestamo': True,
            'tiempo_max_prestamo': 3,
            'descripcion': 'Tablet para consulta de catálogo digital'
        }
    ]
    
    # Verificar equipos existentes
    equipos_existentes = Equipo.query.count()
    
    if equipos_existentes > 0:
        print(f"⚠ Ya hay {equipos_existentes} equipos en la base de datos")
    else:
        # Agregar equipos de prueba
        for equipo_data in equipos_prueba:
            equipo = Equipo(**equipo_data)
            db.session.add(equipo)
        
        db.session.commit()
        print(f"✓ Se agregaron {len(equipos_prueba)} equipos de prueba exitosamente")
        
        # Mostrar resumen
        for i, eq_data in enumerate(equipos_prueba, 1):
            print(f"  {i}. {eq_data['nombre']} - Serie: {eq_data['numero_serie']}")
