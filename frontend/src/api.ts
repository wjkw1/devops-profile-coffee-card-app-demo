const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
const STORAGE_KEY = 'coffee-card-api-key'

export const getApiKey = () => localStorage.getItem(STORAGE_KEY) ?? ''
export const setApiKey = (key: string) => localStorage.setItem(STORAGE_KEY, key)

export const api = (path: string, options?: RequestInit) => {
  const headers = new Headers(options?.headers)
  const apiKey = getApiKey()
  if (apiKey) headers.set('x-api-key', apiKey)
  return fetch(`${API_BASE_URL}${path}`, { ...options, headers })
}
