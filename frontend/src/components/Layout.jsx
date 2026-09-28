import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [['/', 'Dashboard'], ['/cards', 'Saved cards'], ['/cards/new', 'Add card'], ['/pay', 'Make payment'], ['/transactions', 'Transactions']]
export default function Layout() {
  const { user, logout } = useAuth()
  return <div className="min-h-screen"><header className="bg-ink text-white"><div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5"><Link to="/" className="text-xl font-bold">◈ CardLab <span className="text-xs font-normal text-teal-200">SIMULATION</span></Link><span className="text-sm">{user?.username} · {user?.role} <button onClick={logout} className="ml-3 bg-white/10 text-sm">Log out</button></span></div></header><div className="mx-auto grid max-w-6xl gap-7 px-6 py-8 md:grid-cols-[190px_1fr]"><nav className="flex flex-col gap-1">{[...links, ...(user?.role === 'admin' ? [['/admin', 'Admin dashboard']] : [])].map(([path, label]) => <NavLink key={path} end={path === '/'} to={path} className={({isActive}) => `rounded-lg px-3 py-2 text-sm ${isActive ? 'bg-teal-700 text-white' : 'text-slate-600 hover:bg-white'}`}>{label}</NavLink>)}</nav><main><Outlet /></main></div></div>
}