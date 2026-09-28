import { createContext, useContext, useState } from 'react'
import { api, clearTokens, getRefreshToken, setTokens } from '../services/api'

const AuthContext = createContext(null)
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  async function login(username, password) {
    const { data } = await api.post('/api/auth/login/', { username, password })
    setTokens(data.access, data.refresh)
    try { setUser((await api.get('/api/auth/me/')).data) }
    catch (error) { clearTokens(); throw error }
  }
  async function logout() {
    try { if (getRefreshToken()) await api.post('/api/auth/logout/', { refresh: getRefreshToken() }) }
    finally { clearTokens(); setUser(null) }
  }
  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}
export const useAuth = () => useContext(AuthContext)