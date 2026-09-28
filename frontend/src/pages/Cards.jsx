import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, errorMessage } from '../services/api'

export function AddCard() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ card_type: 'credit', cardholder_name: '', number: '', expiry_month: '', expiry_year: '' })
  const [error, setError] = useState('')
  async function submit(e) { e.preventDefault(); try { await api.post('/api/cards/', { ...form, expiry_month: Number(form.expiry_month), expiry_year: Number(form.expiry_year) }); setForm({ card_type: 'credit', cardholder_name: '', number: '', expiry_month: '', expiry_year: '' }); navigate('/cards') } catch (err) { setError(errorMessage(err)) } }
  return <section className="panel max-w-lg"><h1 className="mb-2 text-2xl font-bold">Add a test card</h1><p className="muted mb-5">Only use published test numbers. Never enter a real card or CVV. We store only the last four digits.</p><form onSubmit={submit} className="space-y-4"><label>Type<select value={form.card_type} onChange={e => setForm({...form,card_type:e.target.value})}><option value="credit">Credit</option><option value="debit">Debit</option></select></label>{[['cardholder_name','Cardholder name','text'], ['number','Test card number (digits only)','text'], ['expiry_month','Expiry month','number'], ['expiry_year','Expiry year','number']].map(([key,label,type]) => <label className="block" key={key}>{label}<input required type={type} autoComplete="off" value={form[key]} onChange={e => setForm({...form,[key]:e.target.value})}/></label>)}{error && <p className="error">{error}</p>}<button>Save masked card</button></form></section>
}

export function SavedCards() {
  const [cards, setCards] = useState([])
  const [error, setError] = useState('')
  async function load() { try { setCards((await api.get('/api/cards/')).data.results) } catch (e) { setError(errorMessage(e)) } }
  useEffect(() => { load() }, [])
  async function remove(id) { if (!window.confirm('Delete this saved card?')) return; try { await api.delete(`/api/cards/${id}/`); load() } catch(e) { setError(errorMessage(e)) } }
  return <section className="panel"><h1 className="mb-5 text-2xl font-bold">Saved cards</h1>{error && <p className="error">{error}</p>}{cards.length === 0 && <p className="muted">No cards saved.</p>}<div className="space-y-3">{cards.map(card => <div key={card.id} className="flex items-center justify-between rounded-lg border p-4"><div><strong>{card.card_brand} · {card.masked_number}</strong><p className="muted">{card.card_type} · {card.cardholder_name} · expires {card.expiry_month}/{card.expiry_year}</p></div><button onClick={() => remove(card.id)} className="bg-red-700">Delete</button></div>)}</div></section>
}