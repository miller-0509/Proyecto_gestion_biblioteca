# 🚀 INICIO RÁPIDO - Gestión de Equipos

## En 3 Pasos

### 1️⃣ Ejecutar la Aplicación
```bash
cd c:\Users\caper\Documents\Proyecto_gestion_biblioteca
python run.py
```
Acceder a: **http://localhost:5000**

---

### 2️⃣ Iniciar Sesión como Admin
```
Correo: admin@biblioteca.com
Contraseña: admin123
```

---

### 3️⃣ Ir a Equipos
En el menú superior: **"Equipos"** → **"Listado"**

O acceder directamente: **http://localhost:5000/equipos/**

---

## 🎯 Operaciones Principales

### 📋 Ver Lista de Equipos
- Se muestra tabla con todos los equipos
- Incluye: Nombre, Tipo, Serie, Estado, Ubicación, Valor

### ➕ Crear Nuevo Equipo
```
Botón: "Nuevo Equipo" (parte superior derecha)
O: http://localhost:5000/equipos/nuevo
```

**Campos obligatorios:**
- Nombre (ej: Portátil HP)
- Tipo (ej: Laptop)
- Número de Serie (ej: HP-2024-001)

**Campos opcionales:**
- Marca, Modelo
- Ubicación
- Fecha de compra, Valor
- Proveedor, Responsable
- Disponible para préstamo, Tiempo máximo
- Descripción

### ✏️ Editar Equipo
- En lista: Click en icono lápiz
- En detalles: Botón "Editar"

### 👁️ Ver Detalles
- En lista: Click en icono ojo
- O click en nombre del equipo

### 🗑️ Eliminar Equipo
- En lista: Click en icono basura
- En detalles: Botón "Eliminar"
- ⚠️ Requiere confirmación

---

## 🔍 Filtros y Búsqueda

**Búsqueda por:**
- Nombre del equipo
- Número de serie
- Marca

**Filtros:**
- Estado (Disponible, Prestado, Mantenimiento, Dañado)
- Tipo de equipo (Laptop, Monitor, etc.)

**Ejemplo combinado:**
- Buscar: "Lenovo"
- Estado: "Disponible"
- Resultado: Todos los Lenovo disponibles

---

## 💡 Ejemplos Prácticos

### Registrar una Laptop para Préstamo
```
Nombre: Portátil Dell Inspiron 15
Tipo: Laptop
Marca: Dell
Modelo: Inspiron 15
Serie: DELL-2024-INS-001
Ubicación: Biblioteca
Valor: $600
Proveedor: Dell Store
Disponible Préstamo: ✓ SÍ
Tiempo máximo: 7 días
```

### Registrar un Proyector Fijo (No Transferible)
```
Nombre: Proyector Sala Magna
Tipo: Proyector
Marca: Epson
Modelo: EB-2250U
Serie: EP-2024-SALA-MAG-001
Ubicación: Aula Magna
Valor: $2,800
Responsable: Mantenimiento
Disponible Préstamo: ✗ NO
```

### Marcar como En Mantenimiento
```
1. Ir a Equipos → Listado
2. Click en el equipo
3. Click "Editar"
4. Estado: "En Mantenimiento"
5. Guardar cambios
```

---

## ⚠️ Validaciones Importantes

❌ **NO PERMITIDO:**
- Dos equipos con el mismo número de serie
- Crear sin nombre
- Crear sin tipo
- Crear sin número de serie

✅ **SIEMPRE:**
- Verificar número de serie único
- Especificar tipo de equipo
- Llenar nombre descriptivo
- Indicar estado actual

---

## 🎨 Indicadores Visuales

| Color | Significado | Estado |
|-------|-------------|--------|
| 🟢 Verde | Disponible | Se puede prestar |
| 🟡 Amarillo | Prestado | En manos de alguien |
| ⚫ Gris | Mantenimiento | En reparación |
| 🔴 Rojo | Dañado | No funciona |

---

## 🔐 Solo para Administradores

- Usuarios normales **NO ven** el menú "Equipos"
- Solo admin puede crear/editar/eliminar
- Acceso bloqueado si no es admin
- Se redirige automáticamente al dashboard

---

## 🆘 Solucionar Problemas

### "No veo el menú Equipos"
→ Verificar que estés logueado como **admin@biblioteca.com**

### "Error: Número de serie ya existe"
→ Usar un número diferente (cada equipo debe ser único)

### "No puedo editar/eliminar"
→ Solo admin puede hacer cambios

### "Página no encontrada"
→ Asegúrate de estar usando `admin@biblioteca.com`

---

## 📞 Datos de Prueba Preconfigurados

**5 Equipos de ejemplo ya cargados:**
1. Portátil Lenovo (Disponible)
2. Monitor Dell (Disponible)
3. Teclado Corsair (Disponible)
4. Proyector Epson (Mantenimiento)
5. Tablet Samsung (Disponible)

Puedes usarlos para familiarizarte con el sistema.

---

## ✨ Próximas Características

- 📦 Módulo de Préstamos (próximamente)
- 📊 Reportes de inventario
- 📈 Gráficos de estado
- 🔔 Alertas de mantenimiento
- 📱 Códigos QR/Barras

---

## 📧 Necesito Ayuda

**Contacta al área de Sistemas para:**
- Cambiar contraseña de admin
- Crear otros usuarios admin
- Reportar errores
- Sugerencias

---

**¡Bienvenido al Sistema de Gestión de Equipos!** 🚀

Hoy: 14/04/2026
