#!/bin/bash
echo "== Violett Deploy =="
echo "Building and starting containers..."
docker compose up -d --build

echo "Running migrations..."
docker compose exec -T backend_pilates python manage.py migrate
docker compose exec -T backend_estetica python manage.py migrate

echo "Seeding databases..."
docker compose exec -T backend_pilates python manage.py seed_e2e
docker compose exec -T backend_estetica python manage.py seed_e2e

echo "Deploy complete! Make sure your .env has the right production keys."
