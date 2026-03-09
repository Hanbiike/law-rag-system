import { buildMessageContentFromParts, getTextFromParts } from '@/components/chat/chat-attachments'
import type { ChatMessage, MessageContent } from '@/components/chat/interface'
import { findLastMessageIndex } from '@/components/chat/utils'
import type { LawRagLang, LawRagMode } from '@/services/law-rag'
import { DefaultChatTransport } from 'ai'

type HistoryTurn = { role: 'user' | 'assistant'; text: string }

type ChatRequestBody = {
  input: MessageContent
  lrMode: LawRagMode
  lrLang: LawRagLang
  lrPreviousResponseId: string | null
  lrFileUrl: string | null
  /** Conversation history for modes that don't support previous_response_id (e.g. search) */
  lrHistory: HistoryTurn[]
}

export function createChatTransport() {
  return new DefaultChatTransport<ChatMessage>({
    api: '/api/chat',
    prepareSendMessagesRequest: ({ messages, body, headers }) => {
      const lastUserIndex = findLastMessageIndex(messages, 'user')
      const inputMessage = lastUserIndex >= 0 ? messages[lastUserIndex] : undefined

      // Collect up to 5 previous turns (user + assistant) for context accumulation
      const historyMessages = lastUserIndex > 0 ? messages.slice(0, lastUserIndex) : []
      const lrHistory: HistoryTurn[] = historyMessages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .slice(-10) // max 5 pairs = 10 messages
        .map((m) => ({
          role: m.role as 'user' | 'assistant',
          text: getTextFromParts(m.parts ?? []).trim()
        }))
        .filter((m) => m.text.length > 0)

      const payload: ChatRequestBody = {
        input: inputMessage ? buildMessageContentFromParts(inputMessage.parts ?? []) : '',
        lrMode: (body?.lrMode as LawRagMode) ?? 'base',
        lrLang: (body?.lrLang as LawRagLang) ?? 'ru',
        lrPreviousResponseId: (body?.lrPreviousResponseId as string | null) ?? null,
        lrFileUrl: (body?.lrFileUrl as string | null) ?? null,
        lrHistory
      }

      return {
        headers: {
          ...headers,
          Accept: 'text/event-stream'
        },
        body: payload
      }
    }
  })
}
