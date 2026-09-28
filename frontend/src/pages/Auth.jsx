import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api, errorMessage } from '../services/api'

export function AuthPage({ register = false }) {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  async function submit(event) {
    event.preventDefault(); setError(''); setLoading(true)
    try {
      if (register) { await api.post('/api/auth/register/', form); navigate('/login', { state: { registered: true } }) }
      else { await login(form.username, form.password); navigate('/') }
    } catch (err) { setError(errorMessage(err)) }
    finally { setLoading(false) }
  }
  return <div className="flex min-h-screen items-center justify-center px-4"><div className="panel w-full max-w-md"><div className="mb-5 text-2xl font-bold">◈ CardLab</div><h1 className="mb-1 text-xl font-semibold">{register ? 'Create an account' : 'Welcome back'}</h1><p className="muted mb-6">A safe payment simulation. Never use real card details.</p><form onSubmit={submit} className="space-y-4">{['username', ...(register ? ['email'] : []), 'password'].map(field => <label key={field} className="block text-sm capitalize">{field}<input className="mt-1" type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'} required value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}/></label>)}{error && <p className="error">{error}</p>}<button disabled={loading} className="w-full">{loading ? 'Please wait…' : register ? 'Register' : 'Log in'}</button></form><p className="muted mt-5">{register ? 'Already registered?' : 'New to CardLab?'} <Link className="text-teal-700 underline" to={register ? '/login' : '/register'}>{register ? 'Log in' : 'Create account'}</Link></p></div></div>
}