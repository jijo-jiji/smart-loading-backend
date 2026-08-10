import { useAuthStore } from '../stores/useAuthStore'
import router from '../router'

// Resolved at build time by Vite. Set VITE_API_URL in your .env.production
// for production, or it falls back to the Render URL on non-localhost hosts.
const PROD_URL = 'https://smart-loading-backend.onrender.com'
const LOCAL_URL = 'http://localhost:8005'

function getBaseUrl() {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl) return envUrl
  const h = window.location.hostname
  if (h === 'localhost' || h === '127.0.0.1') return LOCAL_URL
  return PROD_URL
}

const API_URL = getBaseUrl() + '/api/v1'
const API_KEY = 'unikl_demo_secret_2026'

function getHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    'X-API-KEY': API_KEY
  }
  const token = localStorage.getItem('access_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

async function apiFetch(url, options = {}) {
  options.headers = getHeaders()
  const response = await fetch(url, options)
  
  if (response.status === 401) {
    const authStore = useAuthStore()
    authStore.clearAuth()
    router.push('/login')
    throw new Error('Unauthorized')
  }
  if (response.status === 422) {
    const errorData = await response.json()
    const toast = document.createElement('div')
    toast.style.cssText = 'position:fixed;top:20px;right:20px;background:rgba(239,68,68,0.95);color:white;padding:15px 20px;border-radius:8px;z-index:9999;border:1px solid #f87171;font-family:sans-serif;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);'
    toast.innerHTML = `<strong>Validation Error:</strong> ${errorData.detail}`
    document.body.appendChild(toast)
    setTimeout(() => toast.remove(), 6000)
    throw new Error(errorData.detail)
  }

  return response
}

export async function fetchAllPlans() {
  const response = await apiFetch(`${API_URL}/plans`)
  if (!response.ok) throw new Error('Failed to fetch plans')
  return await response.json()
}

export async function fetchStepsForPlan(planId) {
  const response = await apiFetch(`${API_URL}/plans/${planId}/steps`)
  if (!response.ok) throw new Error('Failed to fetch steps')
  return await response.json()
}

export async function pushPlanToSheets(planId) {
  const response = await apiFetch(`${API_URL}/plans/${planId}/push-sheets`, { method: 'POST' })
  if (!response.ok) throw new Error('Failed to push to sheets')
  return await response.json()
}

export async function optimizePlan(payload) {
  const response = await apiFetch(`${API_URL}/optimize`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
  if (!response.ok) {
    if (response.status !== 422) throw new Error('Failed to optimize plan')
  }
  return await response.json()
}
