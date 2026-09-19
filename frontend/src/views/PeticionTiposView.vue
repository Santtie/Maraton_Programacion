<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { getTipos } from '@/api/documents'
import type { TiposResponse } from '@/api/types'

const tipos = ref<TiposResponse['tipos']>({})
const loading = ref(true)
const error = ref('')
const router = useRouter()

onMounted(async () => {
  try {
    const res = await getTipos()
    tipos.value = res.tipos
  } catch {
    error.value = 'No se pudieron cargar los tipos de solicitud. Intenta de nuevo.'
  } finally {
    loading.value = false
  }
})

function selectTipo(key: string) {
  router.push(`/peticion/${key}`)
}
</script>

<template>
  <div class="page">
    <RouterLink class="back-link" to="/">← Volver al menú</RouterLink>

    <div class="header-section">
      <h1 class="title">Petición Habeas Data</h1>
      <p class="subtitle">
        Selecciona el tipo de petición o solicitud que deseas realizar, serás redirigido al
        formulario correspondiente.
      </p>
    </div>

    <p v-if="loading" class="status-text">Cargando tipos de solicitud...</p>
    <p v-if="error" class="status-text error">{{ error }}</p>

    <div class="cards-container" v-if="!loading && !error">
      <div
        v-for="(cfg, key) in tipos"
        :key="key"
        class="expandable-card"
        role="button"
        tabindex="0"
        @click="selectTipo(key)"
        @keydown.enter="selectTipo(key)"
      >
        <div class="card-header">
          <span class="card-title">{{ cfg.label }}</span>
          <span class="toggle-icon">▼</span>
        </div>
        <div class="card-content">
          <div class="card-inner">
            <p class="card-description">{{ cfg.descripcion }}</p>
            <button class="action-btn" type="button" @click.stop="selectTipo(key)">Seleccionar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  position: relative;
}

.back-link {
  position: absolute;
  top: 24px;
  left: 24px;
  color: var(--dusk-yellow);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
}

.header-section {
  text-align: center;
  margin-bottom: 50px;
  max-width: 800px;
}

.title {
  color: var(--dusk-yellow);
  font-size: 2.8rem;
  font-weight: 800;
  margin-bottom: 20px;
  letter-spacing: 1px;
}

.subtitle {
  color: var(--dusk-cream);
  font-size: 1.05rem;
  line-height: 1.6;
  font-weight: 500;
  opacity: 0.9;
}

.status-text {
  color: var(--dusk-cream);
  opacity: 0.85;
}

.status-text.error {
  color: var(--dusk-orange);
  font-weight: 600;
}

.cards-container {
  display: flex;
  flex-wrap: wrap;
  gap: 25px;
  justify-content: center;
  max-width: 1200px;
  width: 100%;
}

.expandable-card {
  background-color: var(--dusk-turquoise);
  border: 3px solid var(--dusk-yellow);
  border-radius: 16px;
  width: 220px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  cursor: pointer;
  overflow: hidden;
}

.expandable-card:hover,
.expandable-card:focus-visible {
  width: 260px;
  background-color: #4f7276;
  border-color: var(--dusk-cream);
  transform: translateY(-8px);
  box-shadow: 0 15px 30px rgba(240, 208, 107, 0.25);
  outline: none;
}

.card-header {
  padding: 25px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 130px;
}

.card-title {
  color: var(--dusk-cream);
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.4;
  text-transform: uppercase;
}

.toggle-icon {
  color: var(--dusk-yellow);
  font-size: 1.2rem;
  margin-top: 15px;
  transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.expandable-card:hover .toggle-icon {
  transform: rotate(180deg);
  color: var(--dusk-cream);
}

.card-content {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.expandable-card:hover .card-content,
.expandable-card:focus-visible .card-content {
  grid-template-rows: 1fr;
}

.card-inner {
  overflow: hidden;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.expandable-card:hover .card-inner {
  padding-bottom: 25px;
}

.card-description {
  color: var(--dusk-cream);
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 20px;
  font-weight: 500;
  opacity: 0.9;
}

.action-btn {
  background-color: var(--dusk-orange);
  color: var(--dusk-cream);
  border: none;
  padding: 10px 20px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.9rem;
  width: 100%;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background-color: var(--dusk-red);
}
</style>
