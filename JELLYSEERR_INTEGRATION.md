# Jellyseerr Integration Guide for Bridgarr

## Overview

Jellyseerr (a fork of Overseerr) is already installed and running on your VPS. This guide will help you configure it to work with Bridgarr for automatic media requests.

**What is Jellyseerr?**
Jellyseerr is a request management and media discovery tool that works with both Plex and Jellyfin. It's a fork of Overseerr with additional features, and it's 100% compatible with Bridgarr's webhook system.

---

## 🌐 Access Information

- **Jellyseerr URL**: http://YOUR_SERVER_IP:5055
- **Container Name**: `jellyseerr`
- **Port**: 5055
- **Status**: ✅ Running (30+ hours uptime)

---

## 🔧 Initial Setup

### 1. Access Jellyseerr

Open your browser and navigate to:
```
http://YOUR_SERVER_IP:5055
```

### 2. Complete Initial Configuration

On first access, you'll need to:

1. **Create Admin Account**
   - Set admin username
   - Set admin password
   - Set admin email

2. **Connect to Media Server** (Optional)
   - You can skip this step or configure Plex/Jellyfin if you have them
   - For Bridgarr-only setup, you don't need a media server

3. **Configure TMDb**
   - Sign in with your TMDb account
   - Or provide TMDb API key
   - This enables media search and metadata

---

## 🔗 Webhook Configuration for Bridgarr

### Step 1: Login to Jellyseerr

Navigate to http://YOUR_SERVER_IP:5055 and login as admin.

### Step 2: Access Settings

1. Click the **Settings** icon (gear) in the top right
2. Navigate to **Notifications** in the left sidebar
3. Click on **Webhook**

### Step 3: Enable Webhook Agent

Toggle **Enable Agent** to ON

### Step 4: Configure Webhook URL

Set the Webhook URL to:
```
http://YOUR_SERVER_IP:8000/api/webhooks/overseerr
```

**Important Notes:**
- Use the IP address, not localhost (unless Jellyseerr and Bridgarr are in the same Docker network)
- The webhook endpoint is `/api/webhooks/overseerr` (compatible with both Overseerr and Jellyseerr)
- Make sure the port 8000 is accessible

### Step 5: Select Notification Types

Enable these notification types:
- ✅ **Media Approved** - When admin approves a request
- ✅ **Media Available** - When media becomes available
- ✅ **Media Auto-Approved** - When media is auto-approved by rules

**Do NOT enable**:
- ❌ Media Pending
- ❌ Media Declined
- ❌ Media Failed

### Step 6: Select JSON Payload

Make sure **JSON Payload** is selected (NOT JSON Template)

### Step 7: Save Configuration

Click **Save Changes**

---

## 🧪 Testing the Integration

### Test 1: Webhook Endpoint

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

1. In Jellyseerr webhook settings
2. Scroll to the bottom
3. Click **Send Test Notification**
4. You should see a success message

### Test 3: Check Bridgarr Logs

```bash
docker logs bridgarr-backend --tail 50
```

Look for:
```
INFO: Received webhook notification: MEDIA_APPROVED
```

---

## 📋 Complete Configuration Example

```yaml
Webhook Settings:
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

## 🔄 How It Works

### Workflow

```
┌────────────────┐         ┌──────────────┐         ┌──────────────┐
│   User         │         │   Jellyseerr │         │   Bridgarr    │
│                │         │              │         │   Backend    │
└───────┬────────┘         └──────┬───────┘         └──────┬───────┘
        │                         │                        │
        │ 1. Search for "Avatar"  │                        │
        ├────────────────────────>│                        │
        │                         │                        │
        │ 2. Request movie        │                        │
        ├────────────────────────>│                        │
        │                         │                        │
        │                         │ 3. Admin approves      │
        │                         │    (or auto-approved)  │
        │                         │                        │
        │                         │ 4. Webhook sent        │
        │                         ├───────────────────────>│
        │                         │                        │
        │                         │                        │ 5. Fetch TMDb
        │                         │                        │    metadata
        │                         │                        │
        │                         │                        │ 6. Search torrent
        │                         │                        │
        │                         │                        │ 7. Add to RD
        │                         │                        │
        │                         │                        │ 8. Store in DB
        │                         │                        │
        │                         │<─── 9. Return 200 OK ──│
        │                         │                        │
        │ 10. Access via          │                        │
        │     Bridgarr Web UI      │                        │
        └─────────────────────────┼────────────────────────>
                                  │
```

### What Happens When You Request Media

1. **User requests** content in Jellyseerr (e.g., "Avatar")
2. **Admin approves** the request (or it's auto-approved)
3. **Jellyseerr sends webhook** to Bridgarr with:
   - Media type (movie/tv)
   - TMDb ID
   - Request details
4. **Bridgarr receives webhook** and creates background task
5. **Immediate response** sent to Jellyseerr (200 OK)
6. **Background processing**:
   - Fetches TMDb metadata
   - Creates database entry
   - Searches for torrents (when implemented)
   - Adds to Real-Debrid
   - Generates streaming URLs
7. **Media appears** in Bridgarr web interface
8. **User can stream** directly from RD CDN

---

## 🎬 End-to-End Testing

### Step 1: Request a Movie

1. Login to Jellyseerr as a regular user
2. Search for a movie (e.g., "The Matrix")
3. Click **Request**
4. Wait for admin approval (or set auto-approval)

### Step 2: Approve Request

1. Login as admin
2. Go to **Requests** page
3. Approve the pending request

### Step 3: Verify in Bridgarr

1. Check Bridgarr backend logs:
```bash
docker logs bridgarr-backend --tail 50
```

2. Check Bridgarr web interface:
```
http://YOUR_SERVER_IP:3002/library
```

3. Verify database entry:
```bash
cd /root/bridgarr/bridgarr-backend
docker-compose exec postgres psql -U bridgarr -d bridgarr \
  -c "SELECT id, title, media_type, tmdb_id, is_available FROM media_items ORDER BY created_at DESC LIMIT 5;"
```

---

## 🔒 Security Considerations

### Current Setup (Development)
- ✅ Jellyseerr accessible via HTTP
- ⚠️ No webhook authentication
- ⚠️ Ports exposed to internet

### Production Recommendations

1. **Add Reverse Proxy**
   - Use nginx or Caddy with SSL
   - Enable HTTPS for both Jellyseerr and Bridgarr
   - Update webhook URL to use HTTPS

2. **Webhook Authentication**
   ```
   Authorization Header: Bearer your-secret-token
   ```
   - Add to Jellyseerr webhook settings
   - Configure Bridgarr to validate token

3. **Network Isolation**
   - Put Jellyseerr and Bridgarr in same Docker network
   - Use internal hostnames instead of public IPs
   - Only expose necessary ports

4. **Firewall Rules**
   ```bash
   sudo ufw allow 5055/tcp  # Jellyseerr
   sudo ufw allow 8000/tcp  # Bridgarr API
   sudo ufw allow 3002/tcp  # Bridgarr Web
   ```

---

## 🐛 Troubleshooting

### Problem: Jellyseerr Test Notification Fails

**Solutions:**

1. **Check Bridgarr is Running**
   ```bash
   curl http://YOUR_SERVER_IP:8000/api/webhooks/test
   ```

2. **Check Docker Logs**
   ```bash
   docker logs jellyseerr --tail 50
   docker logs bridgarr-backend --tail 50
   ```

3. **Verify URL**
   - Make sure no trailing slash
   - Use IP address not hostname (unless DNS configured)
   - Port 8000 must be accessible

### Problem: Webhook Received but Nothing Happens

**Solutions:**

1. **Check Bridgarr Logs**
   ```bash
   docker logs bridgarr-backend -f
   ```

2. **Verify TMDb API Key**
   ```bash
   cd /root/bridgarr/bridgarr-backend
   grep TMDB_API_KEY .env
   ```

3. **Check Database Connection**
   ```bash
   docker-compose ps postgres
   ```

### Problem: Media Doesn't Appear in Bridgarr

**Possible Causes:**

1. **No Real-Debrid Token** - Configure in Bridgarr settings
2. **TMDb API Key Missing** - Add to backend .env
3. **Webhook Not Configured** - Check Jellyseerr settings
4. **Wrong Notification Type** - Must be "Media Approved/Available"

---

## 📊 Webhook Payload Example

When Jellyseerr sends a webhook for "Media Approved":

```json
{
  "notification_type": "MEDIA_APPROVED",
  "subject": "Movie Request Approved",
  "message": "Avatar has been approved",
  "media": {
    "media_type": "movie",
    "tmdbId": 19995,
    "tvdbId": null,
    "status": "APPROVED"
  },
  "request": {
    "request_id": 1,
    "requestedBy_username": "john",
    "requestedBy_email": "john@example.com"
  }
}
```

---

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Jellyseerr Web | http://YOUR_SERVER_IP:5055 | Request media |
| Bridgarr Web | http://YOUR_SERVER_IP:3002 | Browse library |
| Bridgarr API | http://YOUR_SERVER_IP:8000 | Backend API |
| Webhook Endpoint | http://YOUR_SERVER_IP:8000/api/webhooks/overseerr | Receives webhooks |
| Webhook Test | http://YOUR_SERVER_IP:8000/api/webhooks/test | Test connectivity |

---

## 📝 Next Steps

1. **Access Jellyseerr**: http://YOUR_SERVER_IP:5055
2. **Complete initial setup** (admin account, TMDb)
3. **Configure webhook** following this guide
4. **Test with a movie request**
5. **Verify in Bridgarr web interface**
6. **Configure Real-Debrid token** in Bridgarr settings

---

## 📚 Additional Resources

- [Jellyseerr Documentation](https://docs.jellyseerr.dev/)
- [Overseerr Documentation](https://docs.overseerr.dev/) (compatible)
- [Bridgarr API Docs](http://YOUR_SERVER_IP:8000/api/docs)
- [TMDb API](https://developers.themoviedb.org/3)
- [Real-Debrid API](https://api.real-debrid.com/)

---

**Last Updated**: 2025-10-16
**Bridgarr Version**: v0.1.0-build.6
**Jellyseerr Version**: Latest (fallenbagel/jellyseerr)
