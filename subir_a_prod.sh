#!/bin/bash
SERVER_IP="187.77.43.144"

echo "======================================"
echo "🚀 INICIANDO DESPLIEGUE A PRODUCCIÓN"
echo "======================================"

echo "📦 1. Empaquetando código optimizado..."
python zip_prod.py

echo "☁️ 2. Subiendo al VPS..."
scp ViolettPilates-Deploy.zip root@$SERVER_IP:/root/

echo "🔄 3. Actualizando servidor e instalando cambios..."
ssh root@$SERVER_IP "cd /root/ViolettPilates && unzip -o /root/ViolettPilates-Deploy.zip -d /root/ViolettPilates && docker compose up -d --build && docker compose exec backend_pilates python manage.py makemigrations && docker compose exec backend_pilates python manage.py migrate && docker compose exec backend_estetica python manage.py migrate && docker compose exec backend_pilates python manage.py seed_e2e && docker compose exec backend_estetica python manage.py seed_e2e && docker compose restart nginx_proxy"

echo "======================================"
echo "✅ ¡DESPLIEGUE COMPLETADO CON ÉXITO!"
echo "======================================"
