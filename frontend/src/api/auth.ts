import { apiGet, apiPost } from './client'
import type { LoginResponse, User } from './types'

export function signup(payload: { nombre: string; username: string; password: string }) {
  return apiPost<User>('/api/auth/signup/', payload, false)
}

export function login(payload: { username: string; password: string }) {
  return apiPost<LoginResponse>('/api/auth/login/', payload, false)
}

export function me() {
  return apiGet<User>('/api/auth/me/')
}
