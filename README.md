# 📚 Sistema de Gestión de Biblioteca y Almacén SENA

> Plataforma web empresarial integral para la administración, control y trazabilidad centralizada de inventarios y préstamos físicos (libros y equipos tecnológicos). Diseñada con arquitectura modular **MVC**, control estricto de accesos basado en roles (**RBAC**), automatizaciones en segundo plano y despliegue contenerizado.

---

## 📋 Descripción General

El **Sistema de Gestión de Biblioteca y Almacén** es una solución web integral orientada a instituciones educativas y formativas. Su objetivo fundamental es erradicar los registros manuales en papel, evitar la pérdida o deterioro no rastreado de bienes institucionales, aplicar topes de préstamo según el rol académico y automatizar tanto la notificación preventiva de vencimientos como la liquidación diaria de multas por mora.

---

## ✨ Módulos y Funcionalidades del Sistema

### 👥 1. Gestión de Usuarios y Control de Acceso (RBAC de 5 Roles)
El sistema cuenta con una matriz de permisos jerárquica que transforma dinámicamente la interfaz gráfica y los accesos del backend:

| Rol | Alcance y Permisos | Límite Máximo de Préstamos |
| :--- | :--- | :---: |
| **Administrador** | Acceso total al sistema, gestión de personal, auditoría, configuración, finanzas y reportes globales. | **Sin límite** |
| **Bibliotecario** | Administración exclusiva del catálogo de libros, préstamos bibliográficos y renovaciones. Sin acceso al almacén de equipos. | **5 préstamos** |
| **Almacenista** | Administración exclusiva del catálogo de equipos tecnológicos, seriales y préstamos de almacén. Sin acceso a biblioteca. | **5 préstamos** |
| **Instructor** | Solicitud de libros y equipos tecnológicos para fines pedagógicos. | **8 préstamos combinados** |
| **Aprendiz** | Solicitud de libros y equipos tecnológicos para formación académica. | **3 préstamos combinados** |

- **Gestión de Estados de Cuenta:** Cuentas en estado `activo`, `inactivo` o `bloqueado` (los usuarios bloqueados o sancionados no pueden solicitar préstamos).
- **Control Visual Dinámico:** El menú lateral (`sidebar`), widgets del dashboard y botones de acción se renderizan en tiempo real según el rol autenticado.

---

### 🛡️ 2. Seguridad, Autenticación y Mailing
- **Verificación de Cuenta por Correo (SMTP):** Al registrarse, los aprendices e instructores reciben un enlace con token criptográfico temporal; la cuenta permanece inactiva hasta su confirmación por correo. (El personal administrativo está exento para agilizar operaciones).
- **Recuperación Segura de Contraseña:** Flujo de autoservicio *"¿Olvidaste tu contraseña?"* con generación de tokens criptográficos de un solo uso (`itsdangerous`) y expiración programada.
- **Criptografía de Contraseñas:** Hashing robusto con algoritmo `Bcrypt`.
- **Protección de Rutas en Backend:** Decoradores de seguridad personalizados (`@admin_required`, `@gestion_libros_required`, `@gestion_equipos_required`).
- **Control de Peticiones:** Integración con `Flask-Limiter` para mitigar ataques de fuerza bruta y abusos de API.

---

### 📖 3. Inventario de Biblioteca (Libros)
- **Catalogación Detallada:** Registro de título, autor, editorial, año de publicación, código ISBN, género/categoría y ubicación física en estantería.
- **Control de Existencias:** Gestión de ejemplares totales y cálculo dinámico de ejemplares disponibles en tiempo real.
- **Búsqueda y Filtros:** Búsqueda rápida por título, autor, ISBN o categoría temática.

---

### 💻 4. Inventario de Almacén (Equipos Tecnológicos)
- **Trazabilidad por Serial y Placa:** Control unitario de portátiles, proyectores, cables, adaptadores y kits especializados mediante número de serie, placa de inventario institucional, marca y modelo.
- **Categorización Técnica:** Clasificación por tipo de hardware y especificaciones de componentes.

---

### 🔍 5. Auditoría y Registro de Excepciones de Estado
- **Estados Operativos:** Los recursos (libros y equipos) pueden transicionar entre estados: `Disponible`, `Prestado`, `Mantenimiento`, `Daño`, `Pérdida`, `En Reparación` y `Dado de Baja`.
- **Trazabilidad Inmutable:** Cada cambio manual de estado genera un registro histórico que almacena el usuario responsable, fecha/hora exacta, estado anterior, nuevo estado y motivo de la novedad.

---

### 🔄 6. Ciclo de Vida Transaccional de Préstamos
- **Flujo Operativo Completo:** `Solicitud Pendiente` ➔ `Aprobada / Rechazada` ➔ `En Préstamo Activo` ➔ `Devuelto / Cerrado`.
- **Validaciones Automáticas al Solicitar:**
  1. Disponibilidad real del recurso en inventario.
  2. Verificación del tope de préstamos simultáneos según el rol del usuario.
  3. Comprobación de que el solicitante no tenga multas pendientes o la cuenta bloqueada.
- **Renovación de Libros:** Los usuarios pueden solicitar prórrogas de fecha límite en préstamos de libros siempre que el ejemplar no tenga reservas en cola.
- **Recepción e Inspección:** Al devolver el bien, el encargado evalúa su estado físico y funcionalidad antes de liberar el inventario.

---

### 💰 7. Módulo Financiero de Multas
- **Cálculo Automático de Mora:** Generación de cargos diarios por cada día de retraso posterior a la fecha pactada de entrega.
- **Estados de Multa:** `Pendiente`, `Pagada` y `Condonada`.
- **Inhabilitación Automática:** Los usuarios con saldo deudor quedan inhabilitados automáticamente para realizar nuevas solicitudes.
- **Gestión Administrativa:** Registro de comprobantes de pago o condonaciones con justificación debidamente auditada.

---

### 🤖 8. Tareas Automatizadas en Segundo Plano (Cron Jobs)
El sistema incluye scripts desacoplados para ejecución desatendida en el servidor:
- **`enviar_recordatorios.py`:** Escanea diariamente la base de datos y envía correos electrónicos preventivos cuando un préstamo está a menos de 24 horas de expirar o cuando entra en estado vencido.
- **`cron_multas.py`:** Procesa todos los préstamos vencidos y liquida los recargos diarios correspondientes de forma automática.

---

### 📊 9. Dashboard Analítico y Generación de Reportes
- **Dashboard en Tiempo Real:** Visualización instantánea de métricas clave (Total inventario, préstamos activos hoy, solicitudes por aprobar, equipos en taller y valor total de multas por recaudar).
- **Centro de Reportes con Filtros:** Filtros por rango de fechas, estado, categoría y rol.
- **Exportación Dual de Alta Fidelidad:**
  - 📊 **Excel (.xlsx):** Generado con `OpenPyXL` para auditorías contables y procesamiento masivo de datos.
  - 📄 **PDF (.pdf):** Generado con `ReportLab` con diseño corporativo institucional, encabezados y formato listo para impresión y firmas.

---

## 🛠️ Tecnologías y Herramientas Utilizadas

| Categoría | Tecnología | Versión | Propósito en el Proyecto |
| :--- | :--- | :---: | :--- |
| **Lenguaje Backend** | **Python** | 3.10+ | Lógica de negocio y servicios |
| **Framework Web** | **Flask** | 3.1.0 | Arquitectura web y enrutamiento modular (Blueprints) |
| **Base de Datos** | **PostgreSQL** | 16+ | Base de datos relacional transaccional (ACID) |
| **ORM / Migraciones** | **Flask-SQLAlchemy / Flask-Migrate** | 3.1.1 / 4.1.0 | Modelado relacional y versionado de esquemas |
| **Seguridad de Sesiones** | **Flask-Login** | 0.6.3 | Manejo seguro de sesiones y autenticación de usuarios |
| **Criptografía & Tokens** | **Bcrypt / itsdangerous** | 5.0.0 / 2.2.0 | Hash de contraseñas y tokens seguros con expiración |
| **Mailing / Notificaciones** | **Flask-Mail** | 0.10.0 | Envío de correos SMTP (verificaciones y recordatorios) |
| **Rate Limiting** | **Flask-Limiter** | 3.12 | Mitigación de abusos y protección contra fuerza bruta |
| **Frontend & UI** | **Bootstrap / HTML5 / CSS3 / Jinja2** | 5.3 | Interfaz de usuario responsiva, moderna y adaptativa |
| **Reportes Excel** | **OpenPyXL** | 3.1.2 | Generación de hojas de cálculo dinámicas |
| **Reportes PDF** | **ReportLab** | 4.1.0 | Generación de documentos y actas PDF vectorizadas |
| **Servidor WSGI** | **Gunicorn** | 23.0.0 | Servidor HTTP de aplicaciones para producción |
| **Contenedores & Despliegue** | **Docker & Docker Compose** | 3.8 | Empaquetado y despliegue en la nube (Coolify / VPS) |

---

## 📂 Estructura del Proyecto

```text
Proyecto_gestion_biblioteca/
│
├── app/
│   ├── __init__.py               # Factory de la aplicación (create_app) y extensiones
│   ├── decorators.py             # Decoradores de seguridad y autorización RBAC
│   ├── email_service.py          # Servicio de mensajería SMTP y plantillas de correo
│   │
│   ├── models/                   # Capa MODELO (Entidades SQLAlchemy)
│   │   ├── usuarios.py           # Modelo Usuario y estados
│   │   ├── libros.py             # Modelo Libro y categorías
│   │   ├── equipos.py            # Modelo Equipo y trazabilidad de hardware
│   │   ├── prestamos.py          # Modelo de Préstamos de Equipos
│   │   ├── prestamos_libros.py   # Modelo de Préstamos de Libros
│   │   ├── renovaciones.py       # Modelo de Historial de Renovaciones
│   │   └── multas.py             # Modelo de Multas y liquidaciones
│   │
│   ├── routes/                   # Capa CONTROLADOR (Lógica de Negocio y Endpoints)
│   │   ├── auth.py               # Login, registro, verificación SMTP y recuperación
│   │   ├── usuarios.py           # Administración y gestión de personal
│   │   ├── libros.py             # Catálogo y CRUD de biblioteca
│   │   ├── equipos.py            # Catálogo y CRUD de almacén de tecnología
│   │   ├── prestamos.py          # Solicitudes y entregas de equipos
│   │   ├── prestamos_libros.py   # Solicitudes, entregas y renovaciones de libros
│   │   ├── multas.py             # Control de deudas, pagos y condonaciones
│   │   └── reportes.py           # Dashboard, analítica y exportación Excel/PDF
│   │
│   ├── templates/                # Capa VISTA (Plantillas Jinja2 / HTML5)
│   │   ├── base.html             # Layout maestro con assets y scripts
│   │   ├── menu.html             # Barra de navegación dinámica según RBAC
│   │   ├── dashboard.html        # Panel principal con indicadores KPI
│   │   ├── login.html            # Pantalla de acceso
│   │   ├── recuperar_password.html # Solicitud de reseteo de clave
│   │   ├── restablecer_password.html # Formulario de nueva clave
│   │   └── [subcarpetas CRUD]/   # Vistas organizadas por cada módulo
│   │
│   └── static/                   # Hojas de estilo CSS personalizadas, scripts y assets
│
├── cron_multas.py                # Job automatizado de liquidación de multas
├── enviar_recordatorios.py       # Job automatizado de recordatorios por email
├── generar_pdf_plan_exposicion.py# Generador del documento PDF del plan de exposición
├── generar_manuales.py           # Generador de documentación y manuales de usuario
├── init_db.py                    # Script de inicialización y seed de la base de datos
├── run.py                        # Punto de entrada para arranque local
├── Dockerfile                    # Definición de la imagen de producción
├── docker-compose.yml            # Orquestación de servicios y redes
└── requirements.txt              # Manifiesto de dependencias Python
```

---

## 🚀 Instalación y Puesta en Marcha

### Prerrequisitos
- **Python 3.10+**
- **PostgreSQL 16+** (o Docker instalado)

---

### Opción 1: Ejecución Local

**1. Clonar el repositorio y crear el entorno virtual:**
```bash
git clone https://github.com/tu-usuario/Proyecto_gestion_biblioteca.git
cd Proyecto_gestion_biblioteca

# En Windows:
python -m venv venv
venv\Scripts\activate

# En Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

**2. Instalar dependencias:**
```bash
pip install -r requirements.txt
```

**3. Configurar variables de entorno (`.env`):**
Crea un archivo `.env` en la raíz del proyecto con la siguiente estructura:
```env
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_super_segura
DATABASE_URL=postgresql://usuario:password@localhost:5432/biblioteca_db

# Configuración de Correo SMTP (Ejemplo Gmail):
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_correo@gmail.com
MAIL_PASSWORD=tu_contraseña_de_aplicacion
MAIL_DEFAULT_SENDER=tu_correo@gmail.com
```

**4. Inicializar la base de datos:**
```bash
python init_db.py
```

**5. Iniciar la aplicación:**
```bash
python run.py
```
> Accede desde el navegador a: `http://localhost:81` o `http://localhost:5000` (según tu configuración).

---

### Opción 2: Despliegue con Docker y Coolify

El proyecto está listo para ejecutarse en contenedores Docker mediante `docker-compose.yml`:

```bash
# Construir y levantar el contenedor en segundo plano
docker-compose up -d --build
```

- **Servidor WSGI:** Corre con **Gunicorn** en el puerto interno `8000` mapeado al puerto `81`.
- **Persistencia:** Volúmenes configurados para base de datos (`db_data`) y registros de auditoría (`log_data`).
- **Red:** Conexión configurada con redes de proxies inversos y plataformas de orquestación como **Coolify**.

---

## 👨‍💻 Autor

**Miller Capera**

*Sistema desarrollado para la gestión eficiente, segura, automatizada e inteligente de recursos institucionales.*
