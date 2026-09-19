<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { sendMessage } from '@/api/chat'
import type { ChatMessage } from '@/api/types'
import { formatMessageHtml } from '@/utils/formatMessage'

const auth = useAuthStore()

const messages = ref<ChatMessage[]>([])
const conversationId = ref<number | null>(null)
const draft = ref('')
const sending = ref(false)
const error = ref('')
const scrollArea = ref<HTMLElement | null>(null)

async function scrollToBottom() {
  await nextTick()
  scrollArea.value?.scrollTo({ top: scrollArea.value.scrollHeight, behavior: 'smooth' })
}

async function handleSend() {
  const query = draft.value
  if (!query.trim() || sending.value) return

  error.value = ''
  const userMessage: ChatMessage = {
    id: Date.now(),
    role: 'user',
    content: query,
    citations: [],
    out_of_domain: false,
    created_at: new Date().toISOString(),
  }
  messages.value.push(userMessage)
  draft.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const res = await sendMessage(query, conversationId.value)
    conversationId.value = res.conversation_id
    messages.value.push(res.message)
  } catch {
    error.value = 'No se pudo obtener respuesta. Intenta de nuevo en un momento.'
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="page">
    <div class="app-container">
      <aside class="sidebar">
        <h1 class="logo">ProyectadurIA</h1>

        <div class="instructions">
          <h3>Instrucciones</h3>
          <p>• Escribe tu situación con tus propias palabras, en lenguaje natural.</p>
          <p>
            • Recibes un resumen legal, la norma aplicable citada y pasos concretos a seguir,
            en el ámbito de Derechos Fundamentales, Protección de Datos e Intimidad.
          </p>
          <p>• Si tu consulta no pertenece a este dominio, la IA te lo indicará en vez de inventar una respuesta.</p>
        </div>

        <RouterLink class="back-link" to="/">← Volver al menú</RouterLink>

        <div class="user-profile" v-if="auth.user">
          <div class="user-avatar">
            <svg viewBox="0 0 24 24">
              <path
                d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
              />
            </svg>
          </div>
          <span class="user-name">{{ auth.user.nombre }}</span>
        </div>
      </aside>

      <main class="chat-area">
        <h2 class="chat-title">Describe tu problema</h2>

        <div class="messages" ref="scrollArea">
          <p v-if="messages.length === 0" class="empty-state">
            Escribe tu caso abajo para empezar. Por ejemplo: "Le pedí a mi banco que me muestre
            mis datos y no me han respondido."
          </p>

          <div
            v-for="m in messages"
            :key="m.id"
            class="message"
            :class="[m.role, { 'out-of-domain': m.out_of_domain }]"
          >
            <div class="bubble" v-html="formatMessageHtml(m.content)"></div>
            <ul class="citations" v-if="m.citations.length">
              <li v-for="(c, i) in m.citations" :key="i">
                <strong>{{ c.norma }}, {{ c.articulo }}</strong>
                <a v-if="c.url" :href="c.url" target="_blank" rel="noopener">ver fuente</a>
              </li>
            </ul>
          </div>

          <div v-if="sending" class="message assistant">
            <div class="bubble loading">Pensando...</div>
          </div>
        </div>

        <p v-if="error" class="error-text" role="alert">{{ error }}</p>

        <div class="input-container">
          <textarea
            class="chat-input"
            placeholder="Cuéntanos tu situación aquí..."
            v-model="draft"
            :disabled="sending"
            @keydown="handleKeydown"
          ></textarea>
          <button class="send-btn" type="button" :disabled="sending || !draft.trim()" @click="handleSend">
            Enviar
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.app-container {
  background-color: var(--dusk-plum);
  width: 100%;
  max-width: 1100px;
  height: 85vh;
  min-height: 600px;
  border-radius: 24px;
  display: flex;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 253, 247, 0.1);
  overflow: hidden;
}

.sidebar {
  flex: 1;
  padding: 50px 40px;
  display: flex;
  flex-direction: column;
  border-right: 2px solid rgba(240, 208, 107, 0.2);
}

.logo {
  color: var(--dusk-yellow);
  font-size: 2.4rem;
  font-weight: 800;
  margin-bottom: 40px;
  letter-spacing: 1px;
}

.instructions h3 {
  color: var(--dusk-orange);
  font-size: 1.3rem;
  margin-bottom: 16px;
  font-weight: 700;
}

.instructions p {
  color: var(--dusk-cream);
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 14px;
  opacity: 0.9;
}

.back-link {
  color: var(--dusk-yellow);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  margin-top: 20px;
}

.user-profile {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50px;
  width: fit-content;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background-color: var(--dusk-cream);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar svg {
  width: 20px;
  height: 20px;
  fill: var(--dusk-plum);
}

.user-name {
  color: var(--dusk-cream);
  font-weight: 600;
  font-size: 1rem;
}

.chat-area {
  flex: 1.3;
  padding: 40px 50px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, rgba(80, 30, 49, 1) 0%, rgba(65, 23, 39, 1) 100%);
  min-width: 0;
}

.chat-title {
  color: var(--dusk-yellow);
  font-size: 1.7rem;
  font-weight: 700;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 6px;
  margin-bottom: 16px;
}

.empty-state {
  color: var(--dusk-cream);
  opacity: 0.7;
  font-size: 0.95rem;
  font-style: italic;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  align-items: flex-end;
}

.message.assistant {
  align-self: flex-start;
  align-items: flex-start;
}

.bubble {
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 0.95rem;
  line-height: 1.5;
}

.message.user .bubble {
  background-color: var(--dusk-yellow);
  color: var(--dusk-plum);
  border-bottom-right-radius: 4px;
}

.message.assistant .bubble {
  background-color: rgba(255, 253, 247, 0.08);
  color: var(--dusk-cream);
  border-bottom-left-radius: 4px;
  border: 1px solid rgba(255, 253, 247, 0.12);
}

.message.out-of-domain .bubble {
  border-color: var(--dusk-orange);
  background-color: rgba(217, 90, 64, 0.12);
}

.bubble.loading {
  opacity: 0.7;
  font-style: italic;
}

.citations {
  list-style: none;
  padding: 0;
  margin: 6px 4px 0;
  font-size: 0.78rem;
  color: var(--dusk-yellow);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.citations a {
  margin-left: 8px;
  color: var(--dusk-turquoise);
  text-decoration: underline;
}

.error-text {
  color: var(--dusk-orange);
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.input-container {
  position: relative;
  width: 100%;
  flex-shrink: 0;
}

.chat-input {
  width: 100%;
  height: 110px;
  background-color: var(--dusk-yellow);
  border: 4px solid var(--dusk-orange);
  border-radius: 20px;
  padding: 20px 120px 20px 20px;
  font-family: 'Montserrat', sans-serif;
  font-size: 1.05rem;
  color: var(--dusk-plum);
  resize: none;
  outline: none;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.chat-input::placeholder {
  color: rgba(80, 30, 49, 0.6);
  font-weight: 500;
}

.chat-input:focus {
  border-color: var(--dusk-cream);
  box-shadow: 0 15px 30px rgba(240, 208, 107, 0.3);
}

.chat-input:disabled {
  opacity: 0.7;
}

.send-btn {
  position: absolute;
  bottom: 18px;
  right: 18px;
  background-color: var(--dusk-plum);
  color: var(--dusk-yellow);
  border: none;
  border-radius: 50px;
  padding: 10px 25px;
  font-weight: 700;
  font-size: 1rem;
  transition: all 0.2s ease;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  background-color: var(--dusk-plum-dark);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .app-container {
    flex-direction: column;
    height: auto;
  }
  .sidebar {
    border-right: none;
    border-bottom: 2px solid rgba(240, 208, 107, 0.2);
  }
}
</style>
