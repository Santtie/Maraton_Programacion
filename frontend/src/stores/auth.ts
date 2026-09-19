import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import type { User } from '@/api/types'

const ACCESS_KEY = 'proyectaduria_access'
const REFRESH_KEY = 'proyectaduria_refresh'
const USER_KEY = 'proyectaduria_user'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem(ACCESS_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY))
  const user = ref<User | null>(readUser())

  const isAuthenticated = computed(() => !!accessToken.value)

  function readUser(): User | null {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as User
    } catch {
      return null
    }
  }

  function persist(access: string, refresh: string, userData: User) {
    accessToken.value = access
    refreshToken.value = refresh
    user.value = userData
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
  }

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    persist(res.access, res.refresh, res.user)
  }

  async function signup(nombre: string, username: string, password: string) {
    await authApi.signup({ nombre, username, password })
    // El registro no devuelve tokens; encadenamos el login para una sesión inmediata.
    await login(username, password)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return { accessToken, refreshToken, user, isAuthenticated, login, signup, logout }
})
