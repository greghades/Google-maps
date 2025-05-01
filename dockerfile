# Usa una imagen base de Python basada en Debian para compatibilidad con Playwright
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para Playwright
RUN apt-get update && apt-get install -y \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    # Dependencias adicionales recomendadas para Playwright
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libdrm2 \
    libegl1 \
    libgl1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos para instalar dependencias de Python
COPY requirements.txt .

# Instala las dependencias de Python, incluyendo Playwright
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

# Copia el código de la aplicación
COPY . .

# Expone el puerto 8000 para el servidor FastAPI
EXPOSE 8001

# Comando para correr la aplicación con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]