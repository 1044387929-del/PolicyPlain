import request from '@/apis/request'

export interface ExplainPayload {
  text: string
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

export function explainPolicy(data: ExplainPayload) {
  return request.post<ExplainResponse>('/policy/explain', data)
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
