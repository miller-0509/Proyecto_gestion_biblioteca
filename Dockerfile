# ── Imagen base ligera ────────────────────────────────────────────
FROM python:3.11-slim

# Evitar prompts interactivos y bufferizar stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Directorio de trabajo ─────────────────────────────────────────
WORKDIR /app

# ── Dependencias del sistema (necesarias para compilar algunas libs) ─
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# ── Instalar dependencias Python ──────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# ── Copiar código fuente ──────────────────────────────────────────
COPY . .

# ── Crear directorios necesarios ──────────────────────────────────
RUN mkdir -p instance logs

# ── Puerto expuesto ───────────────────────────────────────────────
EXPOSE 81

# ── Comando de arranque ──────────────────────────────────────────
# Primero inicializa la BD, luego lanza Gunicorn
CMD ["sh", "-c", "python init_db.py && gunicorn --bind 0.0.0.0:81 --workers 3 --timeout 120 'run:app'"]
