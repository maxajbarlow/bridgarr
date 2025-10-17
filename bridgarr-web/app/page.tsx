'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { libraryApi, authApi } from '@/lib/api'
import Link from 'next/link'
import toast from 'react-hot-toast'

interface Movie {
  id: number
  title: string
  year?: number
  poster_path?: string
  is_available: boolean
  error_message?: string
}

export default function LibraryHome() {
  const router = useRouter()
  const [movies, setMovies] = useState<Movie[]>([])
  const [loading, setLoading] = useState(true)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [showRegister, setShowRegister] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '' })

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      setShowLogin(true)
      setLoading(false)
    } else {
      setIsLoggedIn(true)
      loadLibrary()
    }
  }, [])

  const loadLibrary = async () => {
    setLoading(true)
    try {
      const data = await libraryApi.getMovies(1, 50)
      setMovies(data.items || [])
    } catch (error: any) {
      console.error('Failed to load library:', error)
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.')
        setIsLoggedIn(false)
        setShowLogin(true)
      } else {
        toast.error('Failed to load library')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = await authApi.login(loginForm.username, loginForm.password)
      localStorage.setItem('auth_token', data.access_token)
      setIsLoggedIn(true)
      setShowLogin(false)
      toast.success('Welcome back!')
      loadLibrary()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await authApi.register(registerForm.username, registerForm.email, registerForm.password)
      toast.success('Account created! Please login.')
      setShowRegister(false)
      setShowLogin(true)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    setIsLoggedIn(false)
    setShowLogin(true)
    toast.success('Logged out')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Top Navigation */}
      <nav className="bg-gray-900/90 backdrop-blur-sm border-b border-gray-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-3">
              <span className="text-3xl">🎬</span>
              <span className="text-2xl font-bold text-white">Bridgarr</span>
            </Link>

            {/* Right Menu */}
            {isLoggedIn && (
              <div className="relative">
                <button
                  onClick={() => setShowMenu(!showMenu)}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition"
                >
                  <span className="text-white">Menu</span>
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Dropdown Menu */}
                {showMenu && (
                  <div className="absolute right-0 mt-2 w-56 bg-gray-800 rounded-lg shadow-xl border border-gray-700 overflow-hidden">
                    <Link
                      href="/settings"
                      className="block px-4 py-3 text-white hover:bg-gray-700 transition"
                      onClick={() => setShowMenu(false)}
                    >
                      ⚙️ Settings
                    </Link>
                    <Link
                      href="/library"
                      className="block px-4 py-3 text-white hover:bg-gray-700 transition"
                      onClick={() => setShowMenu(false)}
                    >
                      📁 Browse Library
                    </Link>
                    <a
                      href={`${process.env.NEXT_PUBLIC_API_URL}/api/docs`}
                      target="_blank"
                      className="block px-4 py-3 text-white hover:bg-gray-700 transition"
                      onClick={() => setShowMenu(false)}
                    >
                      📚 API Docs
                    </a>
                    <hr className="border-gray-700" />
                    <button
                      onClick={() => { handleLogout(); setShowMenu(false); }}
                      className="block w-full text-left px-4 py-3 text-red-400 hover:bg-gray-700 transition"
                    >
                      🚪 Logout
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content - Library Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : movies.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📭</div>
            <h2 className="text-2xl font-bold text-white mb-2">Your Library is Empty</h2>
            <p className="text-gray-400 mb-6">Start adding movies through Jellyseerr</p>
            <div className="max-w-md mx-auto bg-gray-800/50 rounded-lg p-6 border border-gray-700">
              <p className="text-sm text-gray-300 mb-3">Quick Setup:</p>
              <ol className="text-sm text-gray-400 text-left space-y-2">
                <li>1. Go to Settings and add your Real-Debrid API token</li>
                <li>2. Configure Jellyseerr webhook in Settings</li>
                <li>3. Request movies through Jellyseerr</li>
                <li>4. Movies will appear here automatically</li>
              </ol>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-white mb-2">My Library</h1>
              <p className="text-gray-400">{movies.length} movies in your collection</p>
            </div>

            {/* Movie Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
              {movies.map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>
          </>
        )}
      </main>

      {/* Login Modal */}
      {showLogin && !isLoggedIn && (
        <Modal onClose={() => {}}>
          <h2 className="text-2xl font-bold text-white mb-6">Welcome to Bridgarr</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
              <input
                type="text"
                value={loginForm.username}
                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => { setShowLogin(false); setShowRegister(true); }}
              className="w-full px-4 py-2 text-gray-400 hover:text-white transition"
            >
              Need an account? Register
            </button>
          </form>
        </Modal>
      )}

      {/* Register Modal */}
      {showRegister && (
        <Modal onClose={() => setShowRegister(false)}>
          <h2 className="text-2xl font-bold text-white mb-6">Create Account</h2>
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
              <input
                type="text"
                value={registerForm.username}
                onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <input
                type="email"
                value={registerForm.email}
                onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
              <input
                type="password"
                value={registerForm.password}
                onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
            >
              Create Account
            </button>
            <button
              type="button"
              onClick={() => { setShowRegister(false); setShowLogin(true); }}
              className="w-full px-4 py-2 text-gray-400 hover:text-white transition"
            >
              Have an account? Login
            </button>
          </form>
        </Modal>
      )}
    </div>
  )
}

function MovieCard({ movie }: { movie: Movie }) {
  const posterUrl = movie.poster_path
    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
    : null

  return (
    <Link
      href={`/media/${movie.id}`}
      className="group relative rounded-lg overflow-hidden bg-gray-800 shadow-lg hover:shadow-2xl transition-all hover:scale-105"
    >
      {/* Poster */}
      <div className="aspect-[2/3] relative bg-gray-700">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={movie.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <span className="text-4xl">🎬</span>
          </div>
        )}

        {/* Status Badge */}
        {movie.is_available ? (
          <div className="absolute top-2 right-2 bg-green-600 text-white text-xs px-2 py-1 rounded-full font-semibold">
            Ready
          </div>
        ) : movie.error_message ? (
          <div className="absolute top-2 right-2 bg-red-600 text-white text-xs px-2 py-1 rounded-full font-semibold">
            Error
          </div>
        ) : (
          <div className="absolute top-2 right-2 bg-yellow-600 text-white text-xs px-2 py-1 rounded-full font-semibold">
            Processing
          </div>
        )}

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <span className="text-white text-4xl">▶</span>
        </div>
      </div>

      {/* Title */}
      <div className="p-3">
        <h3 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-blue-400 transition">
          {movie.title}
        </h3>
        {movie.year && (
          <p className="text-gray-400 text-xs mt-1">{movie.year}</p>
        )}
      </div>
    </Link>
  )
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-xl p-8 max-w-md w-full border border-gray-700 shadow-2xl relative">
        {children}
      </div>
    </div>
  )
}
