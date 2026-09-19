<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api/client'

const nombre = ref('')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function handleSubmit() {
  error.value = ''
  if (!nombre.value.trim() || !username.value.trim() || !password.value.trim()) {
    error.value = 'Completa todos los campos.'
    return
  }
  if (password.value.length < 8) {
    error.value = 'La contraseña debe tener al menos 8 caracteres.'
    return
  }
  loading.value = true
  try {
    await auth.signup(nombre.value.trim(), username.value.trim(), password.value)
    router.push('/')
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'No se pudo conectar con el servidor.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card">
      <div class="avatar-container">
        <div class="avatar">
          <svg viewBox="0 0 24 24">
            <path
              d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
            />
          </svg>
        </div>
      </div>

      <h2>Crea tu cuenta en ProyectadurIA</h2>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="nombre">Nombre</label>
          <input id="nombre" v-model="nombre" type="text" placeholder="ej. Juan Pérez" autocomplete="name" />
        </div>

        <div class="form-group">
          <label for="usuario">Usuario</label>
          <input id="usuario" v-model="username" type="text" placeholder="ej. juanperez123" autocomplete="username" />
        </div>

        <div class="form-group">
          <label for="password">Contraseña</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="mínimo 8 caracteres"
            autocomplete="new-password"
          />
        </div>

        <p v-if="error" class="error-text" role="alert">{{ error }}</p>

        <div class="btn-container">
          <button type="submit" class="btn" :disabled="loading">
            {{ loading ? 'Creando cuenta...' : 'Registrarse' }}
          </button>
        </div>
      </form>

      <p class="switch-link">
        ¿Ya tienes cuenta? <RouterLink to="/login">Inicia sesión</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.card {
  background-color: var(--dusk-cream);
  border-radius: 20px;
  padding: 40px 30px 30px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  position: relative;
  margin-top: 40px;
}

.avatar-container {
  position: absolute;
  top: -45px;
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--dusk-cream);
  border-radius: 50%;
  padding: 8px;
}

.avatar {
  background-color: var(--dusk-red);
  width: 75px;
  height: 75px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar svg {
  width: 40px;
  height: 40px;
  fill: white;
}

h2 {
  text-align: center;
  color: var(--dusk-plum);
  margin-top: 25px;
  margin-bottom: 30px;
  font-size: 22px;
}

.form-group {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 10px;
}

.form-group label {
  flex: 0 0 90px;
  color: var(--dusk-turquoise);
  font-weight: 600;
  font-size: 14px;
}

.form-group input {
  flex: 1;
  min-width: 0;
  padding: 12px 15px;
  border: 2px solid var(--dusk-yellow);
  border-radius: 10px;
  background-color: rgba(240, 208, 107, 0.15);
  font-size: 14px;
  color: var(--dusk-plum);
  outline: none;
  transition: all 0.3s ease;
}

.form-group input:focus {
  border-color: var(--dusk-orange);
  box-shadow: 0 0 8px rgba(217, 90, 64, 0.3);
  background-color: #ffffff;
}

.error-text {
  color: var(--dusk-red);
  font-size: 13px;
  text-align: center;
  margin: -8px 0 12px;
  font-weight: 600;
}

.btn-container {
  text-align: center;
  margin-top: 20px;
}

.btn {
  background: linear-gradient(to right, var(--dusk-red), var(--dusk-orange));
  color: white;
  border: none;
  padding: 12px 40px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.switch-link {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: var(--dusk-plum);
  opacity: 0.8;
}

.switch-link a {
  color: var(--dusk-red);
  font-weight: 700;
  text-decoration: none;
}
</style>
