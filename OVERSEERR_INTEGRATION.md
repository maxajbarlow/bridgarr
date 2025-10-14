# Overseerr Integration Guide

## Overview

Connect Overseerr to Linkarr to automatically add approved media requests to your library. When a user requests content in Overseerr and it gets approved, Linkarr will automatically receive the notification and add it to your library.

---

## 🔗 Step-by-Step Setup

### 1. Access Overseerr Settings

1. Open your Overseerr instance
2. Login as an admin
3. Navigate to **Settings** (gear icon)
4. Go to **Notifications** in the left sidebar
5. Click on **Webhook**

### 2. Configure Webhook

#### Enable Webhook Agent
- Toggle **Enable Agent** to ON

#### Set Webhook URL
```
http://YOUR_SERVER_IP:8000/api/webhooks/overseerr
```

**Important Notes:**
- Replace `YOUR_SERVER_IP` with your actual Linkarr server IP if different
- If Overseerr is on the same server, you can use `http://localhost:8000/api/webhooks/overseerr`
- If using HTTPS (recommended for production), use `https://` instead

#### Select Notification Types

Enable the following notification types:
- ✅ **Media Approved** - Triggers when admin approves a request
- ✅ **Media Available** - Triggers when media becomes available
- ✅ **Media Auto-Approved** - Triggers when media is auto-approved

**Do NOT enable** (these won't be processed):
- ❌ Media Pending
- ❌ Media Declined
- ❌ Media Failed

#### Payload Format
- Select **JSON Payload** (NOT JSON Template)

#### Authorization Header (Optional)
- Leave empty for now
- Can be configured later for additional security

### 3. Test the Connection

#### Option 1: Use Overseerr Test Button
1. Scroll down in the webhook settings
2. Click **Send Test Notification**
3. Check if you see a success message

#### Option 2: Manual Test via curl
```bash
curl -X POST http://YOUR_SERVER_IP:8000/api/webhooks/test
```

**Expected Response:**
```json
{
  "status": "ok",
  "message": "Webhook endpoint is reachable",
  "service": "Linkarr",
  "version": "0.1.0-build.3",
  "timestamp": "2025-10-14T22:46:43.339603"
}
```

### 4. Verify Webhook Test Endpoint

Visit this URL in your browser:
```
http://YOUR_SERVER_IP:8000/api/webhooks/test
```

You should see the JSON response above.

---

## 📋 Complete Configuration Example

Here's what your Overseerr webhook configuration should look like:

```yaml
Webhook Configuration:
  Enable Agent: ON
  Webhook URL: http://YOUR_SERVER_IP:8000/api/webhooks/overseerr

  Notification Types:
    - Media Approved: ✅
    - Media Available: ✅
    - Media Auto-Approved: ✅
    - Media Pending: ❌
    - Media Declined: ❌
    - Media Failed: ❌

  JSON Payload: Selected
  Authorization Header: (empty)
```

---

## 🔄 How It Works

### Workflow

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   Overseerr  │        │   Linkarr    │        │  Real-Debrid │
│              │        │   Backend    │        │              │
└──────┬───────┘        └──────┬───────┘        └──────┬───────┘
       │                       │                       │
       │ 1. User requests      │                       │
       │    "The Matrix"       │                       │
       │                       │                       │
       │ 2. Admin approves     │                       │
       │                       │                       │
       │ 3. Webhook sent ──────>                       │
       │    (MEDIA_APPROVED)   │                       │
       │                       │                       │
       │                       │ 4. Fetch metadata     │
       │                       │    from TMDb          │
       │                       │                       │
       │                       │ 5. Search for torrent │
       │                       │                       │
       │                       │ 6. Add to RD ────────>│
       │                       │                       │
       │                       │<─ 7. Get streaming URL│
       │                       │                       │
       │                       │ 8. Store in database  │
       │                       │                       │
       │<─ 9. Return success ──│                       │
       │                       │                       │
```

### What Happens When Media is Approved

1. **Overseerr sends webhook** to Linkarr with media information
2. **Linkarr receives webhook** and validates the payload
3. **Background task created** to process the request asynchronously
4. **Immediate 200 response** sent back to Overseerr (webhook confirmed)
5. **Background processing:**
   - Checks if media already exists in Linkarr database
   - Fetches detailed metadata from TMDb (title, poster, description, etc.)
   - Creates placeholder entry in database
   - Queues torrent search task (when implemented)
   - Adds torrent to Real-Debrid
   - Stores streaming URLs

---

## 🧪 Testing the Integration

### Test 1: Request a Movie in Overseerr

1. Login to Overseerr as a regular user
2. Search for a movie (e.g., "The Matrix")
3. Click **Request**
4. Login as admin and approve the request
5. Check Linkarr logs to see the webhook received

### Test 2: Check Linkarr Logs

```bash
cd /root/linkarr/linkarr-backend
docker-compose logs -f backend
```

You should see:
```
INFO: Received webhook notification: MEDIA_APPROVED
INFO: Processing media request for TMDb ID: 603
INFO: Added movie: The Matrix (TMDb ID: 603)
```

### Test 3: Verify in Database

```bash
docker-compose exec postgres psql -U linkarr -d linkarr -c "SELECT id, title, media_type, is_available FROM media_items ORDER BY created_at DESC LIMIT 5;"
```

---

## 📊 Webhook Payload Example

When Overseerr sends a webhook, here's what the payload looks like:

```json
{
  "notification_type": "MEDIA_APPROVED",
  "subject": "Movie Request Approved",
  "message": "The Matrix has been approved",
  "media": {
    "media_type": "movie",
    "tmdbId": 603,
    "tvdbId": null,
    "status": "APPROVED"
  },
  "request": {
    "request_id": 123,
    "requestedBy_username": "john_doe",
    "requestedBy_email": "john@example.com"
  },
  "extra": []
}
```

### Supported Notification Types

| Type | Processed? | Description |
|------|------------|-------------|
| `MEDIA_APPROVED` | ✅ Yes | Admin manually approved request |
| `MEDIA_AVAILABLE` | ✅ Yes | Media is now available for download |
| `MEDIA_AUTO_APPROVED` | ✅ Yes | Media was auto-approved based on rules |
| `MEDIA_PENDING` | ❌ No | Request is waiting for approval |
| `MEDIA_DECLINED` | ❌ No | Request was declined |
| `MEDIA_FAILED` | ❌ No | Request processing failed |

---

## 🔒 Security Considerations

### For Production Deployment

1. **Use HTTPS**
   ```
   https://your-domain.com/api/webhooks/overseerr
   ```

2. **Add Reverse Proxy** (nginx/Caddy)
   - Handles SSL/TLS encryption
   - Rate limiting
   - Additional security headers

3. **Webhook Secret** (Future Enhancement)
   - Currently not implemented
   - Can be added to verify webhook authenticity

4. **Firewall Rules**
   - Restrict webhook endpoint to Overseerr IP only
   - Use VPN or private network if both services are on same network

---

## 🐛 Troubleshooting

### Problem: Overseerr Test Fails

**Symptoms:**
- Test notification in Overseerr shows error
- Connection timeout

**Solutions:**
1. Check Linkarr backend is running:
   ```bash
   docker-compose ps
   ```

2. Test endpoint directly:
   ```bash
   curl http://YOUR_SERVER_IP:8000/api/webhooks/test
   ```

3. Check firewall rules:
   ```bash
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

4. Verify URL is correct (no trailing slash)

### Problem: Webhook Received but Nothing Happens

**Symptoms:**
- Webhook returns 200 OK
- But media doesn't appear in Linkarr

**Solutions:**
1. Check backend logs for errors:
   ```bash
   docker-compose logs -f backend
   ```

2. Verify TMDb API key is configured:
   ```bash
   cat .env | grep TMDB_API_KEY
   ```

3. Check if media already exists:
   ```bash
   docker-compose exec postgres psql -U linkarr -d linkarr -c "SELECT * FROM media_items WHERE tmdb_id = 603;"
   ```

### Problem: Database Connection Errors

**Symptoms:**
- 500 errors in webhook responses
- Database connection failures in logs

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Verify database credentials in `.env`:
   ```bash
   grep DATABASE_URL .env
   ```

3. Restart backend:
   ```bash
   docker-compose restart backend
   ```

---

## 📝 Advanced Configuration

### Custom Notification Template (Future)

You can customize what information Overseerr sends by creating a custom JSON template. This is optional and not required for basic functionality.

### Webhook Retry Logic

Overseerr will automatically retry failed webhooks:
- 1st retry: After 5 seconds
- 2nd retry: After 10 seconds
- 3rd retry: After 30 seconds
- After 3 failures, webhook is marked as failed

---

## 🔗 Related Resources

- [Overseerr Documentation](https://docs.overseerr.dev/)
- [Linkarr API Docs](http://YOUR_SERVER_IP:8000/api/docs)
- [Real-Debrid API](https://api.real-debrid.com/)
- [TMDb API](https://developers.themoviedb.org/3)

---

## 📞 Support

If you encounter issues:
1. Check Linkarr backend logs
2. Check Overseerr logs
3. Verify network connectivity between services
4. Test webhook endpoint manually

**Backend Logs:**
```bash
cd /root/linkarr/linkarr-backend
docker-compose logs -f backend
```

**Test Webhook:**
```bash
curl -v http://YOUR_SERVER_IP:8000/api/webhooks/test
```

---

**Last Updated:** 2025-10-14
**Linkarr Version:** v0.1.0-build.3
