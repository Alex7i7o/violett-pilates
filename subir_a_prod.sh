#!/bin/bash
set -e
set -o pipefail

SERVER_IP="187.77.43.144"

# Capturador de errores local: si cualquier paso falla, se frena y muestra el cartel de error (NUNCA el de éxito)
error_handler() {
  local exit_code=$?
  local line_no=$1
  echo ""
  echo "=================================================="
  echo "❌ ERROR CRÍTICO: EL DESPLIEGUE NO PUDO COMPLETARSE"
  echo "Fallo en la línea: $line_no (Código de salida: $exit_code)"
  echo "Revisá los logs arriba para ver el error exacto."
  echo "=================================================="
  exit $exit_code
}
trap 'error_handler $LINENO' ERR

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
  set -o pipefail

  # Capturador de errores remoto: si falla cualquier compilación o migración en el VPS
  remote_error_handler() {
    local exit_code=$?
    echo ""
    echo "=================================================="
    echo "❌ ERROR EN EL VPS: Falló una tarea en el servidor"
    echo "=================================================="
    exit $exit_code
  }
  trap 'remote_error_handler' ERR

  echo "--- Limpiando código fuente viejo para evitar archivos huérfanos..."
  rm -rf /root/ViolettPilates/*

  echo "--- Descomprimiendo código fuente nuevo..."
  unzip -q -o /root/ViolettPilates-Deploy.zip -d /root/ViolettPilates
  cd /root/ViolettPilates

  echo "--- Construyendo frontend Pilates (separado, sin caché)..."
  docker compose build --no-cache frontend_pilates

  echo "--- Construyendo frontend Estética (separado, sin caché)..."
  docker compose build --no-cache frontend_estetica

  echo "--- Construyendo backend y proxy..."
  docker compose build --no-cache backend_pilates backend_estetica nginx_proxy

  echo "--- Iniciando todos los servicios..."
  docker compose up -d

  echo "--- Esperando que los backends arranquen (10s)..."
  sleep 10

  echo "--- Aplicando migraciones Pilates..."
  docker compose exec -T backend_pilates python manage.py migrate --noinput

  echo "--- Aplicando migraciones Estética..."
  docker compose exec -T backend_estetica python manage.py migrate --noinput

  echo "--- Reiniciando backend y proxy Nginx para refrescar resolución DNS e IPs..."
  docker compose restart backend_pilates backend_estetica nginx_proxy
  sleep 4

  echo "--- Verificando estado activo de los contenedores..."
  if ! docker compose ps backend_pilates | grep -q "Up"; then
    echo "❌ Error: El contenedor backend_pilates no quedó en estado 'Up'."
    exit 1
  fi
  if ! docker compose ps nginx_proxy | grep -q "Up"; then
    echo "❌ Error: El contenedor nginx_proxy no quedó en estado 'Up'."
    exit 1
  fi

  echo "--- ¡Servicios y contenedores activos correctamente en el servidor!"
ENDSSH

echo ""
echo "======================================"
echo "✅ ¡DESPLIEGUE COMPLETADO CON ÉXITO!"
echo "Todos los servicios están en línea."
echo "======================================"
