const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(status: number, data: unknown, message: string) {
    super(message)
    this.status = status
    this.data = data
  }
}

function getAccessToken(): string | null {
  return localStorage.getItem('proyectaduria_access')
}

interface RequestOptions {
  method?: string
  body?: unknown
  auth?: boolean
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true } = options

  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth) {
    const token = getAccessToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (response.status === 204) return undefined as T

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : undefined

  if (!response.ok) {
    const message = extractErrorMessage(data) || `Error ${response.status}`
    throw new ApiError(response.status, data, message)
  }

  return data as T
}

function extractErrorMessage(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null
  const obj = data as Record<string, unknown>
  if (typeof obj.detail === 'string') return obj.detail
  const firstKey = Object.keys(obj)[0]
  if (firstKey) {
    const value = obj[firstKey]
    if (Array.isArray(value) && typeof value[0] === 'string') return `${firstKey}: ${value[0]}`
    if (typeof value === 'string') return `${firstKey}: ${value}`
  }
  return null
}

export async function apiGet<T>(path: string, auth = true): Promise<T> {
  return request<T>(path, { method: 'GET', auth })
}

export async function apiPost<T>(path: string, body?: unknown, auth = true): Promise<T> {
  return request<T>(path, { method: 'POST', body, auth })
}

export async function apiDelete<T>(path: string, auth = true): Promise<T> {
  return request<T>(path, { method: 'DELETE', auth })
}

/** Descarga un archivo binario (ej. PDF) autenticado, devuelto como Blob. */
export async function apiGetBlob(path: string): Promise<Blob> {
  const token = getAccessToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const response = await fetch(`${API_BASE_URL}${path}`, { headers })
  if (!response.ok) throw new ApiError(response.status, undefined, `Error ${response.status}`)
  return response.blob()
}

export { API_BASE_URL }
