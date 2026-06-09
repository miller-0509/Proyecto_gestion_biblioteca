# 📚 Sistema de Gestión de Biblioteca y Almacén SENA

> Plataforma web para la administración profesional y centralizada de préstamos de libros y equipos tecnológicos, orientada a instituciones educativas, con una arquitectura sólida de control de accesos (RBAC), tareas automatizadas y patrón de diseño MVC.

---

## 📋 Descripción

El **Sistema de Gestión de Biblioteca y Almacén** es una aplicación web empresarial desarrollada con Flask y PostgreSQL que permite administrar de forma centralizada el inventario y los préstamos físicos de una institución. 

El sistema cuenta con un control de accesos robusto basado en 5 roles jerárquicos, garantizando la seguridad en el backend y una interfaz dinámica en el frontend que se adapta a los privilegios de cada usuario. Su objetivo principal es digitalizar, asegurar y agilizar todos los procesos de solicitud, seguimiento y auditoría de recursos.

---

## ✨ Funcionalidades Principales

### 👥 Gestión Avanzada de Usuarios y Roles (RBAC)
- Jerarquía de 5 roles con permisos y límites estrictos:
  - **Administrador**: Control total sobre todos los módulos y gestión de personal. Sin límites de préstamo.
  - **Bibliotecario**: Gestión exclusiva de libros. Límite de 5 préstamos. No ve equipos.
  - **Almacenista**: Gestión exclusiva de equipos. Límite de 5 préstamos. No ve libros.
  - **Instructor**: Nivel usuario. Límite de 5 préstamos combinados.
  - **Aprendiz**: Nivel usuario. Límite de 3 préstamos combinados.
- Control dinámico de UI: El menú lateral, dashboard y botones de acción se ocultan/muestran según el rol de la sesión.
- Control de estado por cuenta: `activo`, `inactivo` o `bloqueado`.

### 🛡️ Seguridad y Autenticación
- **Verificación de Correo (Mailing)**: Los aprendices e instructores deben verificar su correo con tokens para iniciar sesión. El personal administrativo está exento de este paso para agilizar operaciones.
- **Recuperación de Contraseña**: Flujo profesional "¿Olvidaste tu contraseña?" con envío de correos y enlaces criptográficos temporales (`itsdangerous`).
- **Decoradores de Seguridad**: Uso de `@gestion_libros_required`, `@gestion_equipos_required`, `@admin_required` para proteger rutas en el backend.

### 📖 Inventario (Libros y Equipos)
- Inventarios detallados: Títulos, seriales, marcas, códigos únicos, ubicaciones y responsables.
- **Gestión de Estados Manual y Excepciones**: Cambios a estado de `daño`, `mantenimiento`, `pérdida`, `baja`, `reparación`, `bloqueo temporal`, `recuperación`.
- Registro histórico inmutable de todos los cambios de estado (auditoría).

### 🔄 Sistema de Préstamos e Historial
- Solicitudes con flujo completo: `pendiente` → `aceptado` / `rechazado` → `devuelto`.
- Límite estricto de préstamos activos combinados según el rol.
- Renovaciones de préstamos (para libros).
- Prevención de duplicados o superposiciones en disponibilidad.

### 📊 Reportes y Dashboard
- **Dashboard en Tiempo Real**: Estadísticas de inventario, préstamos activos y multas pendientes.
- **Reportes Específicos**: Descargas de reportes detallados y listados sobre la actividad del sistema.

### 🤖 Procesos Automatizados (Cron Jobs)
El sistema incluye scripts que se pueden configurar como tareas en segundo plano (Cron o Tareas Programadas) para automatizar procesos clave:
- **`enviar_recordatorios.py`**: Escanea diariamente los préstamos e informa por correo electrónico si un préstamo está próximo a vencer (menos de 24h) o si ya se encuentra vencido.
- **`cron_multas.py`**: Automatización del servicio de multas (`actualizar_multas_diarias`). Identifica los préstamos vencidos que superaron la fecha límite y aplica automáticamente los cargos o recargos de mora diarios.

---

## 🏗️ Arquitectura del Sistema (Patrón MVC)

La aplicación sigue el patrón de diseño **Modelo-Vista-Controlador (MVC)**, implementado a través del framework Flask:

### 1. Modelos (Entidades de Base de Datos)
Mapean la estructura de PostgreSQL a objetos de Python usando SQLAlchemy (`app/models/`):
- `Usuario`, `Libro`, `Equipo`
- `PrestamoLibro` y `Prestamo` (Equipos)
- `Renovacion` (Historial de extensiones de libros)
- `Multa` (Recargos automáticos por mora)

### 2. Vistas (Templates)
Interfaces renderizadas desde el servidor (`app/templates/`) utilizando Jinja2, HTML5, CSS Vanilla y Bootstrap. Incluyen:
- Modulos CRUD separados por carpetas (`/usuarios`, `/libros`, `/equipos`, `/prestamos_libros`, etc.).
- Paneles maestros dinámicos como `dashboard.html` y `menu.html`.
- Sistema de alertas e interfaces responsivas.

### 3. Controladores (Rutas)
Lógica de negocio y enrutamiento en (`app/routes/`):
- `auth.py`: Autenticación y flujos de acceso.
- `usuarios.py`, `libros.py`, `equipos.py`: Controladores CRUD de entidades principales.
- `prestamos.py`, `prestamos_libros.py`: Lógica transaccional de asignación y devolución.
- `multas.py`, `reportes.py`: Procesamiento de estados financieros, multas y analítica.

---

## 🛠️ Tecnologías utilizadas

| Tecnología | Versión | Descripción |
|---|---|---|
| **Python** | 3.x | Lenguaje principal del backend |
| **Flask** | 3.1.0 | Framework web |
| **PostgreSQL** | 16+ | Base de datos relacional robusta |
| **Flask-SQLAlchemy** | 3.1.1 | ORM avanzado para consultas |
| **Flask-Login** | 0.6.3 | Gestión de sesiones seguras |
| **Flask-Mail** | - | Envío de correos (Verificaciones, Recordatorios) |
| **itsdangerous** | - | Tokens temporales criptográficos |
| **Bootstrap / CSS** | 5.3 | Interfaz dinámica y responsiva |

---

## 📂 Estructura del proyecto

```text
Proyecto_gestion_biblioteca/
│
├── app/                          
│   ├── __init__.py               # Factory de la app (create_app)
│   ├── decorators.py             # Seguridad de rutas
│   ├── email_service.py          # Lógica SMTP para envíos de correo
│   │
│   ├── models/                   # Capa MODELO: Definición de Tablas
│   │   ├── usuarios.py, equipos.py, libros.py, multas.py, prestamos.py...
│   │
│   ├── routes/                   # Capa CONTROLADOR: Lógica de negocio
│   │   ├── auth.py, reportes.py, prestamos_libros.py, multas.py...
│   │
│   ├── templates/                # Capa VISTA: UI (Jinja2)
│   │   ├── dashboard.html, menu.html, y subcarpetas por módulo...
│   │
│   └── static/                   # Recursos estáticos
│
├── config.py                     # Variables de entorno y BD
├── cron_multas.py                # Job de generación de multas automáticas
├── enviar_recordatorios.py       # Job de notificaciones por email
├── init_db.py                    # Script de inicialización de BD
├── run.py                        # Script de arranque
└── requirements.txt              
```

---

## ⚙️ Instalación y Uso

### Requisitos previos
- Python 3.8 o superior.
- PostgreSQL en ejecución local o en contenedor Docker.
- Variables de entorno configuradas (`.env` con credenciales SMTP y `DATABASE_URL`).

### Pasos de instalación

**1. Clonar y Configurar Entorno**
```bash
git clone https://github.com/tu-usuario/Proyecto_gestion_biblioteca.git
cd Proyecto_gestion_biblioteca
python -m venv venv
# Activar (Windows): venv\Scripts\activate
# Activar (Linux/Mac): source venv/bin/activate
```

**2. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**3. Base de Datos PostgreSQL**
Configura tu base de datos e inicializa las tablas:
```bash
python init_db.py
```

**4. Levantar el Servidor**
```bash
python run.py
```
Accede desde tu navegador a `http://localhost:81`.

---

## 👨‍💻 Autor

**Miller Capera**

*Sistema desarrollado para la gestión eficiente, segura e inteligente de recursos en entornos educativos.*
