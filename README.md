# Linkarr - v0.1.0-build.3

**Real-Debrid Direct Streaming Platform**

Linkarr is a lightweight alternative to traditional media server setups (Jellyfin/Plex + Riven). Instead of proxying streams through your VPS and consuming bandwidth, Linkarr stores only metadata and Real-Debrid URLs, allowing clients to stream directly from Real-Debrid's CDN.

## Architecture Overview

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Overseerr     │────────>│   Linkarr    │<────────│  Android TV     │
│   (Requests)    │ Webhook │   Backend    │  REST   │    Client       │
└─────────────────┘         │              │  API    │                 │
                            │  • Metadata  │         │  • ExoPlayer    │
                            │  • RD URLs   │         │  • Compose TV   │
                            │  • Auth      │         │  • Direct CDN   │
                            │              │         │    Streaming    │
                            └──────┬───────┘         └─────────────────┘
                                   │
                                   v
                            ┌──────────────┐
                            │ Real-Debrid  │
                            │     API      │
                            └──────────────┘
```

## Key Features

- **Zero Bandwidth Usage**: Clients stream directly from Real-Debrid CDN
- **Minimal Storage**: Only metadata and URLs stored (no media files)
- **Overseerr Integration**: Automatic content addition via webhooks
- **Real-Debrid Integration**: Torrent caching and direct streaming links
- **Android TV Native**: Optimized for 10-foot UI experience
- **Multi-User Support**: Each user brings their own Real-Debrid account
- **Auto Link Refresh**: Background tasks keep streaming URLs valid

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Metadata and user database
- **Redis** - Caching and task queue
- **Celery** - Background task processing
- **SQLAlchemy** - ORM for database operations
- **Docker** - Containerized deployment

### Android TV Client
- **Kotlin** - Primary programming language
- **Jetpack Compose for TV** - Modern declarative UI
- **ExoPlayer** - Advanced media playback
- **Retrofit** - REST API client
- **Coil** - Image loading

## Project Structure

```
linkarr/
├── linkarr-backend/         # FastAPI backend server
│   ├── app/
│   │   ├── api/             # REST API endpoints
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   └── tasks/           # Celery background tasks
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
├── linkarr-android/         # Android TV client
│   ├── app/
│   │   └── src/main/
│   │       ├── java/com/linkarr/
│   │       │   ├── data/    # API clients, repositories
│   │       │   ├── domain/  # Business models
│   │       │   └── ui/      # Compose screens
│   │       └── res/         # Resources
│   └── build.gradle.kts
└── docs/                    # Documentation
```

## Quick Start

### Backend Setup

```bash
cd linkarr-backend
docker-compose up -d
```

The backend will be available at `http://localhost:8000`

### Android TV Setup

1. Build the APK:
```bash
cd linkarr-android
./gradlew assembleRelease
```

2. Install on Android TV:
```bash
adb install -r app/build/outputs/apk/release/app-release.apk
```

3. Configure backend URL in app settings

## Configuration

### Backend Environment Variables

```env
# Database
DATABASE_URL=postgresql://linkarr:password@postgres:5432/linkarr

# Redis
REDIS_URL=redis://redis:6379/0

# Real-Debrid
RD_API_BASE_URL=https://api.real-debrid.com/rest/1.0

# TMDb
TMDB_API_KEY=your_tmdb_api_key

# Security
SECRET_KEY=your-secret-key-here
```

### Required External Services

1. **Overseerr** - Content request management
2. **Real-Debrid Account** - Each user needs their own account
3. **TMDb API Key** - For metadata enrichment

## How It Works

1. **Content Request**: User requests content via Overseerr
2. **Webhook Trigger**: Overseerr sends webhook to Linkarr on approval
3. **Torrent Search**: Linkarr searches for best torrent via indexers
4. **RD Caching**: Torrent added to Real-Debrid for caching
5. **Metadata Fetch**: TMDb metadata fetched and stored
6. **URL Generation**: Direct streaming URLs generated via RD API
7. **Client Streaming**: Android TV client fetches URL and streams directly from RD CDN

## Database Schema

### Core Tables

- **users** - User accounts with RD API tokens
- **media_items** - Movies/Shows metadata
- **seasons** - TV season information
- **episodes** - Individual episode data
- **rd_torrents** - Real-Debrid torrent tracking
- **rd_links** - Cached streaming URLs with expiration

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/rd-token` - Save Real-Debrid API token

### Media
- `GET /api/media` - List all media
- `GET /api/media/{id}` - Get media details
- `GET /api/media/{id}/play` - Get streaming URL

### Library
- `GET /api/library/movies` - User's movie library
- `GET /api/library/shows` - User's TV shows library

### Webhooks
- `POST /api/webhooks/overseerr` - Overseerr webhook handler

## Background Tasks

- **Link Refresh**: Refresh expiring RD URLs (every 4 hours)
- **Torrent Status Check**: Monitor torrent caching progress
- **Metadata Update**: Sync latest metadata from TMDb

## Development Roadmap

### v0.1.0 (Current) - MVP
- [x] Project structure
- [x] Backend API implementation (Authentication, Media, Library, Webhooks)
- [x] Database models and migrations
- [x] Real-Debrid client integration
- [x] TMDb metadata manager
- [x] Overseerr webhook handler
- [x] Content manager service layer
- [x] Link cache manager with auto-refresh
- [x] Celery background tasks (link refresh, torrent monitoring)
- [x] Android TV project structure
- [x] Android TV data layer (API client, repositories, ViewModels)
- [x] Android TV UI screens (Login, Home, Detail)
- [ ] Android TV Player screen
- [ ] ExoPlayer integration

### v0.2.0 - Enhanced Features
- [ ] Search functionality
- [ ] Continue watching
- [ ] Watchlist management
- [ ] Multiple quality options

### v0.3.0 - Advanced Features
- [ ] Subtitle support
- [ ] Intro/outro skip detection
- [ ] Multiple user profiles
- [ ] Watch together feature

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **Automation Avenue** - Initial inspiration and setup guidance
- **Overseerr** - Content request management
- **Real-Debrid** - Torrent caching and CDN infrastructure
- **TMDb** - Movie and TV show metadata

---

**Current Build**: v0.1.0-build.3
**Last Updated**: 2025-10-14

**Implementation Status**:
- ✅ Backend Core: Complete
- ✅ API Endpoints: Complete
- ✅ Service Layer: Complete
- ✅ Background Tasks: Complete
- ✅ Database Migrations: Setup Complete
- ✅ Android TV Client: Data Layer Complete
- 🚧 Android TV Client: Video Player In Progress
