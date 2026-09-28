import { useEffect, useState } from 'react'
import { api, errorMessage, paymentsApi } from '../services/api'

export default function Payment() {
  const [cards, setCards] = useState([])
  const [cardId, setCardId] = useState('')
  const [amount, setAmount] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [key, setKey] = useState(() => crypto.randomUUID())
  useEffect(() => { api.get('/api/cards/').then(({data}) => setCards(data.results)).catch(e => setError(errorMessage(e))) }, [])
  async function submit(e) {
    e.preventDefault(); setError(''); setResult(null); setBusy(true)
    try { const {data} = await paymentsApi.post('/payments', { card_id: Number(cardId), amount, currency: 'USD' }, { headers: {'Idempotency-Key': key} }); setResult(data); setKey(crypto.randomUUID()) }
    catch(err) { setError(errorMessage(err)) }
    finally { setBusy(false) }
  }
  return <section className="panel max-w-lg"><h1 className="text-2xl font-bold">Make a simulated payment</h1><p className="muted mb-6">USD 0.01–1000.00 succeeds; higher amounts decline. No real funds move.</p><form onSubmit={submit} className="space-y-4"><label className="block">Saved card<select required value={cardId} onChange={e => {setCardId(e.target.value); setKey(crypto.randomUUID())}}><option value="">Select a card</option>{cards.map(card => <option key={card.id} value={card.id}>{card.card_brand} {card.masked_number}</option>)}</select></label><label className="block">Amount (USD)<input type="number" required min="0.01" step="0.01" value={amount} onChange={e => {setAmount(e.target.value); setKey(crypto.randomUUID())}} /></label>{error && <p className="error">{error}</p>}{result && <p role="status" className={`rounded-lg p-3 ${result.status === 'SUCCESS' ? 'bg-green-50 text-green-800' : 'bg-amber-50 text-amber-800'}`}>{result.status} · ${result.amount} · Reference {result.reference}</p>}<button disabled={!cards.length || busy}>{busy ? 'Processing…' : 'Submit payment'}</button></form></section>
}