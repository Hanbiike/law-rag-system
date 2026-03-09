const LAW_RAG_BASE_URL = process.env.LAW_RAG_API_URL ?? 'http://localhost:8000'

export type LawRagMode = 'base' | 'pro' | 'search'
export type LawRagLang = 'ru' | 'kg'

export interface LawRagQueryRequest {
  query: string
  type?: LawRagMode
  lang?: LawRagLang
  previous_response_id?: string | null
}

export interface LawRagDocQueryRequest {
  query: string
  file_url: string
  type?: 'base' | 'pro'
  lang?: LawRagLang
  previous_response_id?: string | null
}

export interface LawRagImageQueryRequest {
  query: string
  image_url: string
  type?: 'base' | 'pro'
  lang?: LawRagLang
  previous_response_id?: string | null
}

export interface LawRagResponse {
  response: string
  response_id: string | null
  mode: string
  lang: string
}

async function post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${LAW_RAG_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
    signal
  })

  if (!res.ok) {
    let detail = 'Ошибка запроса к Law RAG API'
    try {
      const errBody = (await res.json()) as { detail?: string }
      if (errBody.detail) detail = errBody.detail
    } catch {
      // ignore json parse error
    }
    throw new Error(detail)
  }

  return res.json() as Promise<T>
}

export function queryText(
  params: LawRagQueryRequest,
  signal?: AbortSignal
): Promise<LawRagResponse> {
  return post<LawRagResponse>('/v1/query', params, signal)
}

export function queryDoc(
  params: LawRagDocQueryRequest,
  signal?: AbortSignal
): Promise<LawRagResponse> {
  return post<LawRagResponse>('/v1/query/doc', params, signal)
}

export function queryImage(
  params: LawRagImageQueryRequest,
  signal?: AbortSignal
): Promise<LawRagResponse> {
  return post<LawRagResponse>('/v1/query/image', params, signal)
}

// ─── SSE streaming ─────────────────────────────────────────────────────────

export type SSEEvent =
  | { type: 'delta'; content: string }
  | { type: 'done'; response_id: string | null }
  | { type: 'error'; message: string }

async function postStream(
  path: string,
  body: unknown,
  signal?: AbortSignal
): Promise<Response> {
  const res = await fetch(`${LAW_RAG_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
    signal
  })

  if (!res.ok) {
    let detail = 'Ошибка запроса к Law RAG API'
    try {
      const errBody = (await res.json()) as { detail?: string }
      if (errBody.detail) detail = errBody.detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }

  return res
}

async function* parseSSE(
  res: Response,
  signal?: AbortSignal
): AsyncGenerator<SSEEvent> {
  if (!res.body) throw new Error('No response body')
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      if (signal?.aborted) break
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6)) as SSEEvent
          yield event
        } catch {
          // ignore invalid JSON
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export async function* streamQueryText(
  params: LawRagQueryRequest,
  signal?: AbortSignal
): AsyncGenerator<SSEEvent> {
  const res = await postStream('/v1/query/stream', params, signal)
  yield* parseSSE(res, signal)
}

export async function* streamQueryDoc(
  params: LawRagDocQueryRequest,
  signal?: AbortSignal
): AsyncGenerator<SSEEvent> {
  const res = await postStream('/v1/query/doc/stream', params, signal)
  yield* parseSSE(res, signal)
}

export async function* streamQueryImage(
  params: LawRagImageQueryRequest,
  signal?: AbortSignal
): AsyncGenerator<SSEEvent> {
  const res = await postStream('/v1/query/image/stream', params, signal)
  yield* parseSSE(res, signal)
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${LAW_RAG_BASE_URL}/health`, { method: 'GET' })
    if (!res.ok) return false
    const body = (await res.json()) as { status?: string }
    return body.status === 'ok'
  } catch {
    return false
  }
}

/** Detect image URL by extension or mime-like pattern */
const IMAGE_URL_RE = /^https?:\/\/\S+\.(jpe?g|png|gif|webp)(\?.*)?$/i

/** Detect PDF URL */
const PDF_URL_RE = /^https?:\/\/\S+\.pdf(\?.*)?$/i

/** Extract first URL from text that matches a pattern */
function extractUrl(text: string, pattern: RegExp): string | null {
  const words = text.split(/\s+/)
  for (const word of words) {
    if (pattern.test(word.trim())) return word.trim()
  }
  return null
}

export interface DetectedFileUrl {
  type: 'image' | 'doc'
  url: string
  /** query text with the URL removed */
  cleanedQuery: string
}

/** Inspect query text and explicit fileUrl override to detect file attachment type */
export function detectFileAttachment(
  queryText: string,
  explicitFileUrl: string | null | undefined
): DetectedFileUrl | null {
  if (explicitFileUrl) {
    if (IMAGE_URL_RE.test(explicitFileUrl)) {
      return { type: 'image', url: explicitFileUrl, cleanedQuery: queryText }
    }
    if (PDF_URL_RE.test(explicitFileUrl)) {
      return { type: 'doc', url: explicitFileUrl, cleanedQuery: queryText }
    }
    // Unknown extension – treat as doc (the API will validate)
    return { type: 'doc', url: explicitFileUrl, cleanedQuery: queryText }
  }

  const pdfUrl = extractUrl(queryText, PDF_URL_RE)
  if (pdfUrl) {
    return {
      type: 'doc',
      url: pdfUrl,
      cleanedQuery: queryText.replace(pdfUrl, '').replace(/\s{2,}/g, ' ').trim()
    }
  }

  const imageUrl = extractUrl(queryText, IMAGE_URL_RE)
  if (imageUrl) {
    return {
      type: 'image',
      url: imageUrl,
      cleanedQuery: queryText.replace(imageUrl, '').replace(/\s{2,}/g, ' ').trim()
    }
  }

  return null
}

/** Tag embedded in response text to carry response_id back to the client */
export const META_TAG_RE = /<!--LAW_RAG_META:(\{[^}]+\})-->/

export function appendMetaTag(text: string, responseId: string | null): string {
  if (!responseId) return text
  return `${text}\n<!--LAW_RAG_META:{"rid":"${responseId}"}-->`
}

export function extractMetaFromText(text: string): { rid: string | null; cleanText: string } {
  const match = META_TAG_RE.exec(text)
  if (!match) return { rid: null, cleanText: text }
  try {
    const meta = JSON.parse(match[1]) as { rid?: string }
    const cleanText = text.replace(match[0], '').trimEnd()
    return { rid: meta.rid ?? null, cleanText }
  } catch {
    return { rid: null, cleanText: text }
  }
}
