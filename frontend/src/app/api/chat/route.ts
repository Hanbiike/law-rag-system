import type { NextRequest } from 'next/server'
import {
  createUIMessageStream,
  createUIMessageStreamResponse
} from 'ai'
import {
  detectFileAttachment,
  streamQueryDoc,
  streamQueryImage,
  streamQueryText,
  type LawRagLang,
  type LawRagMode
} from '@/services/law-rag'

export const runtime = 'edge'

// ─── Input types ────────────────────────────────────────────────────────────

type InputPart =
  | { type: 'text'; text: string }
  | { type: 'file'; mediaType: string; url: string }
  | { type: 'data-document'; data: { name: string; content: string; mimeType: string } }

type InputContent = string | InputPart[]

interface RequestBody {
  input: InputContent
  /** Law RAG mode: base | pro | search */
  lrMode?: LawRagMode
  /** Response language */
  lrLang?: LawRagLang
  /** Previous response ID for conversation continuity */
  lrPreviousResponseId?: string | null
  /** Explicit file URL (PDF or image) provided by the user */
  lrFileUrl?: string | null
  /** Conversation history turns for manual context accumulation (used in search mode) */
  lrHistory?: Array<{ role: 'user' | 'assistant'; text: string }>
}

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Extract plain text and any embedded document context from InputContent */
function extractQueryInfo(input: InputContent): {
  text: string
  documentContext: string
} {
  if (typeof input === 'string') {
    return { text: input, documentContext: '' }
  }

  let text = ''
  let documentContext = ''

  for (const part of input) {
    if (part.type === 'text') {
      text += (text ? ' ' : '') + part.text
    } else if (part.type === 'data-document') {
      // Include parsed document content as context in the query
      documentContext +=
        `\n\n[Документ: ${part.data.name}]\n` + part.data.content.slice(0, 8000)
    }
  }

  return { text, documentContext }
}

/** Strip invisible LAW_RAG_META comment from assistant text */
function stripMeta(text: string): string {
  return text.replace(/\n?<!--LAW_RAG_META:[^>]*-->/g, '').trim()
}

/**
 * Build a context-enriched query from conversation history.
 * Used for modes that don't support previous_response_id (e.g. search).
 */
function buildQueryWithHistory(
  currentQuery: string,
  history: Array<{ role: 'user' | 'assistant'; text: string }>
): string {
  if (history.length === 0) return currentQuery

  const lines: string[] = ['[История диалога]']
  for (const turn of history) {
    const label = turn.role === 'user' ? 'Пользователь' : 'Ассистент'
    // Truncate very long turns to keep the query size reasonable
    const text = stripMeta(turn.text).slice(0, 600)
    lines.push(`${label}: ${text}`)
  }
  lines.push('[Текущий вопрос]', currentQuery)
  return lines.join('\n')
}

// ─── Handler ────────────────────────────────────────────────────────────────

export async function POST(req: NextRequest): Promise<Response> {
  try {
    const body = (await req.json()) as RequestBody

    const mode: LawRagMode = body.lrMode ?? 'base'
    const lang: LawRagLang = body.lrLang ?? 'ru'
    const previousResponseId = body.lrPreviousResponseId ?? null
    const explicitFileUrl = body.lrFileUrl ?? null
    const history = body.lrHistory ?? []

    const { text, documentContext } = extractQueryInfo(body.input ?? '')

    // Build the final query (prepend document context when present)
    const baseQuery = text.trim()
    const queryWithDoc = documentContext ? `${baseQuery}\n${documentContext}` : baseQuery

    // For search mode (no previous_response_id support), manually inject history as context
    const fullQuery =
      mode === 'search' && history.length > 0
        ? buildQueryWithHistory(queryWithDoc, history)
        : queryWithDoc

    if (!fullQuery) {
      return new Response(
        JSON.stringify({ error: 'Пустой запрос' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Detect whether the user is referencing a file URL
    const fileAttachment = detectFileAttachment(baseQuery, explicitFileUrl)

    // Construct request signal: abort on client disconnect or after 60s timeout
    const controller = new AbortController()
    req.signal.addEventListener('abort', () => controller.abort(), { once: true })
    const timeoutId = setTimeout(() => controller.abort(), 60_000)

    // For search mode: context comes from manually injected history in fullQuery,
    // so previous_response_id must be null to avoid double-counting.
    const effectivePrevId = mode === 'search' ? null : previousResponseId

    const stream = createUIMessageStream({
      execute: async ({ writer }) => {
        const textId = crypto.randomUUID()
        writer.write({ type: 'text-start', id: textId })

        try {
          let eventStream: AsyncGenerator<import('@/services/law-rag').SSEEvent>

          if (fileAttachment?.type === 'image') {
            eventStream = streamQueryImage(
              {
                query: fileAttachment.cleanedQuery || fullQuery,
                image_url: fileAttachment.url,
                type: mode === 'search' ? 'base' : mode,
                lang,
                previous_response_id: effectivePrevId
              },
              controller.signal
            )
          } else if (fileAttachment?.type === 'doc') {
            eventStream = streamQueryDoc(
              {
                query: fileAttachment.cleanedQuery || fullQuery,
                file_url: fileAttachment.url,
                type: mode === 'search' ? 'base' : mode,
                lang,
                previous_response_id: effectivePrevId
              },
              controller.signal
            )
          } else {
            eventStream = streamQueryText(
              {
                query: fullQuery,
                type: mode,
                lang,
                previous_response_id: effectivePrevId
              },
              controller.signal
            )
          }

          let gotDone = false

          for await (const event of eventStream) {
            if (event.type === 'delta') {
              writer.write({ type: 'text-delta', id: textId, delta: event.content })
            } else if (event.type === 'done') {
              gotDone = true
              // Embed response_id as invisible meta tag so the client can extract it
              if (event.response_id) {
                const meta = `\n<!--LAW_RAG_META:{"rid":"${event.response_id}"}-->`
                writer.write({ type: 'text-delta', id: textId, delta: meta })
              }
            } else if (event.type === 'error') {
              writer.write({ type: 'text-delta', id: textId, delta: event.message })
            }
          }

          if (!gotDone) {
            writer.write({
              type: 'text-delta',
              id: textId,
              delta: '\nСоединение прервано. Попробуйте ещё раз.'
            })
          }
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Неизвестная ошибка'

          const isTimeout =
            err instanceof Error &&
            (err.name === 'AbortError' || message.toLowerCase().includes('timeout'))

          const userMessage = isTimeout
            ? 'Запрос занял слишком много времени. Попробуйте режим base.'
            : message.startsWith('Не удалось')
              ? message
              : `Сервер недоступен. Проверьте подключение. (${message})`

          writer.write({ type: 'text-delta', id: textId, delta: userMessage })
        } finally {
          writer.write({ type: 'text-end', id: textId })
          clearTimeout(timeoutId)
        }
      }
    })

    return createUIMessageStreamResponse({ stream })
  } catch (error) {
    console.error('[Law RAG API] Error:', error)
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown error'
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
