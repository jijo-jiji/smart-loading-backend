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
  background-color: var(--color-bg);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--color-border);
}

h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.subtitle {
  color: var(--color-text-muted);
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
  color: var(--color-primary);
  font-weight: 500;
}

input {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--color-border);
  padding: 0.75rem 1rem;
  color: var(--color-text);
  border-radius: 4px;
  font-family: inherit;
  transition: all 0.2s ease;
}

input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.2);
}

.error-msg {
  color: #ff3366;
  font-size: 0.875rem;
  background: rgba(255, 51, 102, 0.1);
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid rgba(255, 51, 102, 0.2);
}
</style>
