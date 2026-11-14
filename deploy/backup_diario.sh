#!/bin/bash
# ==============================================================================
# Script de Copia de Seguridad Diaria Automática — Violett Pilates (FireSeed)
# ==============================================================================
# Este script está diseñado para ejecutarse como una tarea programada (cron) en el VPS.
# Genera un dump completo de PostgreSQL desde el contenedor Docker y aplica retención de 14 días.
#
# Para activarlo en crontab (todos los días a las 03:00 AM):
# 1. Dar permisos de ejecución:
#    chmod +x /home/usuario/proyectos/violett-pilates/deploy/backup_diario.sh
# 2. Abrir crontab:
#    crontab -e
# 3. Agregar la línea:
#    0 3 * * * /home/usuario/proyectos/violett-pilates/deploy/backup_diario.sh >> /var/log/backup_violett.log 2>&1
# ==============================================================================

set -e

BACKUP_DIR="/var/backups/violett"
FECHA=$(date +%Y-%m-%d_%H%M%S)
CONTAINER_PILATES="violettpilates-db_pilates-1"
DB_USER="violett_user"
DB_NAME="violett_pilates"
RETENTION_DAYS=14

# 1. Crear directorio de backups si no existe con permisos seguros
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] INICIANDO COPIA DE SEGURIDAD VIOLETT ==="

# 2. Realizar dump de PostgreSQL
BACKUP_FILE="${BACKUP_DIR}/backup_violett_${FECHA}.sql.gz"

if docker ps --format '{{.Names}}' | grep -q "$CONTAINER_PILATES"; then
    echo "Exportando base de datos desde $CONTAINER_PILATES..."
    docker exec "$CONTAINER_PILATES" pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --clean | gzip > "$BACKUP_FILE"
    chmod 600 "$BACKUP_FILE"
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup generado con éxito: $BACKUP_FILE (Tamaño: $FILE_SIZE)"
else
    echo "⚠️ ERROR: El contenedor de base de datos $CONTAINER_PILATES no está en ejecución."
    exit 1
fi

# 3. Política de retención: Borrar backups anteriores a los días fijados
echo "Aplicando política de retención (mantener últimos $RETENTION_DAYS días)..."
DELETED_COUNT=$(find "$BACKUP_DIR" -type f -name "backup_violett_*.sql.gz" -mtime +$RETENTION_DAYS -print -delete | wc -l)
echo "✓ Archivos obsoletos eliminados: $DELETED_COUNT"

echo "=== COPIA DE SEGURIDAD FINALIZADA CON ÉXITO ==="
