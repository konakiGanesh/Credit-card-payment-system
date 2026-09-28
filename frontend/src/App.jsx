import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { AuthProvider, useAuth } from './context/AuthContext'
import Admin from './pages/Admin'
import { AuthPage } from './pages/Auth'
import { AddCard, SavedCards } from './pages/Cards'
import Dashboard from './pages/Dashboard'
import Payment from './pages/Payment'
import Transactions from './pages/Transactions'

function Protected({ children, admin = false }) { const { user } = useAuth(); return !user ? <Navigate to="/login" replace/> : admin && user.role !== 'admin' ? <Navigate to="/" replace/> : children }
export default function App() { return <AuthProvider><BrowserRouter><Routes><Route path="/login" element={<AuthPage/>}/><Route path="/register" element={<AuthPage register/>}/><Route element={<Protected><Layout/></Protected>}><Route index element={<Dashboard/>}/><Route path="cards" element={<SavedCards/>}/><Route path="cards/new" element={<AddCard/>}/><Route path="pay" element={<Payment/>}/><Route path="transactions" element={<Transactions/>}/><Route path="admin" element={<Protected admin><Admin/></Protected>}/></Route><Route path="*" element={<Navigate to="/" replace/>}/></Routes></BrowserRouter></AuthProvider> }