# Linkarr Deployment Guide - v0.1.0-build.4

## Current Deployment Status

**VPS**: your-vps-hostname (YOUR_SERVER_IP)
**Deployment Date**: 2025-10-15
**Build**: v0.1.0-build.4

### 🟢 Running Services

| Service | Status | Port | URL |
|---------|--------|------|-----|
| Backend API | ✅ Running | 8000 | http://YOUR_SERVER_IP:8000 |
| Web Management | ✅ Running | 3002 | http://YOUR_SERVER_IP:3002 |
| PostgreSQL | ✅ Healthy | 5432 | localhost:5432 |
| Redis | ✅ Healthy | 6379 | localhost:6379 |
| Celery Worker | ✅ Running | - | Background tasks |
| Celery Beat | ✅ Running | - | Scheduled tasks |

### 📊 Quick Access Links

- **Web Dashboard**: http://YOUR_SERVER_IP:3002
- **API Documentation**: http://YOUR_SERVER_IP:8000/api/docs
- **API Root**: http://YOUR_SERVER_IP:8000
- **Overseerr Webhook**: http://YOUR_SERVER_IP:8000/api/webhooks/overseerr

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VPS1 (your-vps-hostname)              │
│                   YOUR_SERVER_IP                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Backend    │  │     Web      │  │  PostgreSQL  │ │
│  │   FastAPI    │  │   Next.js    │  │   Database   │ │
│  │   :8000      │  │   :3002      │  │   :5432      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Redis     │  │   Celery     │  │   Celery     │ │
│  │   Cache      │  │   Worker     │  │    Beat      │ │
│  │   :6379      │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Docker Container Details

### Backend Services (docker-compose in linkarr-backend/)

```yaml
linkarr-backend:
  - Image: linkarr-backend-backend
  - Ports: 8000:8000
  - Status: Running
  - Health: OK
  - Restart: unless-stopped

linkarr-postgres:
  - Image: postgres:15-alpine
  - Ports: 5432:5432
  - Volume: postgres_data
  - Status: Running (Healthy)
  - Restart: unless-stopped

linkarr-redis:
  - Image: redis:7-alpine
  - Ports: 6379:6379
  - Status: Running (Healthy)
  - Restart: unless-stopped

linkarr-celery-worker:
  - Image: linkarr-backend-backend
  - Command: celery worker
  - Status: Running
  - Restart: unless-stopped

linkarr-celery-beat:
  - Image: linkarr-backend-backend
  - Command: celery beat
  - Status: Running
  - Restart: unless-stopped
```

### Web Frontend (standalone container)

```yaml
linkarr-web:
  - Image: linkarr-web
  - Ports: 3002:3000
  - Status: Running
  - Restart: unless-stopped
```

---

## Management Commands

### View Service Status

```bash
# Backend services
cd /root/linkarr/linkarr-backend
docker-compose ps

# Web frontend
docker ps | grep linkarr-web

# All services
docker ps | grep linkarr
```

### View Logs

```bash
# Backend API logs
docker logs linkarr-backend -f

# Web frontend logs
docker logs linkarr-web -f

# Celery worker logs
docker logs linkarr-celery-worker -f

# Celery beat logs
docker logs linkarr-celery-beat -f

# Database logs
docker logs linkarr-postgres -f
```

### Restart Services

```bash
# Restart backend
cd /root/linkarr/linkarr-backend
docker-compose restart backend

# Restart web frontend
docker restart linkarr-web

# Restart all backend services
docker-compose restart

# Restart everything
docker-compose restart && docker restart linkarr-web
```

### Update Deployment

```bash
# Pull latest code
cd /root/linkarr
git pull

# Rebuild backend
cd linkarr-backend
docker-compose build --no-cache
docker-compose up -d

# Rebuild web frontend
cd ../linkarr-web
docker build -t linkarr-web .
docker stop linkarr-web
docker rm linkarr-web
docker run -d -p 3002:3000 --name linkarr-web \
  -e NEXT_PUBLIC_API_URL=http://YOUR_SERVER_IP:8000 \
  --restart unless-stopped linkarr-web
```

---

## Configuration Files

### Backend Environment (.env)

Location: `/root/linkarr/linkarr-backend/.env`

**Critical Settings:**
- `APP_VERSION=0.1.0-build.4`
- `DATABASE_URL=postgresql://linkarr:linkarr_password@postgres:5432/linkarr`
- `REDIS_URL=redis://redis:6379/0`
- `SECRET_KEY=<generated>`
- `CORS_ORIGINS=http://localhost:3000,http://localhost:3002,http://YOUR_SERVER_IP:3002`

**TO BE CONFIGURED:**
- `TMDB_API_KEY=<your-key-here>`

### Web Frontend Environment

Built with:
- `NEXT_PUBLIC_API_URL=http://YOUR_SERVER_IP:8000`

---

## Integration Setup

### Overseerr Webhook Configuration

1. **Access Overseerr Settings**
   - Go to Settings → Notifications → Webhook

2. **Configure Webhook**
   ```
   Webhook URL: http://YOUR_SERVER_IP:8000/api/webhooks/overseerr
   ```

3. **Enable Notification Types**
   - ✅ Media Approved
   - ✅ Media Available
   - ✅ Media Auto-Approved

4. **Test Connection**
   ```bash
   curl http://YOUR_SERVER_IP:8000/api/webhooks/test
   ```

**Full Guide**: See `/root/linkarr/OVERSEERR_INTEGRATION.md`

---

## User Setup

### 1. Create Admin Account

1. Visit: http://YOUR_SERVER_IP:3002
2. Click "Login" → "Register"
3. Create account with username, email, password

### 2. Configure Real-Debrid Token

1. Get API token from: https://real-debrid.com/apitoken
2. Login to Linkarr web interface
3. Go to Settings
4. Paste RD API token and save

### 3. Add TMDb API Key

1. Get API key from: https://www.themoviedb.org/settings/api
2. SSH to VPS
3. Edit `.env` file:
   ```bash
   nano /root/linkarr/linkarr-backend/.env
   ```
4. Update `TMDB_API_KEY=your_key_here`
5. Restart backend:
   ```bash
   cd /root/linkarr/linkarr-backend
   docker-compose restart backend
   ```

---

## Monitoring & Health Checks

### API Health Endpoint

```bash
curl http://YOUR_SERVER_IP:8000/
```

Expected response:
```json
{
  "name": "Linkarr",
  "version": "0.1.0-build.4",
  "status": "running",
  "docs": "/api/docs"
}
```

### Database Connection

```bash
docker-compose exec postgres psql -U linkarr -d linkarr -c "SELECT COUNT(*) FROM users;"
```

### Redis Connection

```bash
docker-compose exec redis redis-cli ping
```

Expected: `PONG`

---

## Troubleshooting

### Backend Not Responding

```bash
# Check container status
docker ps | grep linkarr-backend

# Check logs for errors
docker logs linkarr-backend --tail 50

# Restart if needed
docker-compose restart backend
```

### Web Frontend Not Loading

```bash
# Check container status
docker ps | grep linkarr-web

# Check logs
docker logs linkarr-web --tail 50

# Restart
docker restart linkarr-web
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker logs linkarr-postgres --tail 50

# Verify connection from backend
docker-compose exec backend python -c "from app.database import engine; print(engine.connect())"
```

### CORS Errors in Web UI

1. Check CORS_ORIGINS in `.env`:
   ```bash
   grep CORS_ORIGINS /root/linkarr/linkarr-backend/.env
   ```

2. Should include: `http://YOUR_SERVER_IP:3002`

3. Restart backend after changes:
   ```bash
   docker-compose restart backend
   ```

---

## Backup & Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U linkarr linkarr > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker-compose exec -T postgres psql -U linkarr linkarr < backup_20251015_120000.sql
```

### Configuration Backup

```bash
# Backup .env file
cp /root/linkarr/linkarr-backend/.env /root/linkarr/linkarr-backend/.env.backup

# Backup docker-compose.yml
cp /root/linkarr/linkarr-backend/docker-compose.yml /root/linkarr/linkarr-backend/docker-compose.yml.backup
```

---

## Security Considerations

### Current Setup (Development/Testing)
- ✅ JWT authentication enabled
- ✅ Password hashing enabled
- ✅ CORS configured
- ⚠️ HTTP only (no HTTPS)
- ⚠️ Database password in .env file
- ⚠️ Ports exposed to internet

### Production Recommendations

1. **Enable HTTPS**
   - Use nginx reverse proxy with Let's Encrypt
   - Update CORS_ORIGINS to use https://

2. **Firewall Configuration**
   ```bash
   ufw allow 22/tcp   # SSH
   ufw allow 80/tcp   # HTTP (for Let's Encrypt)
   ufw allow 443/tcp  # HTTPS
   ufw enable
   ```

3. **Environment Security**
   - Use stronger database password
   - Store .env file with restricted permissions (600)
   - Never commit .env to git

4. **Database Security**
   - Don't expose PostgreSQL port externally
   - Use strong passwords
   - Regular backups

---

## Performance Optimization

### Current Resource Usage

```bash
# Check container resource usage
docker stats --no-stream

# Check disk usage
docker system df
```

### Optimization Tips

1. **Database**
   - Regular VACUUM operations
   - Index optimization
   - Connection pooling (already configured)

2. **Redis**
   - Monitor memory usage
   - Set maxmemory policy if needed

3. **Celery**
   - Adjust worker concurrency based on CPU
   - Monitor task queue length

---

## Maintenance Schedule

### Daily
- Monitor service health
- Check logs for errors
- Verify API responsiveness

### Weekly
- Review Celery task queue
- Check disk space usage
- Backup database

### Monthly
- Update dependencies (if critical patches)
- Review and archive old logs
- Performance analysis

---

## Contact & Support

**Documentation**:
- README: `/root/linkarr/README.md`
- Overseerr Integration: `/root/linkarr/OVERSEERR_INTEGRATION.md`
- Web Frontend: `/root/linkarr/linkarr-web/README.md`

**API Documentation**: http://YOUR_SERVER_IP:8000/api/docs

---

**Last Updated**: 2025-10-15
**Build**: v0.1.0-build.4
**Status**: Production Ready
