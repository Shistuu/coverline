import { useCallback, useEffect, useState } from 'react'
import { api, type Submission } from './api'
import { SubmissionCard } from './components/SubmissionCard'
import { SubmitForm } from './components/SubmitForm'

type Tab = 'broker' | 'underwriter'

export default function App() {
  const [tab, setTab] = useState<Tab>('broker')
  const [subs, setSubs] = useState<Submission[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setSubs(await api.list(tab === 'underwriter' ? 'referred' : undefined))
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [tab])

  useEffect(() => {
    load()
  }, [load])

  return (
    <main>
      <header className="row top">
        <h1>Coverline</h1>
        <nav>
          <button className={tab === 'broker' ? 'active' : ''} onClick={() => setTab('broker')}>
            Broker
          </button>
          <button
            className={tab === 'underwriter' ? 'active' : ''}
            onClick={() => setTab('underwriter')}
          >
            Underwriter queue
          </button>
        </nav>
      </header>

      {error && <p className="error">Can't reach the API ({error}). Is the backend running?</p>}

      <div className={tab === 'broker' ? 'grid' : ''}>
        {tab === 'broker' && <SubmitForm onCreated={load} />}
        <section>
          <h2>{tab === 'broker' ? 'Submissions' : 'Waiting for review'}</h2>
          {subs.length === 0 && <p className="muted">Nothing here yet.</p>}
          {subs.map((s) => (
            <SubmissionCard key={s.id} sub={s} onChange={load} underwriter={tab === 'underwriter'} />
          ))}
        </section>
      </div>
    </main>
  )
}
