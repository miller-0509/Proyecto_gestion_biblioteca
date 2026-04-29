# 📚 Sistema de Gestión de Biblioteca

> Plataforma web para la administración de préstamos de libros y equipos tecnológicos, orientada a instituciones educativas.

---

## 📋 Descripción

El **Sistema de Gestión de Biblioteca** es una aplicación web desarrollada con Flask que permite administrar de forma centralizada el préstamo de libros y equipos tecnológicos dentro de una institución educativa. El sistema diferencia entre roles de usuario (administrador, instructor y aprendiz), garantizando que cada actor tenga acceso únicamente a las funciones que le corresponden. Su objetivo principal es digitalizar y agilizar los procesos de solicitud, aprobación, seguimiento y devolución de recursos físicos.

---

## ✨ Funcionalidades

### 👥 Gestión de Usuarios
- Registro, edición y eliminación de usuarios.
- Roles disponibles: **Administrador**, **Instructor** y **Aprendiz**.
- Control de estado por cuenta: `activo`, `inactivo` o `bloqueado`.
- Contraseñas almacenadas con hash seguro (Werkzeug).

### 📖 Gestión de Libros
- Catálogo de libros con título, autor, género y código único.
- Control de disponibilidad y tiempo máximo de préstamo.
- Estados de libro: `disponible`, `prestado`, `mantenimiento` o `dañado`.

### 🖥️ Gestión de Equipos
- Inventario de equipos tecnológicos (laptops, monitores, teclados, herramientas, etc.).
- Registro detallado: número de serie, marca, modelo, proveedor, responsable y ubicación.
- Control de disponibilidad y tiempo máximo de préstamo por equipo.

### 🔄 Préstamos de Equipos
- Solicitud de préstamo por parte de aprendices e instructores.
- Flujo completo: `pendiente` → `aceptado` / `rechazado` → `devuelto`.
- Registro de fecha de solicitud, aprobación, devolución esperada y devolución real.
- Solo el administrador puede aprobar, rechazar y confirmar devoluciones.
- Validación de disponibilidad en tiempo real para evitar préstamos duplicados.

### 📕 Préstamos de Libros
- Solicitud y gestión independiente del préstamo de libros.
- Mismo flujo de estados que los préstamos de equipos.
- Historial completo de préstamos por libro y por usuario.

### 🛡️ Control de Roles y Seguridad
- Decorador `@admin_required` para proteger rutas sensibles en el backend.
- Protección CSRF en todos los formularios mediante Flask-WTF.
- Acceso a funciones administrativas restringido exclusivamente al rol `administrador`.
- Redirección automática y mensajes de acceso denegado para usuarios no autorizados.

### 🔐 Autenticación
- Inicio y cierre de sesión seguros con Flask-Login.
- Verificación de estado de cuenta en cada inicio de sesión.
- Gestión de sesiones con clave secreta generada dinámicamente.

---

## 🛠️ Tecnologías utilizadas

| Tecnología | Versión | Descripción |
|---|---|---|
| **Python** | 3.x | Lenguaje principal del backend |
| **Flask** | 3.1.0 | Framework web |
| **Flask-SQLAlchemy** | 3.1.1 | ORM para base de datos |
| **Flask-Login** | 0.6.3 | Gestión de sesiones y autenticación |
| **Flask-WTF** | - | Protección CSRF |
| **Werkzeug** | 3.1.3 | Seguridad y utilidades web |
| **SQLite** | - | Base de datos embebida |
| **Jinja2** | - | Motor de plantillas HTML |
| **HTML5 / CSS3** | - | Estructura y estilos del frontend |
| **JavaScript** | - | Interactividad del cliente |

---

## 📂 Estructura del proyecto

```
Proyecto_gestion_biblioteca/
│
├── app/                          # Paquete principal de la aplicación
│   ├── __init__.py               # Factory de la app (create_app)
│   ├── decorators.py             # Decoradores personalizados (admin_required)
│   │
│   ├── models/                   # Modelos de base de datos (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── usuarios.py           # Modelo de Usuario
│   │   ├── equipos.py            # Modelo de Equipo
│   │   ├── libros.py             # Modelo de Libro
│   │   ├── prestamos.py          # Modelo de Préstamo de Equipos
│   │   └── prestamos_libros.py   # Modelo de Préstamo de Libros
│   │
│   ├── routes/                   # Blueprints y rutas de la aplicación
│   │   ├── auth.py               # Login, registro y logout
│   │   ├── usuarios.py           # CRUD de usuarios
│   │   ├── equipos.py            # CRUD de equipos
│   │   ├── libros.py             # CRUD de libros
│   │   ├── prestamos.py          # Gestión de préstamos de equipos
│   │   └── prestamos_libros.py   # Gestión de préstamos de libros
│   │
│   ├── templates/                # Plantillas HTML (Jinja2)
│   │   ├── base.html             # Plantilla base con layout general
│   │   ├── login.html            # Página de inicio de sesión
│   │   ├── dashboard.html        # Panel principal
│   │   ├── menu.html             # Menú de navegación
│   │   ├── equipos/              # Vistas de equipos
│   │   ├── libros/               # Vistas de libros
│   │   ├── prestamos/            # Vistas de préstamos de equipos
│   │   ├── prestamos_libros/     # Vistas de préstamos de libros
│   │   └── usuarios/             # Vistas de usuarios
│   │
│   └── static/                   # Archivos estáticos
│       ├── sena-style.css        # Estilos principales del sistema
│       ├── images/               # Imágenes del sistema
│       └── img/                  # Recursos gráficos adicionales
│
├── instance/                     # Archivos de instancia (BD generada)
│   └── almacendb.sqlite          # Base de datos SQLite
│
├── config.py                     # Configuración de la aplicación
├── run.py                        # Punto de entrada del servidor
├── init_db.py                    # Script de inicialización de BD
├── requirements.txt              # Dependencias del proyecto
└── README.md                     # Documentación del proyecto
```

---

## ⚙️ Instalación y uso

### Requisitos previos

- Python 3.8 o superior instalado.
- `pip` disponible en el sistema.
- (Recomendado) Entorno virtual de Python.

### Pasos de instalación

**1. Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/Proyecto_gestion_biblioteca.git
cd Proyecto_gestion_biblioteca
```

**2. Crear y activar el entorno virtual**

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Linux / macOS
source venv/bin/activate
```

**3. Instalar las dependencias**

```bash
pip install -r requirements.txt
```

**4. Inicializar la base de datos**

```bash
python init_db.py
```

**5. Ejecutar el servidor**

```bash
python run.py
```

**6. Abrir en el navegador**

```
http://localhost:81
```

> **Nota:** El servidor corre por defecto en el puerto `81`. Si el puerto está en uso, puedes modificarlo en `run.py`.

---

## 🖥️ Uso del sistema

### 👤 Usuario (Aprendiz / Instructor)

1. Acceder al sistema mediante la página de inicio de sesión.
2. Desde el **dashboard**, consultar el catálogo de libros y equipos disponibles.
3. Solicitar un préstamo seleccionando el recurso deseado.
4. Hacer seguimiento del estado de su solicitud: `pendiente`, `aceptado` o `rechazado`.
5. Una vez devuelto el recurso, el historial quedará registrado.

### 🔑 Administrador

1. Iniciar sesión con una cuenta de rol `administrador`.
2. Gestionar el catálogo de libros y equipos (agregar, editar, eliminar).
3. Revisar las solicitudes de préstamo pendientes y aprobarlas o rechazarlas.
4. **Confirmar la devolución** de recursos prestados (acción exclusiva del administrador).
5. Administrar cuentas de usuario: registrar nuevos usuarios, cambiar roles y controlar estados de cuenta.
6. Consultar el historial completo de todos los préstamos del sistema.

---

## 🖼️ Capturas de pantalla

> _Las siguientes capturas serán agregadas próximamente._

| Vista | Descripción |
|---|---|
| ![Login](./app/static/images/screenshot-login.png) | Página de inicio de sesión |
| ![Dashboard](./app/static/images/screenshot-dashboard.png) | Panel principal |
| ![Préstamos](./app/static/images/screenshot-prestamos.png) | Gestión de préstamos |
| ![Equipos](./app/static/images/screenshot-equipos.png) | Catálogo de equipos |

---

## 🚀 Mejoras futuras

- [ ] **Sistema de multas**: calcular y registrar multas automáticas por devoluciones tardías.
- [ ] **Notificaciones por correo**: alertas automáticas al aprobar, rechazar o vencer el plazo de un préstamo.
- [ ] **Dashboard con estadísticas**: gráficas de préstamos activos, recursos más solicitados e historial por período.
- [ ] **Exportación de reportes**: generación de informes en PDF o Excel.
- [ ] **Búsqueda y filtros avanzados**: en catálogos de libros, equipos e historial de préstamos.
- [ ] **Mejoras de UI/UX**: diseño responsivo mejorado y soporte para modo oscuro.
- [ ] **API REST**: exposición de endpoints para integración con otros sistemas institucionales.
- [ ] **Autenticación de dos factores (2FA)**: para cuentas de administrador.

---

## 👨‍💻 Autor

**Miller Capera**

---

*Sistema desarrollado para la gestión eficiente de recursos bibliográficos y tecnológicos en entornos educativos.*
