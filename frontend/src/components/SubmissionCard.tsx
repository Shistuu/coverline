import { useState } from 'react'
import { api, money, type Submission } from '../api'

export function SubmissionCard({
  sub,
  onChange,
  underwriter,
}: {
  sub: Submission
  onChange: (s: Submission) => void
  underwriter?: boolean
}) {
  const [note, setNote] = useState('')
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function run(fn: () => Promise<Submission>) {
    setError(null)
    try {
      onChange(await fn())
    } catch (err) {
      setError((err as Error).message)
    }
  }

  function review(action: 'approve' | 'decline') {
    const premium_cents = price ? Math.round(Number(price) * 100) : undefined
    return run(() => api.review(sub.id, { underwriter: name, action, note, premium_cents }))
  }

  return (
    <article className="card">
      <header className="row">
        <h3>
          #{sub.id} {sub.business_name} <small>({sub.state})</small>
        </h3>
        <span className={`badge ${sub.status}`}>{sub.status}</span>
      </header>
      <p>
        Revenue {money(sub.annual_revenue * 100)} · {sub.seats} seats · {sub.liquor_pct}% alcohol ·{' '}
        {sub.years_in_business} yrs · {sub.prior_claims} claims
      </p>
      <p>
        <strong>Annual premium: {money(sub.premium_cents)}</strong>
      </p>

      <details>
        <summary>Decision log ({sub.decisions.length})</summary>
        <ul className="log">
          {sub.decisions.map((d, i) => (
            <li key={i}>
              <code>{d.rule}</code> → {d.outcome} by {d.actor}: {d.reason}
            </li>
          ))}
        </ul>
      </details>

      {sub.status === 'quoted' && !underwriter && (
        <button onClick={() => run(() => api.bind(sub.id))}>Bind policy</button>
      )}

      {sub.status === 'referred' && underwriter && (
        <div className="review">
          <input placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} />
          <input
            placeholder={`Premium $ (default ${money(sub.premium_cents)})`}
            type="number"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
          <textarea placeholder="Note (required)" value={note} onChange={(e) => setNote(e.target.value)} />
          <div className="row">
            <button disabled={!name || !note} onClick={() => review('approve')}>
              Approve
            </button>
            <button className="danger" disabled={!name || !note} onClick={() => review('decline')}>
              Decline
            </button>
          </div>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </article>
  )
}
