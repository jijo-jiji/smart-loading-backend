import { defineStore } from 'pinia'
import { ref } from 'vue'

const PROD_URL = 'https://smart-loading-backend.onrender.com'
const LOCAL_URL = 'http://localhost:8005'

function getBaseUrl() {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl) return envUrl
  const h = window.location.hostname
  if (h === 'localhost' || h === '127.0.0.1') return LOCAL_URL
  return PROD_URL
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || null)
  const username = ref(localStorage.getItem('username') || null)

  function setAuth(newToken, newUsername) {
    token.value = newToken
    username.value = newUsername
    localStorage.setItem('access_token', newToken)
    localStorage.setItem('username', newUsername)
  }

  function clearAuth() {
    token.value = null
    username.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
  }

  async function login(usernameInput, passwordInput) {
    const formData = new URLSearchParams()
    formData.append('username', usernameInput)
    formData.append('password', passwordInput)

    const baseUrl = getBaseUrl()
    const response = await fetch(`${baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: formData
    })

    if (!response.ok) {
      throw new Error('Invalid credentials')
    }

    const data = await response.json()
    setAuth(data.access_token, usernameInput)
    return true
  }

  return { token, username, setAuth, clearAuth, login }
})
