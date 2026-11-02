#!/bin/bash
set -e

echo "=========================================="
echo "   🚀 VIOLETT ENGINE - PRODUCTION DEPLOY  "
echo "=========================================="

# 1. Traer últimos cambios de Git (si es repositorio git)
if [ -d ".git" ]; then
  echo "📥 Descargando últimos cambios desde GitHub..."
  git pull origin main
fi

# 2. Reconstruir y levantar contenedores en background
echo "📦 Construyendo y levantando contenedores con Docker Compose..."
docker compose up -d --build

# 3. Ejecutar migraciones de base de datos para cada instancia
echo "🗄️ Aplicando migraciones de base de datos..."
if docker compose ps | grep -q "backend_pilates"; then
  echo "• Migrando backend_pilates..."
  docker compose exec -T backend_pilates python manage.py migrate --noinput
fi

if docker compose ps | grep -q "backend_estetica"; then
  echo "• Migrando backend_estetica..."
  docker compose exec -T backend_estetica python manage.py migrate --noinput
fi

# 4. Seeding opcional (SOLO si se pasa --seed como argumento, nunca por defecto para no pisar passwords en producción)
if [ "$1" == "--seed" ]; then
  echo "🌱 Ejecutando seed de datos de prueba (--seed detectado)..."
  docker compose exec -T backend_pilates python manage.py seed_e2e || true
  docker compose exec -T backend_estetica python manage.py seed_e2e || true
else
  echo "🔒 Saltando seed de pruebas (producción segura: passwords de usuarios preservadas)."
fi

# 5. Limpieza preventiva de imágenes huérfanas en el VPS para no agotar el disco
echo "🧹 Limpiando imágenes temporales y caché antigua de Docker..."
docker image prune -f

echo "=========================================="
echo "   ✅ DEPLOY COMPLETADO EXITOSAMENTE      "
echo "=========================================="
