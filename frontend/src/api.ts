const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type Status = 'quoted' | 'referred' | 'declined' | 'bound'

export interface SubmissionIn {
  business_name: string
  state: string
  annual_revenue: number
  seats: number
  liquor_pct: number
  years_in_business: number
  prior_claims: number
}

export interface Decision {
  actor: string
  outcome: string
  rule: string
  reason: string
  created_at: string
}

export interface Submission extends SubmissionIn {
  id: number
  status: Status
  premium_cents: number | null
  created_at: string
  decisions: Decision[]
}

export interface UnderwriterAction {
  underwriter: string
  action: 'approve' | 'decline'
  note: string
  premium_cents?: number
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body)
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  create: (body: SubmissionIn) =>
    request<Submission>('/submissions', { method: 'POST', body: JSON.stringify(body) }),
  list: (status?: Status) =>
    request<Submission[]>('/submissions' + (status ? `?status=${status}` : '')),
  review: (id: number, body: UnderwriterAction) =>
    request<Submission>(`/submissions/${id}/review`, { method: 'POST', body: JSON.stringify(body) }),
  bind: (id: number) => request<Submission>(`/submissions/${id}/bind`, { method: 'POST' }),
}

export const money = (cents: number | null) =>
  cents == null ? '—' : (cents / 100).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
