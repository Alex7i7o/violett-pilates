#!/bin/bash
echo "== Violett Pilates Deploy =="
echo "Building and starting containers..."
docker compose up -d --build

echo "Running migrations..."
docker compose exec -T backend_pilates python manage.py migrate
docker compose exec -T backend_estetica python manage.py migrate

echo "Deploy complete! Make sure your .env has the right production keys."