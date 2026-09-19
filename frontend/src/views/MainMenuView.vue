<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="page">
    <button class="logout-btn" type="button" @click="logout">Cerrar sesión</button>

    <h1 class="title">ProyectadurIA</h1>

    <div class="slogan-banner">
      Hacemos que defender tus derechos legales sea simple, claro y al alcance de todos.
    </div>

    <p class="greeting" v-if="auth.user">Hola, {{ auth.user.nombre }}</p>

    <h2 class="question">¿Qué deseas hacer?</h2>

    <div class="options-container">
      <RouterLink class="option-card" to="/consulta" aria-label="Realizar una consulta a partir de un texto">
        <span class="option-text">Realizar una consulta<br />a partir de un texto</span>
      </RouterLink>

      <RouterLink class="option-card" to="/peticion" aria-label="Generar una petición de Habeas Data">
        <span class="option-text">Generar una petición<br />de Habeas Data</span>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
}

.logout-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  background: transparent;
  border: 2px solid rgba(255, 253, 247, 0.3);
  color: var(--dusk-cream);
  padding: 8px 18px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  border-color: var(--dusk-yellow);
  color: var(--dusk-yellow);
}

.title {
  color: var(--dusk-yellow);
  font-size: 3.5rem;
  margin-top: 0;
  margin-bottom: 25px;
  font-weight: 800;
  letter-spacing: 2px;
}

.slogan-banner {
  background-color: var(--dusk-yellow);
  color: var(--dusk-plum);
  padding: 16px 45px;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 700;
  max-width: 650px;
  margin-bottom: 20px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.greeting {
  color: var(--dusk-cream);
  opacity: 0.85;
  margin-bottom: 35px;
  font-weight: 500;
}

.question {
  color: var(--dusk-yellow);
  font-size: 2rem;
  margin-bottom: 40px;
  font-weight: 500;
}

.options-container {
  display: flex;
  gap: 40px;
  justify-content: center;
  flex-wrap: wrap;
}

.option-card {
  background-color: var(--dusk-turquoise);
  border: 3px solid var(--dusk-yellow);
  border-radius: 12px;
  padding: 40px 30px;
  width: 280px;
  cursor: pointer;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.option-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 25px rgba(240, 208, 107, 0.2);
  background-color: #4f7276;
  border-color: var(--dusk-cream);
}

.option-text {
  color: var(--dusk-cream);
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.5;
  text-transform: uppercase;
  letter-spacing: 1px;
}
</style>
