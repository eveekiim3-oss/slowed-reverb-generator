# syntax = docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

# Instalar FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Crear carpetas necesarias
RUN mkdir -p uploads processed

# Exponer puerto
EXPOSE 8080

# Comando para iniciar la aplicación
CMD ["python", "app.py"]
