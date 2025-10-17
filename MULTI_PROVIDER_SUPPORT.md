# Multi-Provider Debrid Support - v1.0.1

Bridgarr now supports **4 popular debrid services**, giving you the flexibility to choose your preferred provider!

## Supported Providers

### 1. Real-Debrid (€3/month)
- **Website**: https://real-debrid.com
- **API Token**: https://real-debrid.com/apitoken
- **Features**: Large torrent cache, fast CDN, excellent availability
- **Best For**: Most users - great value and reliability

### 2. AllDebrid (€3/month)
- **Website**: https://alldebrid.com
- **API Token**: https://alldebrid.com/apikeys
- **Features**: European servers, good cache, competitive pricing
- **Best For**: European users, alternative to Real-Debrid

### 3. Premiumize (~€8/month)
- **Website**: https://premiumize.me
- **API Token**: https://www.premiumize.me/account
- **Features**: Cloud storage, VPN included, premium support
- **Best For**: Users wanting cloud storage + debrid in one service

### 4. Debrid-Link (€3/month)
- **Website**: https://debrid-link.fr
- **API Token**: https://debrid-link.fr/webapp/apikey
- **Features**: Seedbox integration, French company, good cache
- **Best For**: Users in France, seedbox features

## How to Use

### Setting Up Your Provider

1. **Register with your chosen provider** (links above)
2. **Get a premium subscription** (most are ~€3/month)
3. **Get your API token** from your account settings
4. **In Bridgarr**:
   - Go to Settings
   - Select your provider from the dropdown
   - Paste your API token
   - Click "Save"

### For New Users

When you register on Bridgarr:
- Default provider is Real-Debrid
- You can change it anytime in Settings
- Token is validated before saving

### For Existing Users

If you already have a Real-Debrid token configured:
- It will continue to work seamlessly
- You can switch to another provider anytime
- Your existing library remains accessible

## Technical Details

### API Endpoints

#### New Endpoints
- `POST /api/auth/debrid-token` - Save debrid provider and token
- `GET /api/auth/debrid-token/test` - Test token validity
- `DELETE /api/auth/debrid-token` - Remove token

#### Legacy Endpoints (Still Supported)
- `POST /api/auth/rd-token` - Saves as Real-Debrid token
- `GET /api/auth/rd-token/test` - Tests RD token
- `DELETE /api/auth/rd-token` - Removes RD token

### Request Format

**Save debrid token:**
```json
POST /api/auth/debrid-token
{
  "provider": "real-debrid",  // or "alldebrid", "premiumize", "debrid-link"
  "api_token": "your_token_here"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "debrid_provider": "real-debrid",
  "has_debrid_token": true,
  "has_rd_token": true,  // legacy field
  // ... other fields
}
```

### Database Schema

New columns in `users` table:
- `debrid_provider` (enum) - Selected provider
- `debrid_api_token` (string) - API token
- `debrid_token_expires_at` (datetime) - Token expiration

Legacy columns (kept for backwards compatibility):
- `rd_api_token` (string) - Real-Debrid token
- `rd_token_expires_at` (datetime) - RD token expiration

### Provider Implementation

Each provider implements the `BaseDebridClient` interface:

```python
from app.services.debrid import get_debrid_client, DebridProvider

# Get a client for the user's provider
client = get_debrid_client(
    provider=user.debrid_provider,
    api_token=user.debrid_api_token
)

# All providers support these methods:
client.validate_token()
client.add_magnet(magnet_link)
client.get_torrent_info(torrent_id)
client.process_torrent_for_content(magnet_link)
client.unrestrict_link(link)
# ... and more
```

### Status Normalization

All providers return standardized status codes:
- `QUEUED` - Torrent waiting to start
- `DOWNLOADING` - Currently downloading
- `PROCESSING` - Compressing/uploading
- `READY` - Available for streaming
- `ERROR` - Failed/error state
- `EXPIRED` - Link expired
- `DEAD` - Torrent dead/unavailable

### Provider-Specific Behavior

#### Real-Debrid
- File selection required
- Links expire after 4 hours (auto-refreshed)
- Instant availability check supported

#### AllDebrid
- Automatic file processing
- Status codes: 0-6 (converted to standard)
- Links generated on-demand

#### Premiumize
- Cloud folder-based retrieval
- No file selection needed
- Permanent links (no expiration)
- Longer processing times

#### Debrid-Link
- Seedbox integration
- Direct download URLs in response
- OAuth2 authentication
- Video file filtering

## Migration Guide

### For Developers

If you're using the old `rd_client.py`:

**Before:**
```python
from app.services.rd_client import RealDebridClient

rd_client = RealDebridClient(user.rd_api_token)
result = rd_client.add_magnet(magnet_link)
```

**After:**
```python
from app.services.debrid import get_debrid_client

debrid_client = get_debrid_client(
    user.debrid_provider,
    user.debrid_api_token or user.rd_api_token  # fallback to legacy
)
result = debrid_client.add_magnet(magnet_link)
```

### For API Consumers

The API is backwards compatible. Old RD endpoints still work:
- `POST /api/auth/rd-token` → Saved as Real-Debrid
- `GET /api/auth/rd-token/test` → Tests RD token
- Legacy `rd_api_token` field still returned in responses

## Benefits

### For Users
- **Choice**: Pick the provider that works best for you
- **Flexibility**: Switch providers anytime
- **Cost**: Compare prices and features
- **Availability**: If one provider is down, use another
- **Geographic**: Choose provider with servers near you

### For Developers
- **Unified Interface**: Same code for all providers
- **Easy Extension**: Add new providers easily
- **Type Safety**: Strong typing with enums
- **Error Handling**: Consistent error handling
- **Testing**: Mock any provider for testing

## Future Enhancements

Potential future additions:
- [ ] Multi-provider support per user (multiple tokens)
- [ ] Automatic provider failover
- [ ] Provider performance metrics
- [ ] Cost comparison in UI
- [ ] Cache availability comparison
- [ ] Additional providers (TorBox, etc.)

## Support

If you encounter issues with a specific provider:

1. **Test your token** via `/api/auth/debrid-token/test`
2. **Check provider status** on their website
3. **Verify API token** in provider dashboard
4. **Check logs** in Bridgarr backend
5. **Report issues** on GitHub with provider name

## Credits

- **Real-Debrid** - https://real-debrid.com
- **AllDebrid** - https://alldebrid.com
- **Premiumize** - https://premiumize.me
- **Debrid-Link** - https://debrid-link.fr

---

**Version**: 1.0.1
**Release Date**: 2025-10-17
**Status**: Production Ready ✅

Enjoy your new provider options! 🎉
