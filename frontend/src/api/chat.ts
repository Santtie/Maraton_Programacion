import { apiGet, apiPost } from './client'
import type { ChatMessageResponse, ConversationDetail } from './types'

export function sendMessage(query: string, conversationId?: number | null) {
  return apiPost<ChatMessageResponse>('/api/chat/message/', {
    query,
    conversation_id: conversationId ?? undefined,
  })
}

export function getConversation(id: number) {
  return apiGet<ConversationDetail>(`/api/chat/conversations/${id}/`)
}
