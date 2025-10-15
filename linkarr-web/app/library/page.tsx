'use client'

import { useEffect, useState } from 'react'
import { libraryApi } from '@/lib/api'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

interface MediaItem {
  id: number
  title: string
  media_type: 'movie' | 'tv'
  year?: number
  poster_path?: string
  overview?: string
  is_available: boolean
  tmdb_id: number
}

export default function LibraryPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'movies' | 'shows'>('movies')
  const [movies, setMovies] = useState<MediaItem[]>([])
  const [shows, setShows] = useState<MediaItem[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const pageSize = 20

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      toast.error('Please login to view library')
      router.push('/')
      return
    }
    loadLibrary()
  }, [activeTab, page])

  const loadLibrary = async () => {
    setLoading(true)
    try {
      if (activeTab === 'movies') {
        const data = await libraryApi.getMovies(page, pageSize)
        setMovies(data.items || [])
        setTotalPages(Math.ceil((data.total || 0) / pageSize))
      } else {
        const data = await libraryApi.getShows(page, pageSize)
        setShows(data.items || [])
        setTotalPages(Math.ceil((data.total || 0) / pageSize))
      }
    } catch (error: any) {
      console.error('Failed to load library:', error)
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.')
        router.push('/')
      } else {
        toast.error('Failed to load library')
      }
    } finally {
      setLoading(false)
    }
  }

  const items = activeTab === 'movies' ? movies : shows

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <Link href="/" className="text-blue-400 hover:text-blue-300 mb-2 inline-block">
                ← Back to Dashboard
              </Link>
              <h1 className="text-4xl font-bold text-white">Library</h1>
              <p className="text-gray-400 mt-1">Browse your media collection</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Tabs */}
        <div className="flex space-x-4 mb-8">
          <button
            onClick={() => { setActiveTab('movies'); setPage(1); }}
            className={`px-6 py-3 rounded-lg font-semibold transition ${
              activeTab === 'movies'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            Movies
          </button>
          <button
            onClick={() => { setActiveTab('shows'); setPage(1); }}
            className={`px-6 py-3 rounded-lg font-semibold transition ${
              activeTab === 'shows'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            TV Shows
          </button>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            <p className="text-gray-400 mt-4">Loading library...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-400 text-xl">No {activeTab} in your library yet</p>
            <p className="text-gray-500 mt-2">Start by requesting content through Overseerr</p>
          </div>
        ) : (
          <>
            {/* Media Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {items.map((item) => (
                <MediaCard key={item.id} item={item} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center space-x-4 mt-12">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700"
                >
                  Previous
                </button>
                <span className="text-white">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

function MediaCard({ item }: { item: MediaItem }) {
  const posterUrl = item.poster_path
    ? `https://image.tmdb.org/t/p/w500${item.poster_path}`
    : '/placeholder-poster.png'

  return (
    <Link href={`/media/${item.id}`}>
      <div className="group cursor-pointer">
        <div className="relative aspect-[2/3] bg-gray-800 rounded-lg overflow-hidden">
          <img
            src={posterUrl}
            alt={item.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="300"%3E%3Crect fill="%23374151" width="200" height="300"/%3E%3Ctext fill="%239CA3AF" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Poster%3C/text%3E%3C/svg%3E'
            }}
          />
          {!item.is_available && (
            <div className="absolute top-2 right-2 bg-yellow-600 text-white text-xs px-2 py-1 rounded">
              Processing
            </div>
          )}
          {item.is_available && (
            <div className="absolute top-2 right-2 bg-green-600 text-white text-xs px-2 py-1 rounded">
              Available
            </div>
          )}
        </div>
        <div className="mt-2">
          <h3 className="text-white font-semibold truncate group-hover:text-blue-400 transition">
            {item.title}
          </h3>
          {item.year && (
            <p className="text-gray-400 text-sm">{item.year}</p>
          )}
        </div>
      </div>
    </Link>
  )
}
