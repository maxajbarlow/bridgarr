import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://YOUR_SERVER_IP:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  register: async (username: string, email: string, password: string) => {
    const response = await api.post('/api/auth/register', {
      username,
      email,
      password,
    })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  storeRdToken: async (rdToken: string) => {
    const response = await api.post('/api/auth/rd-token', {
      rd_api_token: rdToken,
    })
    return response.data
  },
}

// Library API
export const libraryApi = {
  getStats: async () => {
    const response = await api.get('/api/library/stats')
    return response.data
  },

  getMovies: async (page = 1, pageSize = 20) => {
    const response = await api.get('/api/library/movies', {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  getTvShows: async (page = 1, pageSize = 20) => {
    const response = await api.get('/api/library/shows', {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  getRecent: async (limit = 20) => {
    const response = await api.get('/api/library/recent', {
      params: { limit },
    })
    return response.data
  },

  search: async (query: string, page = 1) => {
    const response = await api.get('/api/library/search', {
      params: { q: query, page },
    })
    return response.data
  },
}

// Media API
export const mediaApi = {
  getDetails: async (mediaId: number) => {
    const response = await api.get(`/api/media/${mediaId}`)
    return response.data
  },

  getSeasons: async (mediaId: number) => {
    const response = await api.get(`/api/media/${mediaId}/seasons`)
    return response.data
  },

  getEpisodes: async (mediaId: number, seasonNumber: number) => {
    const response = await api.get(`/api/media/${mediaId}/seasons/${seasonNumber}/episodes`)
    return response.data
  },
}

// System API
export const systemApi = {
  getHealth: async () => {
    const response = await api.get('/health')
    return response.data
  },

  getInfo: async () => {
    const response = await api.get('/')
    return response.data
  },
}
