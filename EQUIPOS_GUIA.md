# Sistema de Gestión de Equipos - Guía de Uso

## 🚀 Inicio Rápido

### Credenciales de Administrador (Prueba)
- **Correo**: `admin@biblioteca.com`
- **Contraseña**: `admin123`
- ⚠️ **Importante**: Cambiar contraseña después del primer login

### Scripts Disponibles

#### 1. Inicializar Base de Datos
```bash
python init_db.py
```
- Crea las tablas: `usuarios` y `equipos`
- Se ejecuta automáticamente al instalar

#### 2. Crear Usuario Administrador
```bash
python create_admin.py
```
- Crea usuario admin de prueba
- No sobreescribe si ya existe

#### 3. Agregar Equipos de Prueba
```bash
python create_equipos_prueba.py
```
- Agrega 5 equipos de ejemplo
- Incluye diferentes tipos y estados

---

## 📋 Campos de un Equipo

### Información Identitaria (Obligatoria)
- **ID del Equipo**: Clave primaria (auto-generado)
- **Nombre del Equipo**: Descripción clara (ej: "Portátil Lenovo")
- **Tipo de Equipo**: Categoría (Laptop, Monitor, Teclado, etc.)
- **Número de Serie**: Único y NO duplicable ⚠️ MUY IMPORTANTE

### Especificaciones Técnicas
- **Marca**: Fabricante del equipo
- **Modelo**: Modelo específico
- **Descripción**: Notas adicionales

### Estado e Ubicación
- **Estado**: 
  - ✅ Disponible
  - 🔄 Prestado
  - 🔧 En Mantenimiento
  - ❌ Dañado
- **Ubicación**: Dónde se encuentra (Biblioteca, Almacén, Aula X, etc.)

### Información Financiera
- **Fecha de Compra**: Cuándo se adquirió
- **Valor del Equipo**: Costo de adquisición
- **Proveedor**: Empresa de la que se compró
- **Responsable del Equipo**: Persona o área responsable

### Control de Préstamos
- **Disponible para Préstamo**: Sí/No
- **Tiempo Máximo de Préstamo**: En días (si aplica)

---

## 🎮 Funcionalidades CRUD

### Listar Equipos
- **Ruta**: `/equipos/`
- **Filtros**: 
  - Búsqueda por nombre, serie o marca
  - Filtrar por estado
  - Filtrar por tipo de equipo
- **Paginación**: 10 equipos por página

### Crear Nuevo Equipo
- **Ruta**: `/equipos/nuevo`
- **Campos Obligatorios**: Nombre, Tipo, Número de Serie
- **Validación**: Número de serie único
- **Redirección**: Lista de equipos tras éxito

### Editar Equipo
- **Ruta**: `/equipos/<id>/editar`
- **Funcionalidad**: Modificar cualquier campo
- **Validación**: Número de serie único (a menos que sea el mismo)

### Ver Detalles
- **Ruta**: `/equipos/<id>`
- **Información**: Todos los campos del equipo
- **Acciones**: Editar o Eliminar desde aquí

### Eliminar Equipo
- **Confirmación**: Requiere confirmación
- **Irreversible**: Elimina permanentemente
- **Redirección**: Vuelve a la lista

---

## 🔐 Control de Acceso

### Permisos
- ✅ Solo **administradores** pueden:
  - Listar equipos
  - Crear equipos
  - Editar equipos
  - Eliminar equipos
  - Ver detalles

- ❌ Usuarios normales:
  - No tienen acceso a gestión de equipos
  - (Préstamos estarán disponibles próximamente)

### Decorador de Protección
```python
@admin_required  # Verifica es_admin = True
def lista_equipos():
    ...
```

---

## 📊 Ejemplos de Uso

### Registrar una Laptop
```
Nombre: Portátil HP Pavilion
Tipo: Laptop
Marca: HP
Modelo: Pavilion 15
Serie: HP-2024-PAV-001  ← ÚNICO
Ubicación: Sala de Cómputo
Valor: $800
Tiempo máximo de préstamo: 7 días
```

### Registrar un Proyector (No Transferible)
```
Nombre: Proyector Epson EB-2250U
Tipo: Proyector
Marca: Epson
Modelo: EB-2250U
Serie: EP-2024-PROJ-001
Ubicación: Aula Magna
Valor: $2,800
Disponible para préstamo: NO
```

---

## 🔍 Búsqueda y Filtros

### Ejemplos de Búsqueda
- **Por nombre**: "Portátil" → todos los portátiles
- **Por serie**: "LP001" → equipo específico
- **Por marca**: "Dell" → todos los Dell

### Combinación de Filtros
- Estado: "Disponible" + Tipo: "Laptop"
- Búsqueda: "Lenovo" + Estado: "Mantenimiento"

---

## 📱 API (Para Préstamos Futuros)

### Endpoint Disponible
```
GET /equipos/api/disponibles
```
- Retorna JSON de equipos disponibles
- Filtrados por: estado='disponible' y disponible_prestamo=True
- Usado por el módulo de préstamos (próximamente)

---

## ⚙️ Estructura de Base de Datos

### Tabla: equipos
```sql
CREATE TABLE equipos (
    id_equipo INTEGER PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    tipo_equipo VARCHAR(50) NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100) UNIQUE NOT NULL,
    estado ENUM('disponible','prestado','mantenimiento','dañado'),
    ubicacion VARCHAR(150),
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_compra DATE,
    valor FLOAT,
    proveedor VARCHAR(150),
    responsable VARCHAR(150),
    disponible_prestamo BOOLEAN DEFAULT TRUE,
    tiempo_max_prestamo INTEGER,
    descripcion TEXT
);
```

---

## 🛠️ Próximas Fases

- [ ] Módulo de Préstamos
- [ ] Reportes de inventario
- [ ] Historial de movimientos
- [ ] Auditoría de cambios
- [ ] Notificaciones de mantenimiento
- [ ] Importación desde Excel
- [ ] Código de barras/QR

---

## 📞 Soporte

Para reportar errores o sugerencias, contacta al área de sistemas.

**Última actualización**: 14/04/2026
