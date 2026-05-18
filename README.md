# 📚 Sistema de Gestión de Biblioteca y Almacén SENA

> Plataforma web para la administración profesional y centralizada de préstamos de libros y equipos tecnológicos, orientada a instituciones educativas, con una arquitectura sólida de control de accesos (RBAC).

---

## 📋 Descripción

El **Sistema de Gestión de Biblioteca y Almacén** es una aplicación web empresarial desarrollada con Flask y PostgreSQL que permite administrar de forma centralizada el inventario y los préstamos físicos de una institución. 

El sistema cuenta con un control de accesos robusto basado en 5 roles jerárquicos (Administrador, Bibliotecario, Almacenista, Instructor y Aprendiz), garantizando la seguridad en el backend y una interfaz dinámica en el frontend que se adapta a los privilegios de cada usuario. Su objetivo principal es digitalizar, asegurar y agilizar todos los procesos de solicitud, seguimiento y auditoría de recursos.

---

## ✨ Funcionalidades Principales

### 👥 Gestión Avanzada de Usuarios y Roles (RBAC)
- Jerarquía de 5 roles con permisos y límites estrictos:
  - **Administrador**: Control total sobre todos los módulos y gestión de personal. Sin límites de préstamo.
  - **Bibliotecario**: Gestión exclusiva de libros (aprobar, rechazar, devolver, cambiar estado). Límite de 5 préstamos. No ve equipos.
  - **Almacenista**: Gestión exclusiva de equipos (aprobar, rechazar, devolver, cambiar estado). Límite de 5 préstamos. No ve libros.
  - **Instructor**: Nivel usuario. Límite de 5 préstamos combinados.
  - **Aprendiz**: Nivel usuario. Límite de 3 préstamos combinados.
- Control dinámico de UI: El menú lateral, dashboard y botones de acción se ocultan/muestran según el rol de la sesión.
- Control de estado por cuenta: `activo`, `inactivo` o `bloqueado`.

### 🛡️ Seguridad y Autenticación
- **Verificación de Correo (Mailing)**: Los aprendices e instructores deben verificar su correo (envío de token real usando Flask-Mail y suplantación SMTP) para iniciar sesión. El personal administrativo (Admin, Bibliotecario, Almacenista) está exento de este paso para agilizar operaciones.
- **Recuperación de Contraseña**: Flujo profesional "¿Olvidaste tu contraseña?" con envío de correos, enlaces seguros generados criptográficamente (`itsdangerous`) y expiración por tiempo y uso.
- Decoradores de backend (`@gestion_libros_required`, `@gestion_equipos_required`, `@admin_required`) para proteger rutas críticas a nivel del servidor.

### 📖 Gestión de Libros y 🖥️ Gestión de Equipos
- Inventarios detallados (títulos, seriales, marcas, códigos únicos, responsables, ubicaciones).
- **Gestión de Estados Manual y Excepciones**: El personal puede forzar cambios de estado por situaciones reales (`daño`, `mantenimiento`, `pérdida`, `baja`, `reparación`, `bloqueo temporal`, `recuperación`).
- Registro histórico inmutable de todos los cambios de estado (auditoría).

### 🔄 Sistema de Préstamos Inteligente
- Límite estricto de **préstamos combinados activos** (suma de libros + equipos prestados/pendientes) según el rol.
- Flujo completo: `pendiente` → `aceptado` / `rechazado` → `devuelto`.
- El sistema detecta automáticamente disponibilidades y previene "carreras de condiciones" o duplicados.
- Historial transparente para los usuarios donde solo ven sus propios préstamos.

---

## 🛠️ Tecnologías utilizadas

| Tecnología | Versión | Descripción |
|---|---|---|
| **Python** | 3.x | Lenguaje principal del backend |
| **Flask** | 3.1.0 | Framework web |
| **PostgreSQL** | 16+ | Base de datos relacional robusta |
| **Flask-SQLAlchemy** | 3.1.1 | ORM avanzado para consultas |
| **Flask-Login** | 0.6.3 | Gestión de sesiones seguras |
| **Flask-Mail** | - | Envío de correos (Verificaciones y Recuperaciones) |
| **itsdangerous** | - | Tokens temporales criptográficos |
| **Bootstrap / CSS Vanilla** | 5.3 | Interfaz dinámica y responsiva con estilos corporativos (SENA) |

---

## 📂 Estructura del proyecto

```
Proyecto_gestion_biblioteca/
│
├── app/                          
│   ├── __init__.py               # Factory de la app (create_app)
│   ├── decorators.py             # Seguridad de rutas (@gestion_libros_required...)
│   ├── email_service.py          # Lógica SMTP para envíos de correo
│   │
│   ├── models/                   # Definición de Tablas PostgreSQL
│   │   ├── usuarios.py           # Usuario y conteo lógico de préstamos
│   │   ├── equipos.py            # Equipos e Historial de Estados
│   │   ├── libros.py             # Libros e Historial de Estados
│   │   └── ...
│   │
│   ├── routes/                   # Controladores (MVC)
│   │   ├── auth.py               # Login, Recuperación Password, Verificación
│   │   └── ...
│   │
│   ├── templates/                # UI (Jinja2 + Bootstrap)
│   │   ├── dashboard.html        # Dinámico por Roles
│   │   ├── menu.html             # Navbar y Sidebar con RBAC
│   │   └── ...
│   │
│   └── static/                   
│       └── sena-style.css        # Estilos visuales
│
├── config.py                     # Variables de entorno y DB URI
├── update_enum.py                # Script de migración de tipos de Postgres
├── init_db.py                    # Script de inicialización
├── requirements.txt              # Dependencias
└── README.md                     
```

---

## ⚙️ Instalación y uso

### Requisitos previos

- Python 3.8 o superior.
- PostgreSQL en ejecución local o en contenedor Docker.
- Variables de entorno configuradas (Credenciales SMTP para correo, `DATABASE_URL` para PostgreSQL).

### Pasos de instalación

**1. Clonar el repositorio y Entorno Virtual**

```bash
git clone https://github.com/tu-usuario/Proyecto_gestion_biblioteca.git
cd Proyecto_gestion_biblioteca
python -m venv venv
# Activar: venv\Scripts\activate (Windows) o source venv/bin/activate (Linux/Mac)
```

**2. Instalar dependencias**

```bash
pip install -r requirements.txt
```

**3. Configurar Base de Datos PostgreSQL**

Crea una base de datos en PostgreSQL e inicializa las tablas:

```bash
python init_db.py
```
*(Si agregas roles nuevos en el futuro, puedes usar `python update_enum.py` para actualizar la estructura de la base de datos).*

**4. Ejecutar el servidor**

```bash
python run.py
```
Accede mediante el navegador a `http://localhost:81`.

---

## 🚀 Próximos Pasos (Pendientes)

- [x] **Roles y Permisos Múltiples**: Bibliotecarios y Almacenistas.
- [x] **Recuperación de Contraseña Avanzada**.
- [x] **Gestión Manual de Excepciones y Estados Físicos**.
- [x] **Integración Real con Mailing**.
- [x] **Migración a PostgreSQL**.
- [ ] **Sistema de Notificaciones Automáticas**: Alertas de vencimiento de préstamos.
- [ ] **Panel de Estadísticas (Reportes)**: Gráficas de préstamos mensuales, descargas a PDF/Excel reservadas para administración.
- [ ] **Despliegue (Coolify/Docker)**: Configuración en entorno de producción.

---

## 👨‍💻 Autor

**Miller Capera**

*Sistema desarrollado para la gestión eficiente, segura e inteligente de recursos en entornos educativos.*
