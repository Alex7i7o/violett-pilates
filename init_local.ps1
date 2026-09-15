docker compose up -d --build
Write-Host "Esperando a que las bases de datos inicien..."
Start-Sleep -Seconds 15
Write-Host "Migrando Pilates..."
docker compose exec backend_pilates python manage.py migrate
docker compose exec backend_pilates python manage.py seed_e2e
Write-Host "Migrando Estetica..."
docker compose exec backend_estetica python manage.py migrate
docker compose exec backend_estetica python manage.py seed_e2e
Write-Host "¡Todo listo! Ingresa a http://localhost/"
