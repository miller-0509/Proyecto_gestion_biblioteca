import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Clase NumberedCanvas para paginación dinámica e imagen de marca SENA
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        self.saveState()
        
        # Color SENA Green
        sena_green = colors.HexColor('#39A900')
        sena_dark = colors.HexColor('#00303F')
        border_gray = colors.HexColor('#E5E5E5')
        text_gray = colors.HexColor('#555555')
        
        if self._pageNumber == 1:
            # Decoración de la portada
            # Barra lateral verde
            self.setFillColor(sena_green)
            self.rect(0, 0, 30, 792, fill=True, stroke=False)
            
            # Barra lateral oscura
            self.setFillColor(sena_dark)
            self.rect(30, 0, 10, 792, fill=True, stroke=False)
            
            # Línea decorativa inferior
            self.setFillColor(sena_green)
            self.rect(40, 40, 532, 10, fill=True, stroke=False)
        else:
            # Páginas de contenido - Encabezado
            self.setStrokeColor(border_gray)
            self.setLineWidth(0.5)
            self.line(54, 730, 558, 730)
            
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(sena_dark)
            self.drawString(54, 735, "SISTEMA DE GESTIÓN DE BIBLIOTECA Y ALMACÉN - SENA")
            
            # Páginas de contenido - Pie de página
            self.line(54, 50, 558, 50)
            
            self.setFont("Helvetica", 8)
            self.setFillColor(text_gray)
            self.drawString(54, 38, "Servicio Nacional de Aprendizaje (SENA) | Dirección de Formación Profesional")
            
            # Paginación "Página X de Y"
            page_text = f"Página {self._pageNumber} de {page_count}"
            self.drawRightString(558, 38, page_text)
            
        self.restoreState()


def generar_pdf_manual(rol_key, config_rol, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filename = f"manual_{rol_key}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Márgenes: izquierda 54 (0.75"), derecha 54, arriba 80, abajo 80
    doc = SimpleDocTemplate(
        filepath, 
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=80,
        bottomMargin=80
    )
    
    styles = getSampleStyleSheet()
    
    # Paleta de colores SENA
    color_primary = colors.HexColor('#39A900') # Verde SENA
    color_secondary = colors.HexColor('#00303F') # Gris/Teal Oscuro SENA
    color_text = colors.HexColor('#333333') # Texto principal
    color_bg_table = colors.HexColor('#F4F6F9') # Fondo gris suave
    
    # Estilos de Párrafo personalizados
    title_style = ParagraphStyle(
        name='ManualTitle', 
        parent=styles['Heading1'], 
        fontName='Helvetica-Bold', 
        fontSize=24, 
        leading=28, 
        textColor=color_secondary, 
        spaceAfter=15, 
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        name='ManualSubtitle', 
        parent=styles['Normal'], 
        fontName='Helvetica', 
        fontSize=13, 
        leading=16, 
        textColor=colors.HexColor('#666666'), 
        spaceAfter=30, 
        alignment=0
    )
    
    h1_style = ParagraphStyle(
        name='ManualH1', 
        parent=styles['Heading1'], 
        fontName='Helvetica-Bold', 
        fontSize=15, 
        leading=18, 
        textColor=color_primary, 
        spaceBefore=18, 
        spaceAfter=10, 
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        name='ManualH2', 
        parent=styles['Heading2'], 
        fontName='Helvetica-Bold', 
        fontSize=11, 
        leading=14, 
        textColor=color_secondary, 
        spaceBefore=12, 
        spaceAfter=6, 
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        name='ManualBody', 
        parent=styles['Normal'], 
        fontName='Helvetica', 
        fontSize=9.5, 
        leading=14, 
        textColor=color_text, 
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        name='ManualBullet', 
        parent=styles['Normal'], 
        fontName='Helvetica', 
        fontSize=9.5, 
        leading=14, 
        textColor=color_text, 
        leftIndent=15, 
        firstLineIndent=-10, 
        spaceAfter=5
    )
    
    note_style = ParagraphStyle(
        name='ManualNote', 
        parent=styles['Normal'], 
        fontName='Helvetica-Oblique', 
        fontSize=9, 
        leading=13, 
        textColor=colors.HexColor('#555555'), 
        backColor=colors.HexColor('#E8F5E9'), 
        borderColor=color_primary, 
        borderWidth=0.5, 
        borderPadding=8, 
        spaceBefore=10, 
        spaceAfter=10
    )

    alert_style = ParagraphStyle(
        name='ManualAlert', 
        parent=styles['Normal'], 
        fontName='Helvetica-Oblique', 
        fontSize=9, 
        leading=13, 
        textColor=colors.HexColor('#721C24'), 
        backColor=colors.HexColor('#F8D7DA'), 
        borderColor=colors.HexColor('#F5C6CB'), 
        borderWidth=0.5, 
        borderPadding=8, 
        spaceBefore=10, 
        spaceAfter=10
    )

    elements = []
    
    # ------------------ PORTADA ------------------
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("SISTEMA DE GESTIÓN DE BIBLIOTECA Y ALMACÉN", ParagraphStyle(name='Port1', fontName='Helvetica-Bold', fontSize=12, leading=14, textColor=color_primary, spaceAfter=10)))
    elements.append(Paragraph("MANUAL DE USUARIO", title_style))
    elements.append(Paragraph(f"ROL: {config_rol['nombre_rol'].upper()}", ParagraphStyle(name='Port2', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=color_secondary, spaceAfter=20)))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Guía detallada de navegación, funcionalidades, permisos y límites del sistema para el rol especificado.", subtitle_style))
    
    elements.append(Spacer(1, 120))
    
    # Tabla de metadata en la portada
    meta_data = [
        [Paragraph("<b>Entidad:</b>", body_style), Paragraph("Servicio Nacional de Aprendizaje (SENA)", body_style)],
        [Paragraph("<b>Versión:</b>", body_style), Paragraph("1.0 (Mayo 2026)", body_style)],
        [Paragraph("<b>Soporte:</b>", body_style), Paragraph("soporte.biblioteca.almacen@sena.edu.co", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[80, 250])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(meta_table)
    elements.append(PageBreak())
    
    # ------------------ CONTENIDO ------------------
    
    # 1. Introducción
    elements.append(Paragraph("1. Introducción al Rol", h1_style))
    elements.append(Paragraph(config_rol['introduccion'], body_style))
    
    # Límites del Rol (tabla o nota)
    elements.append(Paragraph(f"<b>Reglas de Operación y Límites:</b>", h2_style))
    elements.append(Paragraph(f"• <b>Límite de Préstamos Activos Simultáneos:</b> {config_rol['limite_prestamos']} elementos en total (aplica a la suma de libros y equipos).", bullet_style))
    for regla in config_rol['reglas']:
        elements.append(Paragraph(f"• {regla}", bullet_style))
        
    elements.append(Spacer(1, 10))
    
    # 2. Acceso y Seguridad
    elements.append(Paragraph("2. Acceso y Seguridad", h1_style))
    elements.append(Paragraph("Para ingresar al sistema, siga los siguientes pasos:", body_style))
    elements.append(Paragraph("1. Acceda a la URL del portal institucional de biblioteca y almacén.", bullet_style))
    elements.append(Paragraph("2. Ingrese su correo electrónico institucional registrado y contraseña en la pantalla de inicio de sesión.", bullet_style))
    elements.append(Paragraph("3. Presione el botón <b>Iniciar Sesión</b>. Si los datos son válidos y su cuenta se encuentra en estado <b>Activo</b>, será redirigido al Dashboard principal.", bullet_style))
    
    elements.append(Paragraph("<b>Nota sobre Seguridad y Estados de Cuenta:</b>", note_style))
    elements.append(Paragraph("• Si introduce una contraseña incorrecta repetidamente, su cuenta puede ser bloqueada de forma preventiva.<br/>"
                             "• Si su correo electrónico no ha sido verificado, recibirá un aviso indicando que debe validar su bandeja de entrada mediante el enlace de verificación enviado al registrarse.", body_style))
    
    # 3. Interfaz Principal
    elements.append(Paragraph("3. Interfaz y Panel de Inicio", h1_style))
    elements.append(Paragraph("Una vez autenticado, visualizará un panel de bienvenida con accesos rápidos adaptados a su rol. En la parte superior se ubica la barra de navegación que contiene las siguientes opciones:", body_style))
    
    # Listar menús accesibles
    for menu, desc in config_rol['menu_desc'].items():
        elements.append(Paragraph(f"• <b>{menu}:</b> {desc}", bullet_style))
        
    elements.append(PageBreak())
    
    # 4. Guía de Módulos y Operaciones
    elements.append(Paragraph("4. Guía Detallada de Módulos", h1_style))
    
    for modulo, operacion in config_rol['modulos_detalles'].items():
        elements.append(Paragraph(modulo, h2_style))
        elements.append(Paragraph(operacion['descripcion'], body_style))
        
        # Acciones clave
        elements.append(Paragraph("<b>Acciones Clave:</b>", ParagraphStyle(name='SubSub', fontName='Helvetica-Bold', fontSize=9, leading=12, spaceBefore=4, spaceAfter=4)))
        for accion in operacion['acciones']:
            elements.append(Paragraph(f"  - {accion}", bullet_style))
            
        elements.append(Spacer(1, 8))
        
    # 5. Sanciones y Multas
    elements.append(Paragraph("5. Sanciones y Multas (Sistema de Penalización)", h1_style))
    elements.append(Paragraph("El sistema cuenta con un módulo de multas automatizado para asegurar la devolución oportuna de los recursos prestados:", body_style))
    elements.append(Paragraph("• <b>Generación de Multas:</b> Cuando un préstamo excede la fecha de devolución esperada sin ser devuelto, el sistema automáticamente inicia la acumulación de una multa diaria.", bullet_style))
    elements.append(Paragraph("• <b>Consecuencias:</b> Un usuario que tenga multas en estado 'acumulando' o 'activa' quedará <b>bloqueado automáticamente</b> para solicitar nuevos préstamos de libros o de equipos.", bullet_style))
    
    if rol_key in ['administrador', 'bibliotecario', 'almacenista']:
        elements.append(Paragraph("<b>Gestión Administrativa de Multas:</b>", h2_style))
        elements.append(Paragraph("Como miembro del equipo de gestión, usted puede ingresar al módulo <b>Sanciones</b> para visualizar la lista de usuarios con multas vigentes. Una vez el usuario regrese el recurso o se regularice la situación, el administrador (o el rol respectivo) puede procesar la liberación de la multa en el sistema para restablecer los derechos de préstamo del usuario.", body_style))
    else:
        elements.append(Paragraph("<b>Atención al Usuario:</b>", alert_style))
        elements.append(Paragraph("Para solucionar una sanción, debe hacer la entrega física del recurso retrasado en la biblioteca o almacén. Una vez devuelto el material, el encargado del módulo registrará la entrega y procederá a liberar la sanción en el sistema para desbloquear su perfil.", body_style))
        
    elements.append(Spacer(1, 10))
    
    # 6. Soporte
    elements.append(Paragraph("6. Canales de Ayuda y Soporte", h1_style))
    elements.append(Paragraph("Si presenta inconvenientes técnicos o inconsistencias en sus préstamos, por favor póngase en contacto con los siguientes canales:", body_style))
    
    soporte_data = [
        ["Área de Soporte", "Correo Electrónico", "Ubicación Física"],
        ["Soporte Técnico Sistema", "soporte.biblioteca.almacen@sena.edu.co", "Oficina de Sistemas - Edif. Central"],
        ["Gestión Biblioteca (Libros)", "biblioteca.soporte@sena.edu.co", "Segundo Piso - Sala de Lectura"],
        ["Gestión Almacén (Equipos)", "almacen.soporte@sena.edu.co", "Primer Piso - Ventanilla de Inventario"]
    ]
    
    soporte_table = Table(soporte_data, colWidths=[150, 180, 170])
    soporte_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), color_secondary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    
    elements.append(soporte_table)
    
    # Construcción final del documento
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Manual generado con éxito: {filepath}")


# Datos de configuración para cada uno de los 5 roles
MANUALES_CONFIG = {
    'administrador': {
        'nombre_rol': 'Administrador del Sistema',
        'limite_prestamos': 'Sin Límite (999)',
        'reglas': [
            "Tiene control total sobre todos los módulos del sistema.",
            "Es el único rol que puede realizar la gestión integral de Usuarios (CRUD y bloqueo/activación).",
            "Puede auditar e intervenir en los préstamos y multas de cualquier otra área (Biblioteca y Almacén)."
        ],
        'introduccion': "El rol de Administrador es el encargado de supervisar el correcto funcionamiento del sistema, configurar los parámetros globales, dar soporte a otros roles administrativos y auditar las operaciones de préstamos e inventarios generales.",
        'menu_desc': {
            'Inicio (Dashboard)': "Visualiza un resumen gráfico con estadísticas de préstamos activos, usuarios registrados, multas acumuladas y alertas de inventario.",
            'Equipos': "Acceso completo al catálogo e inventario físico de herramientas y equipos tecnológicos.",
            'Libros': "Acceso completo al catálogo e inventario físico de recursos bibliográficos.",
            'Préstamos': "Acceso a la visualización global y administración de préstamos tanto de libros como de equipos.",
            'Reportes': "Panel de control avanzado que permite filtrar historiales de inventario y transacciones para exportar a formatos Excel y PDF.",
            'Sanciones': "Módulo para supervisar, aplicar y liberar multas a los usuarios por infracción de políticas de préstamo.",
            'Usuarios': "Módulo exclusivo para crear, editar, cambiar roles y suspender cuentas de usuarios del sistema."
        },
        'modulos_detalles': {
            'A. Gestión de Usuarios': {
                'descripcion': "Permite la administración de las cuentas. El administrador puede crear nuevos usuarios y modificar su rol o estado de vigencia.",
                'acciones': [
                    "Crear usuario: Registro manual de aprendices, instructores, bibliotecarios o almacenistas.",
                    "Modificar usuario: Edición de nombres, apellidos, correo institucional y cambio de rol.",
                    "Administración de Estado: Cambiar cuenta a 'Inactivo' o 'Bloqueado' para revocar permisos de inicio de sesión de forma inmediata."
                ]
            },
            'B. Control de Inventarios': {
                'descripcion': "Visualización y edición de los dos catálogos principales del sistema (Biblioteca y Almacén).",
                'acciones': [
                    "Registrar Libro o Equipo: Inserción de nuevos elementos asignando códigos únicos u hojas de servicio.",
                    "Actualización de Estado Físico: Cambiar el estado de un recurso a Mantenimiento, Extraviado o Dañado.",
                    "Eliminación lógica: Dar de baja elementos obsoletos para ocultarlos del catálogo público."
                ]
            },
            'C. Supervisión de Préstamos': {
                'descripcion': "Monitoreo integral de los flujos de préstamos institucionales.",
                'acciones': [
                    "Aprobación de Solicitudes: Aprobar o rechazar solicitudes de préstamos pendientes creadas por aprendices/instructores.",
                    "Procesar Devoluciones: Registrar la entrega de equipos o libros y verificar que coincida con el estado registrado inicialmente."
                ]
            }
        }
    },
    'bibliotecario': {
        'nombre_rol': 'Bibliotecario',
        'limite_prestamos': '5',
        'reglas': [
            "Tiene restringido el acceso al módulo de Almacén y Gestión de Equipos.",
            "No puede modificar ni listar cuentas de usuarios en el sistema.",
            "Es el encargado exclusivo de administrar el catálogo de libros, préstamos de libros y multas asociadas a la biblioteca."
        ],
        'introduccion': "El rol de Bibliotecario es responsable de la administración del catálogo de libros físicos del SENA, facilitando el préstamo y devolución de materiales a aprendices e instructores, y controlando las sanciones correspondientes por retrasos en devoluciones.",
        'menu_desc': {
            'Inicio (Dashboard)': "Visualiza estadísticas e indicadores clave sobre libros prestados, inventario disponible y multas de biblioteca activas.",
            'Libros': "Módulo de catalogación y administración de los libros físicos.",
            'Préstamos': "Acceso directo a la administración (Ver Todos, aprobar, devolver) exclusivamente para préstamos de Libros.",
            'Reportes': "Exportación de reportes de inventario de biblioteca y préstamos de libros en Excel y PDF.",
            'Sanciones': "Visualizar y liberar multas originadas por demoras en la devolución de libros."
        },
        'modulos_detalles': {
            'A. Gestión de Catálogo de Libros': {
                'descripcion': "Catalogación y registro sistemático de los títulos disponibles en la sala de lectura.",
                'acciones': [
                    "Registrar Libro: Agregar título, autor, género literario, código único y ubicación física en estantería.",
                    "Actualización de Ficha: Modificar los datos del libro o su estado (Disponible, Dañado, Perdido).",
                    "Baja de Material: Retirar del catálogo aquellos libros destruidos u obsoletos."
                ]
            },
            'B. Gestión de Préstamos de Libros': {
                'descripcion': "Administración de todo el ciclo de vida de los préstamos bibliotecarios.",
                'acciones': [
                    "Aprobar Préstamo: Revisar solicitudes pendientes y confirmar la entrega del libro físico al solicitante.",
                    "Registrar Devolución: Recibir el libro devuelto, verificar su estado físico y dar por finalizado el préstamo en el sistema."
                ]
            }
        }
    },
    'almacenista': {
        'nombre_rol': 'Almacenista de Equipos',
        'limite_prestamos': '5',
        'reglas': [
            "Tiene restringido el acceso al módulo de Biblioteca y Catalogación de Libros.",
            "No tiene acceso a la visualización o edición de los usuarios del sistema.",
            "Administra exclusivamente el catálogo de equipos tecnológicos y sus préstamos correspondientes."
        ],
        'introduccion': "El rol de Almacenista se encarga del control físico e inventario de los equipos tecnológicos (computadores, proyectores, herramientas de taller) que el SENA dispone para préstamo pedagógico, garantizando su mantenimiento, disponibilidad y correcta asignación.",
        'menu_desc': {
            'Inicio (Dashboard)': "Visualiza métricas del estado del almacén, cantidad de equipos en préstamo, equipos en mantenimiento y multas vigentes de almacén.",
            'Equipos': "Catálogo y registro del inventario tecnológico del almacén.",
            'Préstamos': "Acceso directo a la administración (Ver Todos, aprobar, devolver) de préstamos de Equipos únicamente.",
            'Reportes': "Visualizar y exportar reportes de inventario de equipos y préstamos tecnológicos en Excel y PDF.",
            'Sanciones': "Monitoreo y liberación de multas originadas por demoras o incidentes con los equipos."
        },
        'modulos_detalles': {
            'A. Control de Catálogo de Equipos': {
                'descripcion': "Registro de los bienes e insumos del almacén tecnológico.",
                'acciones': [
                    "Registrar Equipo: Agregar nombre del equipo, tipo, marca, modelo, número de serie y ubicación física en almacén.",
                    "Estado Técnico: Cambiar el estado de un equipo a 'Mantenimiento' cuando requiera revisión o 'Baja' por daño irreparable.",
                    "Eliminación lógica: Ocultar del catálogo los equipos dados de baja permanentemente."
                ]
            },
            'B. Control de Préstamos de Almacén': {
                'descripcion': "Flujo para la asignación y devolución de equipos tecnológicos.",
                'acciones': [
                    "Aprobar Préstamo: Validar solicitudes pendientes y registrar la entrega del equipo tecnológico al usuario.",
                    "Registrar Devolución: Recibir el equipo físico, comprobar su funcionamiento e integridad, y liberar el registro de préstamo."
                ]
            }
        }
    },
    'aprendiz': {
        'nombre_rol': 'Aprendiz SENA',
        'limite_prestamos': '3',
        'reglas': [
            "No tiene acceso a las pantallas de creación o modificación de inventario.",
            "No puede ver préstamos ni multas de otros usuarios del sistema.",
            "Cualquier multa activa bloquea por completo la capacidad de solicitar nuevos préstamos."
        ],
        'introduccion': "El Aprendiz es el usuario final del sistema que requiere acceso a los recursos pedagógicos de biblioteca y equipos para apoyar su proceso de formación técnica o tecnológica en la institución.",
        'menu_desc': {
            'Inicio (Dashboard)': "Visualiza un panel de bienvenida con el estado general de su cuenta, si posee multas activas y sus préstamos vigentes.",
            'Equipos': "Consulta en tiempo real el inventario de equipos disponibles en almacén.",
            'Libros': "Consulta en tiempo real el catálogo de libros disponibles en biblioteca.",
            'Préstamos': "Permite ver la lista de sus préstamos de libros/equipos y solicitar nuevos préstamos.",
            'Sanciones': "Consulta el detalle y valor de sus multas vigentes por entregas tardías."
        },
        'modulos_detalles': {
            'A. Búsqueda en Catálogo': {
                'descripcion': "Permite la exploración de materiales para encontrar elementos de interés formativo.",
                'acciones': [
                    "Búsqueda de Libros: Filtrar títulos por autor, género literario o código único.",
                    "Búsqueda de Equipos: Consultar por tipo de equipo o marca para verificar disponibilidad física."
                ]
            },
            'B. Solicitud de Préstamos': {
                'descripcion': "Proceso para reservar y retirar materiales o herramientas de la sede.",
                'acciones': [
                    "Crear Solicitud: Seleccionar el recurso e ingresar la fecha estimada de devolución para la revisión del administrador.",
                    "Seguimiento de Estado: Verificar si la solicitud ha sido 'Aceptada', 'Rechazada' o si sigue 'Pendiente'."
                ]
            },
            'C. Historial de Préstamos': {
                'descripcion': "Registro personal e histórico del usuario.",
                'acciones': [
                    "Mi Historial: Visualizar todos los libros y equipos que ha solicitado y devuelto en su historial dentro del SENA."
                ]
            }
        }
    },
    'instructor': {
        'nombre_rol': 'Instructor SENA',
        'limite_prestamos': '8',
        'reglas': [
            "Tiene un límite ampliado de hasta 8 préstamos simultáneos para facilitar el material a sus grupos.",
            "No tiene privilegios administrativos sobre inventarios o cuentas de otros usuarios.",
            "Cualquier multa activa bloquea la capacidad de registrar nuevas solicitudes de préstamo."
        ],
        'introduccion': "El Instructor es un usuario docente del SENA que cuenta con privilegios extendidos de préstamo simultáneo para asegurar los materiales y herramientas didácticas necesarios para guiar las clases y talleres de formación.",
        'menu_desc': {
            'Inicio (Dashboard)': "Visualiza un resumen rápido con sus préstamos actuales, fechas de devolución próximas y estado de multas.",
            'Equipos': "Consulta el stock técnico de equipos y herramientas en almacén.",
            'Libros': "Consulta el stock y ubicación de los libros de la biblioteca.",
            'Préstamos': "Acceso para revisar la lista de sus solicitudes, estados de préstamos y generar nuevas solicitudes.",
            'Sanciones': "Consulta detalles de multas o penalidades en su cuenta."
        },
        'modulos_detalles': {
            'A. Búsqueda e Inventarios': {
                'descripcion': "Exploración de catálogos para planeación académica y pedagógica.",
                'acciones': [
                    "Consulta Avanzada: Verificar disponibilidad de lotes de equipos o títulos bibliográficos para sesiones didácticas."
                ]
            },
            'B. Solicitud y Renovaciones': {
                'descripcion': "Petición de recursos para impartir formación.",
                'acciones': [
                    "Crear Solicitud: Escoger recursos e indicar la fecha de devolución esperada para que el encargado apruebe la entrega.",
                    "Solicitar Renovación: Tramitar una solicitud de extensión de plazo si las actividades curriculares se extienden."
                ]
            },
            'C. Historial Académico': {
                'descripcion': "Seguimiento de los insumos didácticos utilizados en trimestres anteriores.",
                'acciones': [
                    "Mi Historial: Consultar y descargar el registro histórico de préstamos personales."
                ]
            }
        }
    }
}


if __name__ == "__main__":
    output_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "static", "manuales"))
    print(f"Generando manuales de usuario en: {output_directory}")
    for rol, config in MANUALES_CONFIG.items():
        generar_pdf_manual(rol, config, output_directory)
    print("Todos los manuales se han generado exitosamente en PDF.")
