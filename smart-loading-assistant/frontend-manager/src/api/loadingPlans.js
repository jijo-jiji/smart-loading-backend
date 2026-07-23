const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const API_KEY = import.meta.env.VITE_API_KEY || 'super_secret_local_key'

function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-API-KEY': API_KEY
  }
}

export async function fetchAllPlans() {
  const response = await fetch(`${API_URL}/plans`, { headers: getHeaders() })
  if (!response.ok) throw new Error('Failed to fetch plans')
  return await response.json()
}

export async function fetchStepsForPlan(planId) {
  const response = await fetch(`${API_URL}/plans/${planId}/steps`, { headers: getHeaders() })
  if (!response.ok) throw new Error('Failed to fetch steps')
  return await response.json()
}

export async function pushPlanToSheets(planId) {
  const response = await fetch(`${API_URL}/plans/${planId}/push-sheets`, { method: 'POST', headers: getHeaders() })
  if (!response.ok) throw new Error('Failed to push to sheets')
  return await response.json()
}
