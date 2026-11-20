import { useState } from 'react'
import { api, type Submission, type SubmissionIn } from '../api'

const EMPTY: SubmissionIn = {
  business_name: '',
  state: 'NY',
  annual_revenue: 1_000_000,
  seats: 40,
  liquor_pct: 10,
  years_in_business: 5,
  prior_claims: 0,
}

const NUMBER_FIELDS: { key: keyof SubmissionIn; label: string; min?: number; max?: number }[] = [
  { key: 'annual_revenue', label: 'Annual revenue ($)', min: 1 },
  { key: 'seats', label: 'Seats', min: 0 },
  { key: 'liquor_pct', label: 'Alcohol share of sales (%)', min: 0, max: 100 },
  { key: 'years_in_business', label: 'Years in business', min: 0 },
  { key: 'prior_claims', label: 'Claims in last 3 years', min: 0 },
]

export function SubmitForm({ onCreated }: { onCreated: (s: Submission) => void }) {
  const [form, setForm] = useState<SubmissionIn>(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      onCreated(await api.create(form))
      setForm(EMPTY)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <h2>New restaurant submission</h2>
      <label>
        Business name
        <input
          required
          value={form.business_name}
          onChange={(e) => setForm({ ...form, business_name: e.target.value })}
        />
      </label>
      <label>
        State
        <input
          required
          maxLength={2}
          value={form.state}
          onChange={(e) => setForm({ ...form, state: e.target.value.toUpperCase() })}
        />
      </label>
      {NUMBER_FIELDS.map((f) => (
        <label key={f.key}>
          {f.label}
          <input
            type="number"
            required
            min={f.min}
            max={f.max}
            value={form[f.key]}
            onChange={(e) => setForm({ ...form, [f.key]: Number(e.target.value) })}
          />
        </label>
      ))}
      {error && <p className="error">{error}</p>}
      <button disabled={busy}>{busy ? 'Rating…' : 'Get quote'}</button>
    </form>
  )
}
