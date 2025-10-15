'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { mediaApi } from '@/lib/api'
import Link from 'next/link'
import toast from 'react-hot-toast'

interface MediaDetails {
  id: number
  title: string
  media_type: 'movie' | 'tv'
  year?: number
  poster_path?: string
  backdrop_path?: string
  overview?: string
  runtime?: number
  genres?: string[]
  rating?: number
  is_available: boolean
  tmdb_id: number
  seasons?: Season[]
  stream_url?: string
}

interface Season {
  id: number
  season_number: number
  name: string
  episode_count: number
  poster_path?: string
  episodes?: Episode[]
}

interface Episode {
  id: number
  episode_number: number
  name: string
  overview?: string
  still_path?: string
  is_available: boolean
  stream_url?: string
}

export default function MediaDetailPage() {
  const params = useParams()
  const router = useRouter()
  const mediaId = params.id as string
  const [media, setMedia] = useState<MediaDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedSeason, setSelectedSeason] = useState<number>(1)
  const [loadingEpisodes, setLoadingEpisodes] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      toast.error('Please login to view media details')
      router.push('/')
      return
    }
    loadMediaDetails()
  }, [mediaId])

  const loadMediaDetails = async () => {
    setLoading(true)
    try {
      const data = await mediaApi.getDetails(parseInt(mediaId))
      setMedia(data)
      if (data.media_type === 'tv' && data.seasons && data.seasons.length > 0) {
        setSelectedSeason(data.seasons[0].season_number)
      }
    } catch (error: any) {
      console.error('Failed to load media details:', error)
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.')
        router.push('/')
      } else if (error.response?.status === 404) {
        toast.error('Media not found')
        router.push('/library')
      } else {
        toast.error('Failed to load media details')
      }
    } finally {
      setLoading(false)
    }
  }

  const handlePlay = async () => {
    if (!media) return

    try {
      const data = await mediaApi.getStreamUrl(media.id)
      if (data.stream_url) {
        window.open(data.stream_url, '_blank')
      } else {
        toast.error('Stream URL not available yet. Content may still be processing.')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to get stream URL')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (!media) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
        <p className="text-gray-400">Media not found</p>
      </div>
    )
  }

  const backdropUrl = media.backdrop_path
    ? `https://image.tmdb.org/t/p/original${media.backdrop_path}`
    : null
  const posterUrl = media.poster_path
    ? `https://image.tmdb.org/t/p/w500${media.poster_path}`
    : null

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Backdrop */}
      {backdropUrl && (
        <div className="relative h-[50vh] overflow-hidden">
          <img
            src={backdropUrl}
            alt={media.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/80 to-transparent" />
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-32 relative z-10">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row gap-8 mb-12">
          {/* Poster */}
          {posterUrl && (
            <div className="flex-shrink-0">
              <img
                src={posterUrl}
                alt={media.title}
                className="w-64 rounded-lg shadow-2xl"
              />
            </div>
          )}

          {/* Info */}
          <div className="flex-1">
            <Link href="/library" className="text-blue-400 hover:text-blue-300 mb-4 inline-block">
              ← Back to Library
            </Link>

            <h1 className="text-5xl font-bold text-white mb-4">
              {media.title}
              {media.year && <span className="text-gray-400 ml-4">({media.year})</span>}
            </h1>

            {/* Meta Info */}
            <div className="flex flex-wrap gap-4 mb-6">
              {media.rating && (
                <span className="text-yellow-400 flex items-center">
                  ⭐ {media.rating.toFixed(1)}/10
                </span>
              )}
              {media.runtime && (
                <span className="text-gray-400">{media.runtime} min</span>
              )}
              {media.genres && media.genres.length > 0 && (
                <span className="text-gray-400">{media.genres.join(', ')}</span>
              )}
            </div>

            {/* Status Badge */}
            <div className="mb-6">
              {media.is_available ? (
                <span className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-full">
                  ● Available
                </span>
              ) : (
                <span className="inline-flex items-center px-4 py-2 bg-yellow-600 text-white rounded-full">
                  ● Processing
                </span>
              )}
            </div>

            {/* Actions */}
            {media.media_type === 'movie' && (
              <div className="flex gap-4 mb-6">
                <button
                  onClick={handlePlay}
                  disabled={!media.is_available}
                  className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2"
                >
                  ▶ Play Movie
                </button>
              </div>
            )}

            {/* Overview */}
            {media.overview && (
              <div>
                <h2 className="text-2xl font-bold text-white mb-3">Overview</h2>
                <p className="text-gray-300 leading-relaxed">{media.overview}</p>
              </div>
            )}
          </div>
        </div>

        {/* TV Show Seasons & Episodes */}
        {media.media_type === 'tv' && media.seasons && media.seasons.length > 0 && (
          <div className="mt-12">
            <h2 className="text-3xl font-bold text-white mb-6">Seasons & Episodes</h2>

            {/* Season Selector */}
            <div className="flex flex-wrap gap-2 mb-6">
              {media.seasons.map((season) => (
                <button
                  key={season.id}
                  onClick={() => setSelectedSeason(season.season_number)}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    selectedSeason === season.season_number
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  Season {season.season_number}
                </button>
              ))}
            </div>

            {/* Episodes List */}
            <div className="space-y-4">
              {media.seasons
                .find((s) => s.season_number === selectedSeason)
                ?.episodes?.map((episode) => (
                  <EpisodeCard
                    key={episode.id}
                    episode={episode}
                    seasonNumber={selectedSeason}
                  />
                )) || (
                <p className="text-gray-400">No episodes available for this season</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function EpisodeCard({ episode, seasonNumber }: { episode: Episode; seasonNumber: number }) {
  const handlePlayEpisode = async () => {
    try {
      const data = await mediaApi.getStreamUrl(episode.id)
      if (data.stream_url) {
        window.open(data.stream_url, '_blank')
      } else {
        toast.error('Stream URL not available yet')
      }
    } catch (error: any) {
      toast.error('Failed to get stream URL')
    }
  }

  const stillUrl = episode.still_path
    ? `https://image.tmdb.org/t/p/w300${episode.still_path}`
    : null

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700 hover:border-blue-500 transition">
      <div className="flex gap-4">
        {/* Episode Still */}
        {stillUrl && (
          <div className="flex-shrink-0 w-40">
            <img
              src={stillUrl}
              alt={episode.name}
              className="w-full rounded-lg"
            />
          </div>
        )}

        {/* Episode Info */}
        <div className="flex-1">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-white font-semibold text-lg">
              {seasonNumber}x{episode.episode_number.toString().padStart(2, '0')} - {episode.name}
            </h3>
            {episode.is_available ? (
              <span className="text-green-400 text-sm">● Available</span>
            ) : (
              <span className="text-yellow-400 text-sm">● Processing</span>
            )}
          </div>
          {episode.overview && (
            <p className="text-gray-400 text-sm mb-3 line-clamp-2">{episode.overview}</p>
          )}
          <button
            onClick={handlePlayEpisode}
            disabled={!episode.is_available}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            ▶ Play Episode
          </button>
        </div>
      </div>
    </div>
  )
}
