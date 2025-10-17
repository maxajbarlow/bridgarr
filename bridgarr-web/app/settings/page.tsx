'use client'

import { useEffect, useState } from 'react'
import { authApi } from '@/lib/api'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

interface UserProfile {
  id: number
  username: string
  email: string
  is_active: boolean
  has_rd_token: boolean
  created_at: string
}

export default function SettingsPage() {
  const router = useRouter()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [rdToken, setRdToken] = useState('')
  const [saving, setSaving] = useState(false)
  const [testingRd, setTestingRd] = useState(false)
  const [rdStatus, setRdStatus] = useState<'unknown' | 'valid' | 'invalid'>('unknown')

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      toast.error('Please login to view settings')
      router.push('/')
      return
    }
    loadProfile()
  }, [])

  const loadProfile = async () => {
    setLoading(true)
    try {
      const data = await authApi.getProfile()
      setProfile(data)
      setRdStatus(data.has_rd_token ? 'valid' : 'unknown')
    } catch (error: any) {
      console.error('Failed to load profile:', error)
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.')
        router.push('/')
      } else {
        toast.error('Failed to load profile')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSaveRdToken = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rdToken.trim()) {
      toast.error('Please enter a Real-Debrid API token')
      return
    }

    setSaving(true)
    try {
      await authApi.saveRdToken(rdToken)
      toast.success('Real-Debrid token saved successfully!')
      setRdToken('')
      setRdStatus('valid')
      loadProfile()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save Real-Debrid token')
      setRdStatus('invalid')
    } finally {
      setSaving(false)
    }
  }

  const handleTestRdToken = async () => {
    setTestingRd(true)
    try {
      const result = await authApi.testRdToken()
      if (result.valid) {
        toast.success(`Real-Debrid connected! Account: ${result.username || 'Active'}`)
        setRdStatus('valid')
      } else {
        toast.error('Real-Debrid token is invalid')
        setRdStatus('invalid')
      }
    } catch (error: any) {
      toast.error('Failed to test Real-Debrid connection')
      setRdStatus('invalid')
    } finally {
      setTestingRd(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    )
  }

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
              <h1 className="text-4xl font-bold text-white">Settings</h1>
              <p className="text-gray-400 mt-1">Manage your account and preferences</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Profile Section */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Profile Information</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-gray-400">Username</label>
              <p className="text-white text-lg">{profile?.username}</p>
            </div>
            <div>
              <label className="text-sm text-gray-400">Email</label>
              <p className="text-white text-lg">{profile?.email}</p>
            </div>
            <div>
              <label className="text-sm text-gray-400">Account Status</label>
              <p className="text-white text-lg">
                {profile?.is_active ? (
                  <span className="text-green-400">● Active</span>
                ) : (
                  <span className="text-red-400">● Inactive</span>
                )}
              </p>
            </div>
            <div>
              <label className="text-sm text-gray-400">Member Since</label>
              <p className="text-white text-lg">
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Real-Debrid Section */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Real-Debrid Configuration</h2>
              <p className="text-gray-400 mt-1">Connect your Real-Debrid account for streaming</p>
            </div>
            {rdStatus === 'valid' && (
              <span className="text-green-400 text-sm">● Connected</span>
            )}
          </div>

          <div className="space-y-6">
            {/* RD Token Status */}
            {profile?.has_rd_token && (
              <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-green-400 font-semibold">Real-Debrid Token Configured</p>
                    <p className="text-gray-400 text-sm mt-1">Your account is connected to Real-Debrid</p>
                  </div>
                  <button
                    onClick={handleTestRdToken}
                    disabled={testingRd}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:opacity-50 transition"
                  >
                    {testingRd ? 'Testing...' : 'Test Connection'}
                  </button>
                </div>
              </div>
            )}

            {/* RD Token Form */}
            <form onSubmit={handleSaveRdToken} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {profile?.has_rd_token ? 'Update' : 'Add'} Real-Debrid API Token
                </label>
                <input
                  type="password"
                  value={rdToken}
                  onChange={(e) => setRdToken(e.target.value)}
                  placeholder="Enter your Real-Debrid API token"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-gray-400 text-sm mt-2">
                  Get your API token from{' '}
                  <a
                    href="https://real-debrid.com/apitoken"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300"
                  >
                    Real-Debrid API Token Page
                  </a>
                </p>
              </div>

              <button
                type="submit"
                disabled={saving || !rdToken.trim()}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {saving ? 'Saving...' : profile?.has_rd_token ? 'Update Token' : 'Save Token'}
              </button>
            </form>

            {/* Instructions */}
            <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
              <h3 className="text-blue-400 font-semibold mb-2">How to get your Real-Debrid API Token</h3>
              <ol className="text-gray-300 text-sm space-y-2 list-decimal list-inside">
                <li>Visit <a href="https://real-debrid.com/apitoken" target="_blank" className="text-blue-400">real-debrid.com/apitoken</a></li>
                <li>Login to your Real-Debrid account</li>
                <li>Copy the API token shown on the page</li>
                <li>Paste it in the field above and click "Save Token"</li>
              </ol>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
