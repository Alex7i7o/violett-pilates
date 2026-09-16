#!/bin/bash
set -e

SERVER_IP="187.77.43.144"

echo "======================================"
echo "🚀 INICIANDO DESPLIEGUE A PRODUCCIÓN"
echo "======================================"

echo "📦 1. Empaquetando código optimizado..."
python zip_prod.py

echo "☁️ 2. Subiendo al VPS..."
scp ViolettPilates-Deploy.zip root@$SERVER_IP:/root/

echo "🔄 3. Desplegando en servidor..."
ssh root@$SERVER_IP << 'ENDSSH'
  set -e
  echo "--- Deteniendo contenedores actuales..."
  cd /root/ViolettPilates && docker compose down --remove-orphans || true

  echo "--- Limpiando código fuente viejo para evitar archivos huérfanos..."
  rm -rf /root/ViolettPilates/*

  echo "--- Descomprimiendo código fuente nuevo..."
  unzip -o /root/ViolettPilates-Deploy.zip -d /root/ViolettPilates
  cd /root/ViolettPilates

  echo "--- Construyendo frontend Pilates (separado, sin caché)..."
  docker compose build --no-cache frontend_pilates

  echo "--- Construyendo frontend Estética (separado, sin caché)..."
  docker compose build --no-cache frontend_estetica

  echo "--- Construyendo backend y proxy..."
  docker compose build backend_pilates backend_estetica nginx_proxy

  echo "--- Iniciando todos los servicios..."
  docker compose up -d

  echo "--- Esperando que los backends arranquen (10s)..."
  sleep 10

  echo "--- Aplicando migraciones Pilates..."
  docker compose exec backend_pilates python manage.py migrate --noinput

  echo "--- Aplicando migraciones Estética..."
  docker compose exec backend_estetica python manage.py migrate --noinput

  echo "--- ¡Despliegue completado!"
ENDSSH

echo "======================================"
echo "✅ ¡DESPLIEGUE COMPLETADO CON ÉXITO!"
echo "======================================"
