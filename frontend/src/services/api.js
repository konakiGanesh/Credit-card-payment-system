import axios from 'axios'

const django = axios.create({ baseURL: import.meta.env.VITE_DJANGO_URL || 'http://localhost:8000' })
const payment = axios.create({ baseURL: import.meta.env.VITE_PAYMENT_URL || 'http://localhost:8001' })
let accessToken = null
let refreshToken = null
let refreshInFlight = null
export function setTokens(access, refresh) { accessToken = access; refreshToken = refresh }
export function clearTokens() { accessToken = null; refreshToken = null }
export function getRefreshToken() { return refreshToken }
async function authorize(config) {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
}
django.interceptors.request.use(authorize)
payment.interceptors.request.use(authorize)
async function refreshAccess() {
  if (!refreshInFlight) {
    refreshInFlight = axios.post(`${django.defaults.baseURL}/api/auth/token/refresh/`, { refresh: refreshToken })
      .then(({ data }) => { accessToken = data.access; if (data.refresh) refreshToken = data.refresh })
      .catch((error) => { clearTokens(); throw error })
      .finally(() => { refreshInFlight = null })
  }
  return refreshInFlight
}
for (const client of [django, payment]) client.interceptors.response.use(response => response, async error => {
  const original = error.config
  if (error.response?.status === 401 && refreshToken && original && !original._retried) {
    original._retried = true
    await refreshAccess()
    original.headers.Authorization = `Bearer ${accessToken}`
    return client(original)
  }
  throw error
})
export const api = django
export const paymentsApi = payment
export function errorMessage(error) {
  const data = error.response?.data
  if (!data) return 'Service unavailable. Please try again.'
  if (typeof data.detail === 'string') return data.detail
  const first = Object.entries(data).find(([, value]) => value)
  return first ? `${first[0]}: ${Array.isArray(first[1]) ? first[1].join(', ') : JSON.stringify(first[1])}` : 'Request failed.'
}