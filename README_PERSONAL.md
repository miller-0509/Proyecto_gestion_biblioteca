# 📘 Resumen del Proyecto - Biblioteca SENA

## 🎯 Visión General
Este proyecto es un **Sistema de Gestión de Biblioteca y Almacén** desarrollado con **Flask** y **PostgreSQL**. Permite administrar usuarios, libros y equipos tecnológicos con un control de accesos basado en **RBAC (5 roles)**, incluyendo funcionalidades de verificación de correo, recuperación de contraseñas y gestión de préstamos.

---

## 📂 Estructura del Repositorio
```
Proyecto_gestion_biblioteca/
│
├─ app/                     # Código principal de la aplicación Flask
│   ├─ __init__.py          # Factory `create_app`
│   ├─ decorators.py        # Decoradores de seguridad
│   ├─ email_service.py     # Lógica de envío de correos
│   ├─ models/              # Definiciones ORM (SQLAlchemy)
│   │   ├─ usuarios.py
│   │   ├─ libros.py
│   │   ├─ equipos.py
│   │   └─ ...
│   ├─ routes/              # Controladores (auth, gestión, etc.)
│   │   ├─ auth.py
│   │   └─ ...
│   ├─ templates/           # Plantillas Jinja2 + Bootstrap
│   └─ static/               # Recursos estáticos (CSS, imágenes)
│
├─ config.py                # Variables de entorno y configuración DB
├─ init_db.py               # Script de inicialización de base de datos
├─ update_enum.py           # Migración de enum en PostgreSQL
├─ requirements.txt         # Dependencias de Python
├─ run.py                   # Punto de entrada del servidor
├─ Dockerfile               # Imagen Docker para despliegue
├─ docker‑compose.yml       # Orquestación con Docker‑Compose
├─ .env (ejemplo)          # Variables de entorno (SMTP, DB, etc.)
└─ README.md                # Documentación pública (este archivo)
```

---

## 🛠️ Tecnologías Principales
| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.x | Lenguaje base del backend |
| Flask | 3.1.0 | Framework web |
| PostgreSQL | 16+ | Base de datos relacional |
| Flask‑SQLAlchemy | 3.1.1 | ORM |
| Flask‑Login | 0.6.3 | Gestión de sesiones |
| Flask‑Mail | – | Envío de correos (verificación, recuperación) |
| itsdangerous | – | Tokens seguros |
| Bootstrap | 5.3 | UI responsiva |

---

## 🚀 Cómo levantar el proyecto (Windows)
1. **Clonar el repositorio** (si aún no lo hiciste) y crear un entorno virtual:
```bash
git clone https://github.com/tu-usuario/Proyecto_gestion_biblioteca.git
cd Proyecto_gestion_biblioteca
python -m venv venv
venv\Scripts\activate   # PowerShell: .\venv\Scripts\Activate.ps1
```
2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```
3. **Configurar variables de entorno**:
   - Copiar `.env.example` a `.env` y añadir `DATABASE_URL`, credenciales SMTP, etc.
4. **Inicializar la base de datos**:
```bash
python init_db.py
```
5. **Ejecutar la aplicación**:
```bash
python run.py
```
   - Acceder a `http://localhost:81` en el navegador.

---

## 📜 Scripts útiles
| Script | Descripción |
|---|---|
| `init_db.py` | Crea todas las tablas en PostgreSQL |
| `update_enum.py` | Actualiza enumeraciones (roles, estados) en la DB |
| `run.py` | Arranca el servidor Flask |
| `docker-compose.yml` + `Dockerfile` | Opciones para levantar la app en contenedores Docker |

---

## ✅ Estado actual y Próximos pasos
- **Funcionalidades completadas**: RBAC, verificación de email, recuperación de contraseña, gestión de libros/equipos, control de préstamos.
- **Pendientes**:
  - Sistema de notificaciones automáticas (vencimientos)
  - Panel de estadísticas y reportes
  - Despliegue en producción (Coolify/Docker)

---

## 👤 Autor
**Miller Capera** – Desarrollo orientado a la gestión eficiente y segura de recursos en entornos educativos.

---

*Este README ha sido generado automáticamente para ofrecerte una visión rápida y estructurada del proyecto tal como está en este momento.*
