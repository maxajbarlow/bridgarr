# Bridgarr Quick Start Guide

Get Bridgarr up and running in 5 minutes!

## Prerequisites

- ✅ Bridgarr backend running on port 8000
- ✅ Bridgarr web interface running on port 3002
- ✅ Jellyseerr-Bridgarr container running on port 5057
- ✅ Real-Debrid account and API token

---

## Step 1: Create Bridgarr Account (2 minutes)

### Option A: Using Web Interface

1. **Open Bridgarr**: http://YOUR_SERVER_IP:3002
2. **Click "Register"**
3. **Fill in details**:
   - Email: your@email.com
   - Username: yourusername
   - Password: (choose a strong password)
4. **Click "Register"**
5. **Login** with your credentials

### Option B: Using API

```bash
curl -X POST http://YOUR_SERVER_IP:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "YourSecurePassword123"
  }'
```

---

## Step 2: Configure Real-Debrid (1 minute)

1. **Get your Real-Debrid API token**:
   - Go to: https://real-debrid.com/apitoken
   - Copy your token

2. **Add to Bridgarr**:
   - **Web UI**: Go to Settings → Paste token → Save
   - **API**:
   ```bash
   # First login to get JWT token
   TOKEN=$(curl -s -X POST http://YOUR_SERVER_IP:8000/api/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=YourSecurePassword123" | jq -r '.access_token')

   # Save RD token
   curl -X POST http://YOUR_SERVER_IP:8000/api/auth/rd-token \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"rd_api_token": "YOUR_RD_TOKEN_HERE"}'
   ```

---

## Step 3: Setup Jellyseerr-Bridgarr (2 minutes)

### 3.1: Complete Setup Wizard

1. **Open Jellyseerr**: http://YOUR_SERVER_IP:5057
2. **Create admin account**:
   - Email: admin@example.com
   - Username: admin
   - Password: (choose a password)
3. **Skip media server** (click "Skip")
4. **Configure TMDb**:
   - Option A: Sign in with TMDb account (recommended)
   - Option B: Enter TMDb API key from https://www.themoviedb.org/settings/api
5. **Click "Finish Setup"**

### 3.2: Configure Webhook (Automated)

```bash
cd /root/bridgarr/scripts
python3 configure-jellyseerr-webhook.py
```

**Enter your Jellyseerr credentials when prompted.**

The script will automatically:
- ✅ Configure webhook URL
- ✅ Enable correct notification types
- ✅ Test the connection

### 3.3: Optional - Manual Webhook Setup

If you prefer manual configuration:

1. Login to Jellyseerr: http://YOUR_SERVER_IP:5057
2. Settings → Notifications → Webhook
3. **Enable Agent**: ON
4. **Webhook URL**: `http://YOUR_SERVER_IP:8000/api/webhooks/overseerr`
5. **Enable these notifications**:
   - ✅ Media Approved
   - ✅ Media Available
   - ✅ Media Auto-Approved
6. **Select**: JSON Payload
7. **Save Changes**

---

## Step 4: Test the Integration (1 minute)

### 4.1: Request a Movie

1. **Open Jellyseerr**: http://YOUR_SERVER_IP:5057
2. **Search** for a movie (e.g., "The Matrix")
3. **Click "Request"**
4. **Approve** the request (or enable auto-approval in Settings)

### 4.2: Verify in Bridgarr

**Check backend logs**:
```bash
docker logs bridgarr-backend --tail 50
```

Look for:
```
INFO: Received webhook notification: MEDIA_APPROVED
```

**Check web interface**:
http://YOUR_SERVER_IP:3002/library

Your requested movie should appear!

### 4.3: Verify in Database

```bash
cd /root/bridgarr/bridgarr-backend
docker-compose exec postgres psql -U bridgarr -d bridgarr \
  -c "SELECT id, title, media_type, tmdb_id, is_available FROM media_items ORDER BY created_at DESC LIMIT 5;"
```

---

## Step 5: Stream Media

1. **Open Bridgarr**: http://YOUR_SERVER_IP:3002/library
2. **Click on a movie**
3. **Click "Play"** (when available)
4. **Enjoy!** 🎬

---

## Quick Reference URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Bridgarr Web** | http://YOUR_SERVER_IP:3002 | Browse & stream media |
| **Bridgarr API** | http://YOUR_SERVER_IP:8000 | Backend API |
| **API Docs** | http://YOUR_SERVER_IP:8000/api/docs | Interactive API documentation |
| **Jellyseerr** | http://YOUR_SERVER_IP:5057 | Request media |
| **Real-Debrid** | https://real-debrid.com/apitoken | Get API token |
| **TMDb API** | https://www.themoviedb.org/settings/api | Get TMDb key |

---

## Optional: Enable Auto-Approval

To automatically approve all requests in Jellyseerr:

1. **Jellyseerr** → Settings → General
2. **Enable**:
   - ✅ Auto-Approve Movie Requests
   - ✅ Auto-Approve Series Requests
3. **Save Changes**

Now all requests will be sent to Bridgarr immediately!

---

## Common Issues & Solutions

### Issue: "Cannot connect to Bridgarr backend"

**Check services are running**:
```bash
docker ps | grep bridgarr
```

**Restart if needed**:
```bash
cd /root/bridgarr/bridgarr-backend
docker-compose restart
```

### Issue: "Webhook test fails"

**Verify endpoint**:
```bash
curl http://YOUR_SERVER_IP:8000/api/webhooks/test
```

**Expected response**:
```json
{
  "status": "ok",
  "message": "Webhook endpoint is reachable",
  "service": "Bridgarr",
  "version": "0.1.0-build.6"
}
```

### Issue: "Requests don't appear in Bridgarr"

1. **Check webhook is configured** in Jellyseerr
2. **Check TMDb API key** is set in backend:
   ```bash
   cd /root/bridgarr/bridgarr-backend
   grep TMDB_API_KEY .env
   ```
3. **Check logs** for errors:
   ```bash
   docker logs bridgarr-backend --tail 100
   ```

### Issue: "Cannot stream media"

1. **Verify Real-Debrid token** is configured
2. **Check RD account** is premium and active
3. **Check media is available** (green badge in library)

---

## What's Next?

### Add More Users

1. Register additional users at http://YOUR_SERVER_IP:3002
2. Give them access to Jellyseerr: http://YOUR_SERVER_IP:5057
3. Configure user permissions in Jellyseerr Settings → Users

### Set Request Limits

Jellyseerr → Settings → Request Limits:
- Set movie quota (e.g., 10 per week)
- Set TV show quota
- Save changes

### Monitor Usage

**View logs**:
```bash
docker logs bridgarr-backend -f
docker logs bridgarr-web -f
docker logs jellyseerr-bridgarr -f
```

**Check database stats**:
```bash
cd /root/bridgarr/bridgarr-backend
docker-compose exec postgres psql -U bridgarr -d bridgarr \
  -c "SELECT media_type, COUNT(*) FROM media_items GROUP BY media_type;"
```

---

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   User      │         │ Jellyseerr   │         │   Bridgarr    │
│             │         │  (Port 5057) │         │   Backend    │
└──────┬──────┘         └──────┬───────┘         └──────┬───────┘
       │                       │                        │
       │ 1. Request "Avatar"   │                        │
       ├──────────────────────>│                        │
       │                       │                        │
       │ 2. Approve request    │                        │
       │                       │ 3. Webhook             │
       │                       ├───────────────────────>│
       │                       │                        │
       │                       │                        │ 4. Fetch metadata
       │                       │                        │ 5. Search torrents
       │                       │                        │ 6. Add to RD
       │                       │                        │ 7. Store in DB
       │                       │                        │
       │ 8. Stream from Bridgarr web (Port 3002)        │
       └───────────────────────┴────────────────────────>
```

---

## Support & Documentation

- **Full Setup Guide**: `/root/bridgarr/JELLYSEERR_LINKARR_INTEGRATION.md`
- **Deployment Guide**: `/root/bridgarr/DEPLOYMENT.md`
- **Configuration Scripts**: `/root/bridgarr/scripts/README.md`
- **Project README**: `/root/bridgarr/README.md`

---

**Last Updated**: 2025-10-16
**Bridgarr Version**: v0.1.0-build.6
**Status**: Production Ready ✅

Happy streaming! 🎬🍿
