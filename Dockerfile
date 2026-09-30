FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar librerías C necesarias para que GeoDjango y psycopg reconozcan PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  binutils \
  gdal-bin \
  libgdal-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
