import { useUserStore } from '@/stores/user'
import request from '@/apis/request'

export interface ExplainPayload {
  text: string
  topic?: string
}

export interface ExplainFromUrlPayload {
  url: string
  topic?: string
}

export interface ExplainResponse {
  record_id: string
  summary_one_line: string
  applicability: string[]
  materials: { items: string[]; source_note: string }
  channels: string[]
  important_dates: string[]
  common_misunderstandings: string[]
  uncovered_points: string[]
  verification_hints: string[]
  model?: string | null
  warnings: string[]
}

/** SSE `partial` 事件里 `data` 的形状（与 ExplainResponse 相同字段，无 record_id） */
export type ExplainPartialPayload = Omit<ExplainResponse, 'record_id'>

export type ExplainStreamStatus = {
  stage?: string
  message?: string
}

export type ExplainStreamCallbacks = {
  onDelta?: (text: string) => void
  /** 服务端在流式过程中解析出的结构化片段，用于前端渐进渲染 */
  onPartial?: (data: ExplainPartialPayload) => void
  onDone?: (result: ExplainResponse) => void
  onError?: (detail: string) => void
  onStatus?: (status: ExplainStreamStatus) => void
}

async function runPolicyExplainSse(
  path: string,
  body: unknown,
  callbacks: ExplainStreamCallbacks,
  options?: { signal?: AbortSignal },
): Promise<void> {
  const baseURL = import.meta.env.VITE_API_BASE_URL
  const token = useUserStore().accessToken
  try {
    const res = await fetch(`${baseURL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal: options?.signal,
    })
    if (!res.ok) {
      let detail = `请求失败（${res.status}）`
      try {
        const j = (await res.json()) as { detail?: unknown }
        if (typeof j.detail === 'string') detail = j.detail
      } catch {
        /* ignore */
      }
      callbacks.onError?.(detail)
      return
    }
    const reader = res.body?.getReader()
    if (!reader) {
      callbacks.onError?.('无法读取响应流')
      return
    }
    const dec = new TextDecoder()
    let buf = ''

    const consumeBlock = (block: string) => {
      for (const line of block.split('\n')) {
        const t = line.trim()
        if (!t.startsWith('data:')) continue
        const raw = t.slice(5).trim()
        let ev: Record<string, unknown>
        try {
          ev = JSON.parse(raw) as Record<string, unknown>
        } catch {
          continue
        }
        const evName = ev.event
        if (evName === 'status') {
          callbacks.onStatus?.({
            stage: typeof ev.stage === 'string' ? ev.stage : undefined,
            message: typeof ev.message === 'string' ? ev.message : undefined,
          })
          continue
        }
        if (evName === 'delta' && typeof ev.text === 'string') callbacks.onDelta?.(ev.text)
        else if (evName === 'partial' && ev.data != null && typeof ev.data === 'object' && !Array.isArray(ev.data)) {
          callbacks.onPartial?.(ev.data as ExplainPartialPayload)
        } else if (evName === 'error' && typeof ev.detail === 'string') {
          callbacks.onError?.(ev.detail)
          return true
        } else if (evName === 'done') {
          const { event: _e, ...rest } = ev
          callbacks.onDone?.(rest as unknown as ExplainResponse)
          return true
        }
      }
      return false
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        buf += dec.decode()
        break
      }
      buf += dec.decode(value, { stream: true })
      let idx: number
      while ((idx = buf.indexOf('\n\n')) >= 0) {
        const block = buf.slice(0, idx)
        buf = buf.slice(idx + 2)
        if (consumeBlock(block)) return
      }
    }
    const tail = buf.trim()
    if (tail && consumeBlock(tail)) return
    callbacks.onError?.('流式响应未正常结束')
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') return
    callbacks.onError?.(e instanceof Error ? e.message : '网络异常')
  }
}

/** POST /policy/explain：SSE，`event` 为 `partial` | `done` | `error`（兼容旧版 `delta`） */
export async function explainPolicyStream(
  data: ExplainPayload,
  callbacks: ExplainStreamCallbacks,
  options?: { signal?: AbortSignal },
): Promise<void> {
  return runPolicyExplainSse('/policy/explain', data, callbacks, options)
}

/** POST /policy/explain-from-url：SSE，额外含 `status` 阶段事件 */
export async function explainPolicyStreamFromUrl(
  data: ExplainFromUrlPayload,
  callbacks: ExplainStreamCallbacks,
  options?: { signal?: AbortSignal },
): Promise<void> {
  return runPolicyExplainSse('/policy/explain-from-url', data, callbacks, options)
}

export interface ExplanationListItem {
  record_id: string
  topic: string
  created_at: string
  summary_one_line: string | null
}

export interface ExplanationListResponse {
  items: ExplanationListItem[]
  total: number
}

export function fetchExplanations(params?: { limit?: number; offset?: number }) {
  return request.get<ExplanationListResponse>('/policy/explanations', params)
}

export interface ExplanationDetailResponse {
  record_id: string
  topic: string
  created_at: string
  input_text: string | null
  result: Omit<ExplainResponse, 'record_id'>
}

export function fetchExplanationDetail(id: string) {
  return request.get<ExplanationDetailResponse>(`/policy/explanations/${id}`)
}
