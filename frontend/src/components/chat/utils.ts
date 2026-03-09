import { v4 as uuid } from 'uuid'

import type { ChatMessage, Persona } from './interface'

export function generateMessageId(): string {
  return globalThis.crypto?.randomUUID?.() ?? uuid()
}

export function ensureMessageIds(messages: ChatMessage[]): ChatMessage[] {
  return messages.map((message) => ({
    ...message,
    id: message.id ?? generateMessageId(),
    createdAt: message.createdAt ?? new Date().toISOString()
  }))
}

export const DefaultPersona: Persona = {
  id: 'law-rag',
  role: 'system',
  name: 'New Chat',
  prompt: 'Вы — юридический ассистент по законодательству Кыргызской Республики.'
}

export const DefaultPersonas: Persona[] = [DefaultPersona]

export function findLastMessageIndex(messages: ChatMessage[], role: ChatMessage['role']): number {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i]?.role === role) {
      return i
    }
  }
  return -1
}
