# Jellyseerr Integration Guide for Bridgarr

## Overview

This guide covers setting up a **dedicated Jellyseerr instance** specifically for Bridgarr. You now have two separate Jellyseerr instances running:

- **Jellyseerr (Port 5055)** - For Jellyfin
- **Jellyseerr-Bridgarr (Port 5057)** - For Bridgarr ⭐ NEW!

Both instances run independently with their own configurations and databases.

---

## 🌐 Access Information

**Jellyseerr for Bridgarr:**
- **URL**: http://YOUR_SERVER_IP:5057
- **Container**: `jellyseerr-bridgarr`
- **Image**: fallenbagel/jellyseerr:latest
- **Status**: ✅ Running
- **Purpose**: Media requests for Bridgarr streaming platform

**Jellyseerr for Jellyfin (Existing):**
- **URL**: http://YOUR_SERVER_IP:5055
- **Container**: `jellyseerr`
- **Purpose**: Media requests for Jellyfin media server

---

## 🔧 Initial Setup for Bridgarr Jellyseerr

### Step 1: Access Jellyseerr-Bridgarr

Open your browser and navigate to:
```
http://YOUR_SERVER_IP:5057
```

You'll see the setup wizard.

### Step 2: Create Admin Account

1. Set admin username
2. Set admin email
3. Set admin password

### Step 3: Skip Media Server Connection

**Important:** Click **"Skip"** when asked about Plex/Jellyfin/Emby.

- Bridgarr doesn't need a traditional media server
- Bridgarr handles streaming directly from Real-Debrid
- This Jellyseerr instance is only for request management

### Step 4: Configure TMDb

You have two options:

**Option A: Sign in with TMDb Account**
- Click "Sign in with TMDb"
- Authorize the application
- Recommended for ease of use

**Option B: Use TMDb API Key**
- Get API key from: https://www.themoviedb.org/settings/api
- Paste the key in the setup wizard
- Click Continue

### Step 5: Complete Setup

- Review settings
- Click "Finish Setup"
- You'll be redirected to the Jellyseerr home page

---

## 🔗 Webhook Configuration for Bridgarr

After completing initial setup, configure the webhook to send requests to Bridgarr.

### 🤖 Automated Configuration (Recommended)

We've created a Python script to automate the webhook configuration:

**Step 1**: Complete the Jellyseerr setup wizard first (create admin account, configure TMDb)

**Step 2**: Run the configuration script:
```bash
cd /root/bridgarr/scripts
python3 configure-jellyseerr-webhook.py
```

The script will:
- ✅ Login to Jellyseerr-Bridgarr
- ✅ Configure webhook URL
- ✅ Enable correct notification types
- ✅ Test the connection
- ✅ Verify everything works

**Script location**: `/root/bridgarr/scripts/configure-jellyseerr-webhook.py`
**Documentation**: `/root/bridgarr/scripts/README.md`

---

### 📝 Manual Configuration

If you prefer to configure manually, follow these steps:

### Step 1: Access Settings

1. Login to Jellyseerr-Bridgarr: http://YOUR_SERVER_IP:5057
2. Click the **Settings** icon (gear) in the top right
3. Navigate to **Notifications** in the left sidebar
4. Click on **Webhook**

### Step 2: Enable Webhook Agent

Toggle **Enable Agent** to ON

### Step 3: Configure Webhook URL

Set the Webhook URL to:
```
http://YOUR_SERVER_IP:8000/api/webhooks/overseerr
```

**Important Notes:**
- Use the IP address (not localhost) for proper connectivity
- The endpoint is `/api/webhooks/overseerr` (compatible with both Overseerr and Jellyseerr)
- Port 8000 is the Bridgarr backend API

### Step 4: Select Notification Types

Enable these notification types:
- ✅ **Media Approved** - When admin approves a request
- ✅ **Media Available** - When media becomes available
- ✅ **Media Auto-Approved** - When media is auto-approved

**Do NOT enable:**
- ❌ Media Pending
- ❌ Media Declined
- ❌ Media Failed

### Step 5: Select JSON Payload

Make sure **JSON Payload** is selected (NOT JSON Template)

### Step 6: Authorization Header

Leave empty for now (can be configured later for additional security)

### Step 7: Save Configuration

Click **Save Changes**

---

## 🧪 Testing the Integration

### Test 1: Webhook Endpoint Connectivity

```bash
curl http://YOUR_SERVER_IP:8000/api/webhooks/test
```

**Expected Response:**
```json
{
  "status": "ok",
  "message": "Webhook endpoint is reachable",
  "service": "Bridgarr",
  "version": "0.1.0-build.6"
}
```

### Test 2: Send Test Notification

1. In Jellyseerr-Bridgarr webhook settings
2. Scroll to the bottom
3. Click **Send Test Notification**
4. You should see a success message

### Test 3: Check Bridgarr Logs

```bash
docker logs bridgarr-backend --tail 50
```

Look for:
```
INFO: Received webhook notification
```

### Test 4: Request a Movie

1. Login to Jellyseerr-Bridgarr (port 5057)
2. Search for a movie (e.g., "The Matrix")
3. Click **Request**
4. Approve the request (as admin)
5. Check Bridgarr backend logs
6. Check Bridgarr database:

```bash
cd /root/bridgarr/bridgarr-backend
docker-compose exec postgres psql -U bridgarr -d bridgarr \
  -c "SELECT id, title, media_type, tmdb_id, is_available FROM media_items ORDER BY created_at DESC LIMIT 5;"
```

---

## 🔄 Complete Workflow

```
┌────────────────┐         ┌──────────────┐         ┌──────────────┐
│   User         │         │ Jellyseerr   │         │   Bridgarr    │
│                │         │  (Port 5057) │         │   Backend    │
└───────┬────────┘         └──────┬───────┘         └──────┬───────┘
        │                         │                        │
        │ 1. Search "Avatar"      │                        │
        ├────────────────────────>│                        │
        │                         │                        │
        │ 2. Request Movie        │                        │
        ├────────────────────────>│                        │
        │                         │                        │
        │                         │ 3. Admin Approves      │
        │                         │                        │
        │                         │ 4. Webhook Sent        │
        │                         ├───────────────────────>│
        │                         │                        │
        │                         │                        │ 5. Fetch TMDb
        │                         │                        │    Metadata
        │                         │                        │
        │                         │                        │ 6. Search Torrent
        │                         │                        │
        │                         │                        │ 7. Add to RD
        │                         │                        │
        │                         │                        │ 8. Store in DB
        │                         │                        │
        │                         │<─── 9. Return 200 OK ──│
        │                         │                        │
        │ 10. Stream from Bridgarr │                        │
        │     Web UI (Port 3002)  │                        │
        └─────────────────────────┼────────────────────────>
                                  │
```

---

## 📊 Your Dual Jellyseerr Setup

### Port Configuration

| Service | Port | Purpose | URL |
|---------|------|---------|-----|
| **Jellyseerr-Bridgarr** | 5057 | Requests for Bridgarr | http://YOUR_SERVER_IP:5057 |
| **Jellyseerr** | 5055 | Requests for Jellyfin | http://YOUR_SERVER_IP:5055 |
| **Bridgarr Web** | 3002 | Stream media | http://YOUR_SERVER_IP:3002 |
| **Bridgarr API** | 8000 | Backend API | http://YOUR_SERVER_IP:8000 |

### Why Two Jellyseerr Instances?

**Benefits:**
- ✅ Separate request queues for each platform
- ✅ Independent user management
- ✅ Different approval workflows
- ✅ No configuration conflicts
- ✅ Each instance has its own database

**Use Cases:**
- Request via Jellyseerr-Bridgarr → Stream via Bridgarr (Real-Debrid direct)
- Request via Jellyseerr → Watch via Jellyfin (traditional media server)

---

## 🔒 Security Considerations

### Current Setup (Development)
- ⚠️ HTTP only (no HTTPS)
- ⚠️ No webhook authentication
- ⚠️ Ports exposed to internet

### Production Recommendations

1. **Add Reverse Proxy with SSL**
   ```nginx
   # nginx example
   server {
       listen 443 ssl;
       server_name jellyseerr-bridgarr.yourdomain.com;

       location / {
           proxy_pass http://localhost:5057;
       }
   }
   ```

2. **Webhook Authentication**
   - Add Authorization header in Jellyseerr webhook settings
   - Configure Bridgarr to validate the token

3. **Firewall Rules**
   ```bash
   sudo ufw allow 5057/tcp  # Jellyseerr-Bridgarr
   sudo ufw allow 5055/tcp  # Jellyseerr (Jellyfin)
   sudo ufw allow 3002/tcp  # Bridgarr Web
   sudo ufw allow 8000/tcp  # Bridgarr API
   ```

---

## 🐛 Troubleshooting

### Problem: Can't Access Jellyseerr-Bridgarr

**Solutions:**

1. **Check Container Status**
   ```bash
   docker ps | grep jellyseerr-bridgarr
   ```

2. **Check Logs**
   ```bash
   docker logs jellyseerr-bridgarr --tail 50
   ```

3. **Restart Container**
   ```bash
   cd /root/jellyseerr-bridgarr
   docker-compose restart
   ```

### Problem: Webhook Test Fails

**Solutions:**

1. **Verify Bridgarr is Running**
   ```bash
   curl http://YOUR_SERVER_IP:8000/api/webhooks/test
   ```

2. **Check Backend Logs**
   ```bash
   docker logs bridgarr-backend --tail 50
   ```

3. **Verify Webhook URL**
   - No trailing slash
   - Correct IP address
   - Port 8000 accessible

### Problem: Requests Don't Appear in Bridgarr

**Possible Causes:**

1. **TMDb API Key Missing**
   ```bash
   cd /root/bridgarr/bridgarr-backend
   grep TMDB_API_KEY .env
   ```
   Add if missing:
   ```bash
   nano .env
   # Add: TMDB_API_KEY=your_key_here
   docker-compose restart backend
   ```

2. **Wrong Notification Types**
   - Must enable: Media Approved, Media Available, Media Auto-Approved

3. **Check Database Connection**
   ```bash
   docker-compose ps postgres
   ```

### Problem: Port Conflict

If port 5057 is already in use:

```bash
# Edit docker-compose.yml
cd /root/jellyseerr-bridgarr
nano docker-compose.yml
# Change ports: - 5058:5055  (or another free port)
docker-compose down
docker-compose up -d
```

---

## 📋 Complete Configuration Example

```yaml
Jellyseerr-Bridgarr Webhook Settings:
  Enable Agent: ✅ ON
  Webhook URL: http://YOUR_SERVER_IP:8000/api/webhooks/overseerr

  Notification Types:
    - Media Approved: ✅
    - Media Available: ✅
    - Media Auto-Approved: ✅
    - Media Pending: ❌
    - Media Declined: ❌
    - Media Failed: ❌

  JSON Payload: ✅ Selected
  Authorization Header: (empty)
```

---

## 🚀 Quick Start Checklist

- [ ] Access http://YOUR_SERVER_IP:5057
- [ ] Complete admin account setup
- [ ] Skip media server connection
- [ ] Configure TMDb
- [ ] Enable webhook agent
- [ ] Set webhook URL to Bridgarr
- [ ] Enable correct notification types
- [ ] Select JSON Payload
- [ ] Save webhook settings
- [ ] Send test notification
- [ ] Request a test movie
- [ ] Verify in Bridgarr backend logs
- [ ] Check Bridgarr web interface for media

---

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Jellyseerr-Bridgarr | http://YOUR_SERVER_IP:5057 | Request media for Bridgarr |
| Bridgarr Web | http://YOUR_SERVER_IP:3002 | Browse & stream media |
| Bridgarr API | http://YOUR_SERVER_IP:8000 | Backend API |
| API Documentation | http://YOUR_SERVER_IP:8000/api/docs | Swagger UI |
| Webhook Endpoint | http://YOUR_SERVER_IP:8000/api/webhooks/overseerr | Receives webhooks |
| Webhook Test | http://YOUR_SERVER_IP:8000/api/webhooks/test | Test connectivity |
| TMDb API Keys | https://www.themoviedb.org/settings/api | Get TMDb key |
| Real-Debrid Token | https://real-debrid.com/apitoken | Get RD token |

---

## 💡 Tips

### Auto-Approval

To enable auto-approval for all requests:

1. Settings → General → Request Approval
2. Enable "Auto-Approve Movie Requests"
3. Enable "Auto-Approve Series Requests"
4. Save Changes

### User Permissions

Give regular users permission to request:

1. Settings → Users
2. Select user
3. Enable "Request" permission
4. Optionally enable "Auto-Approve"

### Request Limits

Set request limits per user:

1. Settings → General → Request Limits
2. Set movie quota (e.g., 10 per week)
3. Set TV show quota
4. Save Changes

---

## 📚 Additional Resources

- [Jellyseerr Documentation](https://docs.jellyseerr.dev/)
- [Bridgarr API Docs](http://YOUR_SERVER_IP:8000/api/docs)
- [TMDb API](https://developers.themoviedb.org/3)
- [Real-Debrid API](https://api.real-debrid.com/)

---

## 🎬 Next Steps

1. **Complete Jellyseerr-Bridgarr Setup**
   - Visit: http://YOUR_SERVER_IP:5057
   - Follow setup wizard
   - Configure webhook

2. **Configure Bridgarr**
   - Add TMDb API key to backend .env
   - Add Real-Debrid token in web settings

3. **Test Integration**
   - Request a movie
   - Approve it
   - Watch it appear in Bridgarr
   - Stream from Bridgarr web interface!

---

**Last Updated**: 2025-10-16
**Bridgarr Version**: v0.1.0-build.6
**Jellyseerr-Bridgarr Port**: 5057 (dedicated for Bridgarr)
**Container**: `jellyseerr-bridgarr`
