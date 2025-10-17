# Bridgarr Management Web Interface

Modern web-based management interface for Bridgarr - Real-Debrid Direct Streaming Platform.

## Features

- 📊 **Dashboard** - View library statistics and system status
- 🔐 **Authentication** - Secure login and user management
- 📚 **Library Browser** - Browse movies and TV shows
- 🔗 **Integration Guides** - Step-by-step setup for Overseerr
- ⚙️ **Settings** - Configure Real-Debrid tokens and preferences
- 🎨 **Modern UI** - Built with Next.js 14 and Tailwind CSS

## Quick Start

### Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm start
```

### Docker Deployment

```bash
docker build -t bridgarr-web .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://YOUR_SERVER_IP:8000 bridgarr-web
```

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://YOUR_SERVER_IP:8000
```

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State Management:** Zustand
- **Data Fetching:** SWR
- **Icons:** Heroicons
- **Notifications:** React Hot Toast

## Project Structure

```
bridgarr-web/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Homepage/Dashboard
│   └── globals.css        # Global styles
├── lib/                   # Utilities
│   └── api.ts            # API client functions
├── public/               # Static assets
└── components/           # React components
```

## API Integration

The web interface connects to the Bridgarr backend API:

```typescript
import { authApi, libraryApi, mediaApi } from '@/lib/api'

// Login
const data = await authApi.login(username, password)

// Get library stats
const stats = await libraryApi.getStats()

// Browse movies
const movies = await libraryApi.getMovies(page, pageSize)
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Features Roadmap

- [x] Dashboard with statistics
- [x] User authentication
- [x] Integration guides
- [ ] Library browser with pagination
- [ ] Media detail pages
- [ ] User settings page
- [ ] Real-time updates with WebSockets
- [ ] Dark/light mode toggle
- [ ] Mobile-responsive design

## License

MIT
