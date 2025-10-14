'use client'

import { useEffect, useState } from 'react'
import { systemApi, libraryApi, authApi } from '@/lib/api'
import toast from 'react-hot-toast'

export default function Home() {
  const [systemInfo, setSystemInfo] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '' })
  const [showRegister, setShowRegister] = useState(false)

  useEffect(() => {
    loadSystemInfo()
    checkAuth()
  }, [])

  const loadSystemInfo = async () => {
    try {
      const info = await systemApi.getInfo()
      setSystemInfo(info)
    } catch (error) {
      console.error('Failed to load system info:', error)
    }
  }

  const checkAuth = () => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      setIsLoggedIn(true)
      loadStats()
    }
  }

  const loadStats = async () => {
    try {
      const data = await libraryApi.getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = await authApi.login(loginForm.username, loginForm.password)
      localStorage.setItem('auth_token', data.access_token)
      setIsLoggedIn(true)
      setShowLogin(false)
      toast.success('Login successful!')
      loadStats()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed')
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await authApi.register(registerForm.username, registerForm.email, registerForm.password)
      toast.success('Registration successful! Please login.')
      setShowRegister(false)
      setShowLogin(true)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    setIsLoggedIn(false)
    setStats(null)
    toast.success('Logged out successfully')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-white">Linkarr Management</h1>
              <p className="text-gray-400 mt-1">Real-Debrid Direct Streaming Platform</p>
            </div>
            <div className="flex items-center gap-4">
              {systemInfo && (
                <div className="text-right">
                  <p className="text-sm text-gray-400">Version</p>
                  <p className="text-white font-semibold">{systemInfo.version}</p>
                </div>
              )}
              {isLoggedIn ? (
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
                >
                  Logout
                </button>
              ) : (
                <button
                  onClick={() => setShowLogin(true)}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition"
                >
                  Login
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Stats Grid */}
        {isLoggedIn && stats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-12">
            <StatCard title="Total Movies" value={stats.total_movies} color="blue" />
            <StatCard title="Available Movies" value={stats.available_movies} color="green" />
            <StatCard title="Total Shows" value={stats.total_shows} color="purple" />
            <StatCard title="Available Shows" value={stats.available_shows} color="green" />
            <StatCard title="Total Episodes" value={stats.total_episodes} color="indigo" />
          </div>
        ) : null}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <ActionCard
            title="API Documentation"
            description="View and test all available API endpoints"
            link={`${process.env.NEXT_PUBLIC_API_URL}/api/docs`}
            icon="📚"
          />
          <ActionCard
            title="Overseerr Integration"
            description="Configure webhook to receive media requests"
            link="#overseerr-setup"
            icon="🔗"
          />
          <ActionCard
            title="Real-Debrid Setup"
            description="Configure your Real-Debrid API token"
            link="#rd-setup"
            icon="🎬"
          />
          <ActionCard
            title="Library Browser"
            description="Browse your media library"
            link="/library"
            icon="📁"
          />
          <ActionCard
            title="System Status"
            description="View backend health and services"
            link="/status"
            icon="📊"
          />
          <ActionCard
            title="Settings"
            description="Configure Linkarr settings"
            link="/settings"
            icon="⚙️"
          />
        </div>

        {/* Integration Guide */}
        <div id="overseerr-setup" className="mt-12 bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700">
          <h2 className="text-2xl font-bold text-white mb-4">🔗 Overseerr Integration</h2>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 mb-4">
              Connect Overseerr to automatically add approved media requests to Linkarr.
            </p>
            <ol className="text-gray-300 space-y-3">
              <li>Open Overseerr and go to <strong>Settings → Notifications → Webhook</strong></li>
              <li>Enable the Webhook agent</li>
              <li>Set Webhook URL to: <code className="bg-gray-900 px-2 py-1 rounded text-primary-400">
                {process.env.NEXT_PUBLIC_API_URL}/api/webhooks/overseerr
              </code></li>
              <li>Select notification types: <strong>Media Approved</strong>, <strong>Media Available</strong></li>
              <li>Choose <strong>JSON Payload</strong> format</li>
              <li>Save settings</li>
            </ol>
            <div className="mt-6 p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
              <p className="text-sm text-blue-200 mb-2"><strong>Test the webhook:</strong></p>
              <code className="text-xs text-blue-300">
                curl {process.env.NEXT_PUBLIC_API_URL}/api/webhooks/test
              </code>
            </div>
          </div>
        </div>

        {/* RD Setup Guide */}
        <div id="rd-setup" className="mt-8 bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700">
          <h2 className="text-2xl font-bold text-white mb-4">🎬 Real-Debrid Setup</h2>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 mb-4">
              Configure your Real-Debrid API token to enable streaming.
            </p>
            <ol className="text-gray-300 space-y-3">
              <li>Go to <a href="https://real-debrid.com/apitoken" target="_blank" rel="noopener" className="text-primary-400 hover:text-primary-300">Real-Debrid API Token Page</a></li>
              <li>Copy your API token</li>
              <li>Login to Linkarr and go to Settings</li>
              <li>Paste your RD API token and save</li>
            </ol>
          </div>
        </div>
      </main>

      {/* Login Modal */}
      {showLogin && (
        <Modal onClose={() => setShowLogin(false)}>
          <h2 className="text-2xl font-bold text-white mb-6">Login to Linkarr</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
              <input
                type="text"
                value={loginForm.username}
                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition"
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => { setShowLogin(false); setShowRegister(true); }}
              className="w-full px-4 py-2 text-gray-400 hover:text-white transition"
            >
              Don't have an account? Register
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
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <input
                type="email"
                value={registerForm.email}
                onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
              <input
                type="password"
                value={registerForm.password}
                onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition"
            >
              Create Account
            </button>
            <button
              type="button"
              onClick={() => { setShowRegister(false); setShowLogin(true); }}
              className="w-full px-4 py-2 text-gray-400 hover:text-white transition"
            >
              Already have an account? Login
            </button>
          </form>
        </Modal>
      )}
    </div>
  )
}

function StatCard({ title, value, color }: { title: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: 'from-blue-600 to-blue-800',
    green: 'from-green-600 to-green-800',
    purple: 'from-purple-600 to-purple-800',
    indigo: 'from-indigo-600 to-indigo-800',
  }

  return (
    <div className={`bg-gradient-to-br ${colors[color]} rounded-xl p-6 text-white shadow-lg`}>
      <p className="text-sm opacity-90">{title}</p>
      <p className="text-4xl font-bold mt-2">{value}</p>
    </div>
  )
}

function ActionCard({ title, description, link, icon }: any) {
  return (
    <a
      href={link}
      target={link.startsWith('http') ? '_blank' : undefined}
      rel="noopener noreferrer"
      className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700 hover:border-primary-500 transition group"
    >
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-bold text-white mb-2 group-hover:text-primary-400 transition">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </a>
  )
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-xl p-8 max-w-md w-full border border-gray-700 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          ✕
        </button>
        {children}
      </div>
    </div>
  )
}
