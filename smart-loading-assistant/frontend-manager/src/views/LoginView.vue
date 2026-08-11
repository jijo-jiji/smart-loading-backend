<template>
  <div class="login-container">
    <div class="login-card glass-panel">
      <h2>Operator Portal</h2>
      <p class="subtitle">Enter credentials to access the 3D manifest engine.</p>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label>Operator ID</label>
          <input type="text" v-model="username" required placeholder="admin" />
        </div>
        
        <div class="form-group">
          <label>Authorization Code</label>
          <input type="password" v-model="password" required placeholder="password123" />
        </div>
        
        <div v-if="errorMsg" class="error-msg">
          {{ errorMsg }}
        </div>
        
        <button type="submit" :disabled="isLoading" class="btn-primary">
          {{ isLoading ? 'Authenticating...' : 'Authenticate' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/useAuthStore'

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const isLoading = ref(false)

const authStore = useAuthStore()
const router = useRouter()

async function handleLogin() {
  errorMsg.value = ''
  isLoading.value = true
  
  try {
    await authStore.login(username.value, password.value)
    router.push('/manager')
  } catch (err) {
    errorMsg.value = err.message || 'Authentication failed'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg);
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 2.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin: 1rem;
}

h2 {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--primary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.875rem;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--primary);
  font-weight: 700;
}

input {
  background: var(--surface-2);
  border: 1px solid var(--border);
  padding: 0.75rem 1rem;
  color: var(--text);
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  outline: none;
}

input:focus {
  border-color: var(--primary-border);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.error-msg {
  color: var(--danger);
  font-size: 0.875rem;
  background: var(--danger-light);
  padding: 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--danger-border);
}

button[type="submit"] {
  padding: 0.875rem;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}
button[type="submit"]:hover:not(:disabled) {
  filter: brightness(1.12);
  transform: translateY(-1px);
}
button[type="submit"]:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
