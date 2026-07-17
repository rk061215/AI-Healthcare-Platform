# Backup & Recovery Strategy

**v1.0.0** — No paid services, all free-tier compatible.

---

## Overview

This strategy covers four data categories on Render free tier / Docker:

1. **PostgreSQL** — Database (users, appointments, chat history, medicine adherence)
2. **ChromaDB** — Vector embeddings and metadata
3. **Uploaded Files** — Documents, reports, images
4. **Configuration** — Environment variables and secrets

---

## 1. PostgreSQL Backup

### Automated (via pg_dump cron)

```bash
#!/bin/bash
# backup-postgres.sh — run daily via cron or Render Cron Job

BACKUP_DIR="/app/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR"

# Full database dump (compressed)
pg_dump "$DATABASE_URL" \
  --format=custom \
  --compress=9 \
  --file="$BACKUP_DIR/healthcare_$TIMESTAMP.dump"

# Delete backups older than retention
find "$BACKUP_DIR" -name "*.dump" -mtime +$RETENTION_DAYS -delete

echo "Backup complete: $BACKUP_DIR/healthcare_$TIMESTAMP.dump"
```

**Schedule:** Daily at 3 AM (configurable via `BACKUP_SCHEDULE_CRON`)

### Manual Backup
```bash
# Docker
docker exec healthcare-postgres pg_dump -U healthcare_user -d healthcare_agent \
  --format=custom --compress=9 > backup_$(date +%Y%m%d).dump

# Render — use PSQL from local machine
pg_dump "$RENDER_DATABASE_URL" --format=custom --compress=9 > render_backup.dump
```

### Restore
```bash
# Docker
docker exec -i healthcare-postgres pg_restore -U healthcare_user -d healthcare_agent \
  --clean --if-exists < backup.dump

# Render
pg_restore --clean --if-exists -d "$RENDER_DATABASE_URL" render_backup.dump
```

### Partial Restore (single table)
```bash
pg_restore --table=users --data-only -d "$DATABASE_URL" backup.dump
```

---

## 2. ChromaDB Backup

ChromaDB stores data on disk at `/chroma/chroma`. Backup the directory.

### Manual Backup
```bash
# Docker
docker exec healthcare-chroma tar -czf /tmp/chroma_backup.tar.gz -C /chroma chroma
docker cp healthcare-chroma:/tmp/chroma_backup.tar.gz ./chroma_backup_$(date +%Y%m%d).tar.gz

# Render — requires persistent disk
tar -czf /app/backups/chroma/chroma_$(date +%Y%m%d).tar.gz -C /chroma chroma
```

### Automated
```bash
#!/bin/bash
# backup-chroma.sh

BACKUP_DIR="/app/backups/chroma"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_DIR/chroma_$TIMESTAMP.tar.gz" -C /chroma chroma

# Keep 7 daily + 4 weekly
find "$BACKUP_DIR" -name "chroma_*.tar.gz" -mtime +30 -delete
```

### Restore
```bash
# Docker
docker cp chroma_backup.tar.gz healthcare-chroma:/tmp/
docker exec healthcare-chroma tar -xzf /tmp/chroma_backup.tar.gz -C /chroma

# After restore, restart ChromaDB
docker restart healthcare-chroma
```

### ⚠️ Render Free Limitation

ChromaDB **cannot** run reliably on Render free tier:
- Free web services sleep after 15 minutes of inactivity
- ChromaDB data on ephemeral disk is lost on restart
- Persistent disks are 1 GB (shared across all mounts)

**Recommended alternatives (free, no paid subscriptions):**

#### Option A: ChromaDB on a free VPS (Recommended)
```yaml
# e.g., Oracle Cloud Free Tier, Fly.io, or Railway free tier
# Run ChromaDB as a separate service
docker run -d --name chromadb \
  -p 8000:8000 \
  -v chroma_data:/chroma/chroma \
  chromadb/chroma:0.5.23
```
Then set `CHROMA_HOST=<vps-ip>` in Render env vars.

#### Option B: SQLite-backed ChromaDB (single process)
If ChromaDB and backend are on the same machine, use persistent disk:
```yaml
# In docker-compose.production.yml
services:
  chromadb:
    image: chromadb/chroma:0.5.23
    volumes:
      - chroma_data:/chroma/chroma
```
But this is incompatible with Render's architecture.

#### Option C: In-memory mode (last resort)
```python
# In app/vector_store/vector_service.py, fall back to:
client = chromadb.EphemeralClient()
```
Data is lost on restart. Acceptable only for demos.

---

## 3. Uploaded Files Backup

### Documents & Uploads
```bash
#!/bin/bash
# backup-files.sh

BACKUP_DIR="/app/backups/files"
TIMESTAMP=$(date +%Y%m%d)
mkdir -p "$BACKUP_DIR"

# Tar + gzip the uploads and documents directories
tar -czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" /app/uploads
tar -czf "$BACKUP_DIR/documents_$TIMESTAMP.tar.gz" /app/documents

# Keep 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### Restore
```bash
tar -xzf uploads_20260716.tar.gz -C /app/uploads
tar -xzf documents_20260716.tar.gz -C /app/documents
```

---

## 4. Configuration Backup

### Environment Variables
```bash
# Export Render env vars locally
render env list healthcare-backend > backend_env_$(date +%Y%m%d).txt
render env list healthcare-frontend > frontend_env_$(date +%Y%m%d).txt

# Docker env files
cp backend/.env backend/.env.backup.$(date +%Y%m%d)
```

### Secrets (manual — NEVER commit to git)
```bash
# Store in password manager or encrypted file
gpg --symmetric --cipher-algo AES256 secrets.gpg
# Contains: JWT_SECRET_KEY, GEMINI_API_KEY, DATABASE_URLs
```

---

## 5. Automated Backup Script (all-in-one)

```bash
#!/bin/bash
# backup-all.sh — run daily via cron at 3 AM

BACKUP_ROOT="/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION=30

echo "=== Backup started: $TIMESTAMP ==="

# 1. PostgreSQL
pg_dump "$DATABASE_URL" --format=custom --compress=9 \
  --file="$BACKUP_ROOT/postgres/healthcare_$TIMESTAMP.dump" \
  && echo "PostgreSQL backup OK" || echo "PostgreSQL backup FAILED"

# 2. ChromaDB
if [ -d "/chroma/chroma" ]; then
  tar -czf "$BACKUP_ROOT/chroma/chroma_$TIMESTAMP.tar.gz" \
    -C /chroma chroma \
    && echo "ChromaDB backup OK" || echo "ChromaDB backup FAILED"
fi

# 3. Files
tar -czf "$BACKUP_ROOT/files/uploads_$TIMESTAMP.tar.gz" \
  -C /app uploads \
  && echo "Uploads backup OK" || echo "Uploads backup FAILED"
tar -czf "$BACKUP_ROOT/files/documents_$TIMESTAMP.tar.gz" \
  -C /app documents \
  && echo "Documents backup OK" || echo "Documents backup FAILED"

# 4. Cleanup old backups
find "$BACKUP_ROOT/postgres" -name "*.dump" -mtime +$RETENTION -delete
find "$BACKUP_ROOT/chroma" -name "*.tar.gz" -mtime +$RETENTION -delete
find "$BACKUP_ROOT/files" -name "*.tar.gz" -mtime +$RETENTION -delete

echo "=== Backup complete ==="
```

### Schedule with Cron (Docker)
```dockerfile
# Add to Dockerfile or use host cron
RUN apt-get install -y cron
COPY backup-all.sh /app/scripts/backup-all.sh
RUN chmod +x /app/scripts/backup-all.sh
RUN echo "0 3 * * * /app/scripts/backup-all.sh" | crontab -
```

### Schedule with Render Cron Jobs
```yaml
# Add to render.yaml (Render Cron Jobs are free)
cronJobs:
  - name: daily-backup
    schedule: "0 3 * * *"
    command: /app/scripts/backup-all.sh
    plan: free
```

---

## 6. Recovery Runbook

### Scenario A: Database corruption
```
1. Stop backend: docker compose -f docker/docker-compose.production.yml stop backend
2. Restore DB: pg_restore --clean -d "$DATABASE_URL" latest_backup.dump
3. Run migrations: alembic upgrade head
4. Start backend: docker compose start backend
5. Verify: curl http://localhost:8000/health → "healthy"
```

### Scenario B: ChromaDB data loss
```
1. Stop backend: docker compose stop backend
2. Restart ChromaDB: docker compose restart chromadb
3. Restore data: tar -xzf chroma_backup.tar.gz -C /chroma
4. Restart chromadb: docker compose restart chromadb
5. Start backend: docker compose start backend
6. Re-index documents if restore fails
```

### Scenario C: Full disaster recovery
```
1. Provision new PostgreSQL: see DATABASE_DEPLOYMENT_CHECKLIST.md
2. Restore database: pg_restore --clean -d "$DATABASE_URL" latest.dump
3. Run migrations: alembic upgrade head
4. Restore ChromaDB: tar -xzf chroma_backup.tar.gz -C /chroma
5. Restore files: tar -xzf uploads_backup.tar.gz -C /app/uploads
6. Set env vars from stored secrets
7. Start all services
8. Verify: curl /health, /ready, /live
```

### Scenario D: Accidental data deletion
```
1. Identify affected table(s) and time range
2. Extract specific table from full backup:
   pg_restore --list backup.dump | grep "table_data" > table_list.txt
   pg_restore -L table_list.txt --data-only -d "$DATABASE_URL" backup.dump
3. Verify data integrity
```

---

## 7. Backup Storage Strategy (Free Tier)

| Service | Location | Retention | Size Limit |
|---------|----------|-----------|------------|
| PostgreSQL | `/app/backups/postgres/` | 30 days | 1 GB (Render disk) |
| ChromaDB | `/app/backups/chroma/` | 30 days | 1 GB (Render disk) |
| Files | `/app/backups/files/` | 30 days | 1 GB (Render disk) |
| Config | Local machine + password manager | Indefinite | Minimal |

**Total backup storage needed:** ~500 MB–1.5 GB / 30 days

---

## 8. Testing the Backup

```bash
# Monthly verification:
# 1. Restore to a temporary database
createdb healthcare_backup_test
pg_restore -d healthcare_backup_test latest_backup.dump

# 2. Run health check queries
psql -d healthcare_backup_test -c "SELECT count(*) FROM users;"
psql -d healthcare_backup_test -c "SELECT count(*) FROM alembic_version;"

# 3. Clean up
dropdb healthcare_backup_test
```
