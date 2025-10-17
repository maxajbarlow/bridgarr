# Bridgarr Configuration Scripts

This directory contains helper scripts for configuring and managing Bridgarr.

## Available Scripts

### 1. configure-jellyseerr-webhook.py

**Purpose**: Automatically configure Jellyseerr-Bridgarr webhook to send media requests to Bridgarr backend.

**Prerequisites**:
- Jellyseerr-Bridgarr setup wizard must be completed (access http://YOUR_SERVER_IP:5057)
- Admin account created in Jellyseerr
- Python 3 with `requests` library installed

**Usage**:

**Interactive mode** (prompts for credentials):
```bash
cd /root/bridgarr/scripts
python3 configure-jellyseerr-webhook.py
```

**With arguments**:
```bash
python3 configure-jellyseerr-webhook.py --email admin@example.com --password YourPassword
```

**What it does**:
1. Logs in to Jellyseerr-Bridgarr
2. Fetches current webhook settings
3. Configures webhook to point to Bridgarr (`http://YOUR_SERVER_IP:8000/api/webhooks/overseerr`)
4. Enables notification types: Media Approved, Media Available, Media Auto-Approved
5. Tests the webhook connection
6. Verifies Bridgarr endpoint is reachable

**Example output**:
```
=== Jellyseerr-Bridgarr Webhook Configuration ===

[1/5] Logging in to Jellyseerr...
✓ Login successful
[2/5] Fetching current webhook settings...
✓ Retrieved current settings
[3/5] Configuring webhook for Bridgarr...
✓ Webhook configured successfully
[4/5] Testing Bridgarr webhook endpoint...
✓ Bridgarr endpoint is reachable
[5/5] Sending test webhook...
✓ Test webhook sent successfully

=== Configuration Complete! ===
```

---

### 2. configure-jellyseerr-webhook.sh

**Purpose**: Bash version of the webhook configuration script.

**Prerequisites**:
- Same as Python version
- `curl` and `jq` installed

**Usage**:
```bash
./configure-jellyseerr-webhook.sh admin@example.com YourPassword
```

---

## Installation Dependencies

For the Python script:
```bash
pip3 install requests
```

For the Bash script:
```bash
sudo apt-get install curl jq
```

---

## Troubleshooting

### "Connection refused" error

**Problem**: Cannot connect to Jellyseerr or Bridgarr

**Solutions**:
1. Verify Jellyseerr is running:
   ```bash
   docker ps | grep jellyseerr-bridgarr
   ```

2. Verify Bridgarr backend is running:
   ```bash
   docker ps | grep bridgarr-backend
   curl http://YOUR_SERVER_IP:8000/api/webhooks/test
   ```

### "Login failed" error

**Problem**: Invalid credentials

**Solutions**:
1. Verify you completed the Jellyseerr setup wizard
2. Check your email and password are correct
3. Access http://YOUR_SERVER_IP:5057 and try logging in manually

### "Webhook test failed" error

**Problem**: Webhook cannot reach Bridgarr

**Solutions**:
1. Check Bridgarr backend logs:
   ```bash
   docker logs bridgarr-backend --tail 50
   ```

2. Verify webhook URL is correct:
   ```bash
   curl http://YOUR_SERVER_IP:8000/api/webhooks/test
   ```

3. Check firewall rules allow port 8000

---

## Manual Configuration

If the scripts don't work, you can configure the webhook manually:

1. **Access Jellyseerr**: http://YOUR_SERVER_IP:5057
2. **Login** as admin
3. **Go to Settings** → Notifications → Webhook
4. **Enable Agent**: Toggle ON
5. **Webhook URL**: `http://YOUR_SERVER_IP:8000/api/webhooks/overseerr`
6. **Notification Types**: Enable these:
   - ✅ Media Approved
   - ✅ Media Available
   - ✅ Media Auto-Approved
7. **JSON Payload**: Select (NOT JSON Template)
8. **Save Changes**
9. **Send Test Notification**

---

## Verification

After configuration, verify the integration works:

### 1. Check webhook endpoint:
```bash
curl http://YOUR_SERVER_IP:8000/api/webhooks/test
```

Expected response:
```json
{
  "status": "ok",
  "message": "Webhook endpoint is reachable",
  "service": "Bridgarr",
  "version": "0.1.0-build.6"
}
```

### 2. Request a test movie:
1. Go to http://YOUR_SERVER_IP:5057
2. Search for a movie (e.g., "The Matrix")
3. Click Request
4. Approve the request (or enable auto-approve)

### 3. Check Bridgarr logs:
```bash
docker logs bridgarr-backend --tail 50
```

Look for:
```
INFO: Received webhook notification: MEDIA_APPROVED
```

### 4. Check database:
```bash
cd /root/bridgarr/bridgarr-backend
docker-compose exec postgres psql -U bridgarr -d bridgarr \
  -c "SELECT id, title, media_type, tmdb_id FROM media_items ORDER BY created_at DESC LIMIT 5;"
```

### 5. Check Bridgarr web interface:
http://YOUR_SERVER_IP:3002/library

---

## Related Documentation

- **Jellyseerr Integration Guide**: `/root/bridgarr/JELLYSEERR_LINKARR_INTEGRATION.md`
- **Deployment Guide**: `/root/bridgarr/DEPLOYMENT.md`
- **Project README**: `/root/bridgarr/README.md`

---

**Last Updated**: 2025-10-16
**Bridgarr Version**: v0.1.0-build.6
