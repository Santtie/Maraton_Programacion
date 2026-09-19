<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { getTipos, generate, downloadPdf } from '@/api/documents'
import type { CampoConfig, TipoHabeasDataConfig, HabeasDataRequestResult } from '@/api/types'
import { ApiError } from '@/api/client'

const props = defineProps<{ tipo: string }>()

const loadingTipos = ref(true)
const tipoConfig = ref<TipoHabeasDataConfig | null>(null)
const camposConfig = ref<CampoConfig[]>([])
const loadError = ref('')

const values = reactive<Record<string, string>>({})
const submitting = ref(false)
const submitError = ref('')
const result = ref<HabeasDataRequestResult | null>(null)

const allFields = computed(() => camposConfig.value)

onMounted(async () => {
  try {
    const res = await getTipos()
    const cfg = res.tipos[props.tipo]
    if (!cfg) {
      loadError.value = 'Ese tipo de solicitud no existe.'
      return
    }
    tipoConfig.value = cfg
    camposConfig.value = [...res.campos_comunes, ...cfg.campos_extra]
    for (const campo of camposConfig.value) values[campo.name] = ''
  } catch {
    loadError.value = 'No se pudieron cargar los campos del formulario.'
  } finally {
    loadingTipos.value = false
  }
})

function validate(): string | null {
  for (const campo of allFields.value) {
    if (campo.required && !values[campo.name]?.trim()) {
      return `Falta completar: ${campo.label}`
    }
  }
  return null
}

async function handleSubmit() {
  submitError.value = ''
  const validationError = validate()
  if (validationError) {
    submitError.value = validationError
    return
  }
  submitting.value = true
  try {
    result.value = await generate(props.tipo, { ...values })
  } catch (err) {
    submitError.value = err instanceof ApiError ? err.message : 'No se pudo generar el documento.'
  } finally {
    submitting.value = false
  }
}

async function handleDownload() {
  if (!result.value) return
  await downloadPdf(result.value.id, `${result.value.tipo}_habeas_data.pdf`)
}

function startOver() {
  result.value = null
  for (const campo of allFields.value) values[campo.name] = ''
}
</script>

<template>
  <div class="page">
    <RouterLink class="back-link" to="/peticion">← Elegir otro tipo</RouterLink>

    <p v-if="loadingTipos" class="status-text">Cargando formulario...</p>
    <p v-else-if="loadError" class="status-text error">{{ loadError }}</p>

    <template v-else-if="tipoConfig">
      <div class="card" v-if="!result">
        <h1 class="title">{{ tipoConfig.label }}</h1>
        <p class="descripcion">{{ tipoConfig.descripcion }}</p>
        <p class="plazo"><strong>Plazo legal:</strong> {{ tipoConfig.plazo_legal }}</p>

        <form class="form" @submit.prevent="handleSubmit">
          <div class="form-field" v-for="campo in allFields" :key="campo.name">
            <label :for="campo.name">{{ campo.label }}<span v-if="campo.required"> *</span></label>

            <textarea
              v-if="campo.type === 'textarea'"
              :id="campo.name"
              v-model="values[campo.name]"
              rows="3"
            ></textarea>

            <select v-else-if="campo.type === 'choice'" :id="campo.name" v-model="values[campo.name]">
              <option value="" disabled>Selecciona una opción</option>
              <option v-for="opt in campo.choices" :key="opt" :value="opt">{{ opt }}</option>
            </select>

            <input
              v-else
              :id="campo.name"
              :type="campo.type === 'email' ? 'email' : 'text'"
              v-model="values[campo.name]"
            />
          </div>

          <p v-if="submitError" class="error-text" role="alert">{{ submitError }}</p>

          <button type="submit" class="submit-btn" :disabled="submitting">
            {{ submitting ? 'Generando...' : 'Generar solicitud' }}
          </button>
        </form>
      </div>

      <div class="card result-card" v-else>
        <h1 class="title">{{ result.tipo_label }} generada</h1>
        <pre class="documento">{{ result.texto_generado }}</pre>

        <div class="result-actions">
          <button class="submit-btn" type="button" @click="handleDownload">Descargar PDF</button>
          <button class="secondary-btn" type="button" @click="startOver">Generar otra</button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 60px 20px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
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

.status-text {
  color: var(--dusk-cream);
  opacity: 0.85;
  margin-top: 100px;
}

.status-text.error {
  color: var(--dusk-orange);
  font-weight: 600;
}

.card {
  background-color: var(--dusk-cream);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 640px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.title {
  color: var(--dusk-plum);
  font-size: 1.7rem;
  font-weight: 800;
  margin-bottom: 12px;
}

.descripcion {
  color: var(--dusk-turquoise);
  font-weight: 600;
  margin-bottom: 10px;
  line-height: 1.5;
}

.plazo {
  color: var(--dusk-plum);
  font-size: 0.9rem;
  opacity: 0.85;
  margin-bottom: 25px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  color: var(--dusk-plum);
  font-weight: 600;
  font-size: 0.9rem;
}

.form-field input,
.form-field textarea,
.form-field select {
  padding: 12px 15px;
  border: 2px solid var(--dusk-yellow);
  border-radius: 10px;
  background-color: rgba(240, 208, 107, 0.15);
  font-size: 14px;
  color: var(--dusk-plum);
  outline: none;
  font-family: inherit;
  resize: vertical;
  transition: all 0.3s ease;
}

.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  border-color: var(--dusk-orange);
  box-shadow: 0 0 8px rgba(217, 90, 64, 0.3);
  background-color: #ffffff;
}

.error-text {
  color: var(--dusk-red);
  font-weight: 600;
  font-size: 0.9rem;
}

.submit-btn {
  background: linear-gradient(to right, var(--dusk-red), var(--dusk-orange));
  color: white;
  border: none;
  padding: 14px 30px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 700;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.secondary-btn {
  background: transparent;
  color: var(--dusk-plum);
  border: 2px solid var(--dusk-turquoise);
  padding: 12px 28px;
  border-radius: 25px;
  font-weight: 700;
}

.secondary-btn:hover {
  background: rgba(87, 124, 128, 0.1);
}

.result-card {
  max-width: 720px;
}

.documento {
  background: rgba(80, 30, 49, 0.05);
  border: 1px solid rgba(80, 30, 49, 0.15);
  border-radius: 12px;
  padding: 20px;
  color: var(--dusk-plum);
  font-family: 'Montserrat', sans-serif;
  font-size: 0.88rem;
  line-height: 1.6;
  white-space: pre-wrap;
  max-height: 55vh;
  overflow-y: auto;
  margin-bottom: 25px;
}

.result-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
</style>
