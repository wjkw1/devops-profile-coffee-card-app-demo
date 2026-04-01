const BASE_URL = import.meta.env.VITE_API_BASE_URL

export const api = (path: string, options?: RequestInit) => fetch(`${BASE_URL}${path}`, options)
