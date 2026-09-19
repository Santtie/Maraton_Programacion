export interface User {
  id: number
  username: string
  nombre: string
  email: string
  date_joined: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface Citation {
  norma: string
  articulo: string
  fuente: string
  url: string
  texto: string
  score: number
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  out_of_domain: boolean
  created_at: string
}

export interface ChatMessageResponse {
  conversation_id: number
  message: ChatMessage
}

export interface Conversation {
  id: number
  titulo: string
  created_at: string
  updated_at: string
  ultimo_mensaje: string | null
}

export interface ConversationDetail {
  id: number
  titulo: string
  created_at: string
  updated_at: string
  messages: ChatMessage[]
}

export type CampoTipo = 'text' | 'textarea' | 'choice' | 'email'

export interface CampoConfig {
  name: string
  label: string
  type: CampoTipo
  required: boolean
  choices?: string[]
}

export interface TipoHabeasDataConfig {
  label: string
  descripcion: string
  plazo_legal: string
  articulos_fundamento: string[]
  campos_extra: CampoConfig[]
}

export interface TiposResponse {
  campos_comunes: CampoConfig[]
  tipos: Record<string, TipoHabeasDataConfig>
}

export interface HabeasDataRequestResult {
  id: number
  tipo: string
  tipo_label: string
  campos: Record<string, string>
  texto_generado: string
  pdf: string
  created_at: string
}
