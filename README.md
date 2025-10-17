# Bridgarr

**A smart bridge between your media requests and Real-Debrid streaming**

Bridgarr is a self-hosted platform that lets you request movies and TV shows through Jellyseerr, then stream them directly from Real-Debrid's CDN - no massive storage needed, no bandwidth consumed by your server. Think of it as the bridge that connects your media requests to instant, high-quality streaming.

## Why Bridgarr?

Traditional media server setups (Plex/Jellyfin + Sonarr/Radarr) require you to:
- Download and store terabytes of media files
- Proxy streams through your server (eating your bandwidth)
- Wait for downloads to complete before watching
- Manage storage, upgrades, and deletions

**Bridgarr takes a different approach:**
- Store only metadata and streaming URLs (a few MB vs. TB)
- Stream directly from debrid service CDNs (Real-Debrid, AllDebrid, Premiumize, Debrid-Link)
- Zero bandwidth usage on your server
- Instant playback as soon as content is cached

It's perfect if you already have a debrid service account and want a clean, simple interface to request and stream content without managing a traditional media server.

## How It Works

```
You → Jellyseerr (request "Avatar") → Bridgarr → Real-Debrid (cache torrent)
                                         ↓
                                    TMDb (fetch metadata)
                                         ↓
                                    Store: title, poster, RD stream URL
                                         ↓
You ← Click Play ← Bridgarr Web ← Database (just metadata, ~5KB per movie)
      ↓
Stream directly from Real-Debrid CDN (no server bandwidth used!)
```

## Quick Start

### What You Need

- A VPS or home server (1GB RAM is plenty)
- Docker & Docker Compose installed
- A premium account with one of the supported debrid services:
  - [Real-Debrid](https://real-debrid.com) (€3/month)
  - [AllDebrid](https://alldebrid.com) (€3/month)
  - [Premiumize](https://premiumize.me) (~€8/month)
  - [Debrid-Link](https://debrid-link.fr) (€3/month)
- A [TMDb API key](https://www.themoviedb.org/settings/api) (free)
- 15 minutes

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/bridgarr.git
cd bridgarr

# Configure environment
cp bridgarr-backend/.env.example bridgarr-backend/.env
nano bridgarr-backend/.env
# Add your TMDb API key

# Start everything
docker-compose up -d

# Check status
docker-compose ps
```

**Services:**
- Web UI: `http://your-server:3002`
- API: `http://your-server:8000`
- API Docs: `http://your-server:8000/api/docs`

### Setup Jellyseerr Integration

1. **Install Jellyseerr** (if you haven't already):
   ```bash
   docker run -d \
     --name jellyseerr-bridgarr \
     -p 5057:5055 \
     -v /path/to/config:/app/config \
     fallenbagel/jellyseerr:latest
   ```

2. **Configure Jellyseerr:**
   - Open `http://your-server:5057`
   - Create admin account
   - Skip media server setup
   - Add your TMDb account or API key

3. **Connect to Bridgarr:**
   ```bash
   cd /root/bridgarr/scripts
   python3 configure-jellyseerr-webhook.py
   ```
   Enter your Jellyseerr credentials when prompted. The script will automatically configure the webhook.

4. **Start requesting!**
   - Search for a movie in Jellyseerr
   - Click "Request" → Approve
   - Open Bridgarr web UI to see it appear
   - Click "Play" to stream

That's it. No downloads, no waiting for files to finish, no storage management.

## Features

### What's Working (v1.0.1)

- ✅ **Multiple Debrid Providers** - Support for Real-Debrid, AllDebrid, Premiumize, and Debrid-Link
- ✅ **Jellyseerr Webhook Integration** - Automatic content addition on approval
- ✅ **Smart File Selection** - Intelligent torrent file selection, avoiding archives
- ✅ **TMDb Metadata** - Automatic poster, plot, and metadata fetching
- ✅ **Netflix-Style Web UI** - Browse your library with movie posters
- ✅ **Advanced Video Player** - Plyr integration with quality selection and speed control
- ✅ **Multi-User Support** - Each user brings their own debrid service account
- ✅ **Background Tasks** - Auto-refresh streaming URLs before they expire
- ✅ **JWT Authentication** - Secure API access
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile

### What's Coming

- [ ] TV show episode tracking
- [ ] Search within Bridgarr
- [ ] Continue watching section
- [ ] Watchlist management
- [ ] Multiple quality options (4K, 1080p, 720p)
- [ ] Subtitle integration
- [ ] Android TV native app

## Architecture

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Jellyseerr    │────────>│   Bridgarr   │<────────│  Web Browser    │
│   (Requests)    │ Webhook │   Backend    │  REST   │  Management UI  │
└─────────────────┘         │              │  API    │                 │
                            │  • Metadata  │         │  • Dashboard    │
                            │  • RD URLs   │<────────│  • Library      │
                            │  • Auth      │         │  • Settings     │
                            │  • Tasks     │         └─────────────────┘
                            │              │
                            └──────┬───────┘
                                   │
                                   ├─────────────────> You stream from RD CDN
                                   v                   (not from your server!)
                            ┌──────────────┐
                            │ Real-Debrid  │
                            │     API      │
                            └──────────────┘
```

**Tech Stack:**
- Backend: FastAPI, PostgreSQL, Redis, Celery
- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Video: Plyr (advanced HTML5 player)
- Deployment: Docker, Docker Compose

## Configuration

### Backend (.env)

```env
# Application
APP_NAME=Bridgarr
APP_VERSION=1.0.0

# Database (auto-configured in Docker)
DATABASE_URL=postgresql://bridgarr:password@postgres:5432/bridgarr

# Redis (auto-configured in Docker)
REDIS_URL=redis://redis:6379/0

# TMDb API (get your key at https://www.themoviedb.org/settings/api)
TMDB_API_KEY=your_tmdb_api_key_here

# Security (generate a random string)
SECRET_KEY=your-secret-key-here

# Real-Debrid
RD_API_BASE_URL=https://api.real-debrid.com/rest/1.0
RD_LINK_EXPIRY_HOURS=4
```

### User Debrid Service Tokens

Each user adds their own debrid service API token in the web UI:
1. Log in to Bridgarr
2. Click your username → Settings
3. Select your debrid provider (Real-Debrid, AllDebrid, Premiumize, or Debrid-Link)
4. Paste your API token:
   - **Real-Debrid**: https://real-debrid.com/apitoken
   - **AllDebrid**: https://alldebrid.com/apikeys
   - **Premiumize**: https://www.premiumize.me/account
   - **Debrid-Link**: https://debrid-link.fr/webapp/apikey
5. Save

Now when you request content, Bridgarr uses your chosen debrid service to cache and stream.

## Usage

### Requesting Content

1. Open Jellyseerr (`http://your-server:5057`)
2. Search for a movie (e.g., "The Matrix")
3. Click "Request"
4. Approve the request (or enable auto-approval)

### Watching Content

1. Open Bridgarr Web UI (`http://your-server:3002`)
2. You'll see the movie appear in your library
3. Click on the movie poster
4. Click "Play"
5. Stream directly from Real-Debrid's CDN

The streaming URL is valid for 4 hours and automatically refreshes in the background, so you never have broken links.

## Troubleshooting

### "Cannot connect to backend"

```bash
# Check if containers are running
docker-compose ps

# Restart if needed
docker-compose restart
```

### "Requests don't appear in Bridgarr"

1. Check webhook is configured in Jellyseerr (Settings → Notifications → Webhook)
2. Verify webhook URL: `http://your-server:8000/api/webhooks/overseerr`
3. Check backend logs: `docker logs bridgarr-backend --tail 100`
4. Ensure TMDb API key is set in `.env`

### "Cannot stream media"

1. Verify your Real-Debrid token is saved (Settings page)
2. Check your RD account is premium and active
3. Check if media shows as "Available" (green badge in library)

### "Video player shows no audio/subtitles"

This is a codec issue. Real-Debrid provides the raw video file, and your browser needs to support the codec. Try:
- Use Chrome/Edge (better codec support)
- Download the video to play in VLC if streaming doesn't work

## API Reference

Interactive API documentation is available at `http://your-server:8000/api/docs` when the backend is running.

### Key Endpoints

```bash
# Authentication
POST /api/auth/register        # Register new user
POST /api/auth/login           # Login (returns JWT)
POST /api/auth/rd-token        # Save Real-Debrid token

# Library
GET  /api/library/movies       # Get user's movie library
GET  /api/library/shows        # Get user's TV shows
GET  /api/library/stats        # Library statistics

# Media
GET  /api/media/{id}           # Get media details
GET  /api/media/{id}/play      # Get streaming URL

# Webhooks
POST /api/webhooks/overseerr   # Jellyseerr webhook endpoint
```

## FAQ

**Q: Do I need a debrid service account?**
A: Yes, every user needs their own premium account with one of the supported services (Real-Debrid, AllDebrid, Premiumize, or Debrid-Link). Most cost around €3/month.

**Q: Does Bridgarr download files to my server?**
A: No! That's the point. Bridgarr only stores metadata (movie title, poster, RD URL). You stream directly from Real-Debrid's CDN.

**Q: How much storage do I need?**
A: Virtually nothing. The database with 1000 movies is about 5-10MB. Compare that to 1-5GB per movie with traditional setups.

**Q: What happens when the streaming URL expires?**
A: Bridgarr automatically refreshes URLs every 4 hours in the background. You'll never have a broken link.

**Q: Can I use this without Jellyseerr?**
A: Technically yes, but Jellyseerr provides the nice request/approval workflow. You could manually add content via the API, but it's not as user-friendly.

**Q: Does this work with Plex/Jellyfin?**
A: No, Bridgarr replaces your media server. It's a different approach - no local media files, just direct streaming from RD.

**Q: Is this legal?**
A: Bridgarr is just software that organizes metadata and uses Real-Debrid's API. What you do with it is your responsibility. Real-Debrid has terms of service you should read.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[JELLYSEERR_LINKARR_INTEGRATION.md](JELLYSEERR_LINKARR_INTEGRATION.md)** - Detailed Jellyseerr setup
- **[scripts/README.md](scripts/README.md)** - Configuration scripts documentation

## Contributing

This is an open source project. Contributions, issues, and feature requests are welcome!

If you want to contribute:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Credits

- **TMDb** - Movie and TV metadata
- **Real-Debrid** - Torrent caching and CDN infrastructure
- **Jellyseerr** - Request management interface
- **Plyr** - Advanced video player

---

**Current Version:** v1.0.1
**Status:** Production Ready
**Last Updated:** 2025-10-17

Made with ☕ and frustration with traditional media servers eating all my storage and bandwidth.
