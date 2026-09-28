import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api, errorMessage } from '../services/api'

export default function Dashboard() {
  const { user } = useAuth()
  const [cards, setCards] = useState(null)
  const [transactions, setTransactions] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { Promise.all([api.get('/api/cards/'), api.get('/api/transactions/')]).then(([a,b]) => { setCards(a.data); setTransactions(b.data) }).catch(e => setError(errorMessage(e))) }, [])
  const recent = transactions?.results || []
  const success = recent.filter(t => t.status === 'SUCCESS').reduce((sum,t) => sum + Number(t.amount), 0)
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold">Welcome, {user?.username}</h1><p className="muted mt-1">Your payment simulation overview · {user?.email}</p></div>{error && <p className="error">{error}</p>}<div className="grid gap-4 sm:grid-cols-3">{[['Saved cards', cards?.count ?? '—'], ['Transactions', transactions?.count ?? '—'], ['Successful on this page', `$${success.toFixed(2)}`]].map(([label,value]) => <div className="panel" key={label}><p className="muted">{label}</p><p className="mt-2 text-3xl font-bold">{value}</p></div>)}</div><section className="panel"><div className="flex justify-between"><h2 className="text-lg font-semibold">Recent activity</h2><Link className="text-teal-700" to="/transactions">View all →</Link></div><div className="mt-4 space-y-3">{recent.slice(0,5).map(t => <div className="flex justify-between border-t pt-3" key={t.reference}><span>Card •••• {t.card_last_four} <small className="muted">{t.status}</small></span><strong>${t.amount}</strong></div>)}{recent.length === 0 && <p className="muted">No transactions yet. Add a test card to get started.</p>}</div></section></div>
}