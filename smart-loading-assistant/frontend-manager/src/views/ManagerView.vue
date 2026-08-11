<template>
  <div class="manager-layout" :data-mobile-tab="activeMobileTab">
    <!-- Top Navigation Bar -->
    <header class="top-nav">
      <div class="nav-left">
        <div class="logo">
          <div class="logo-icon">📦</div>
          <span class="logo-text">SmartLoad</span>
          <span class="logo-badge">v4</span>
        </div>
      </div>
      <div class="nav-center">
        <template v-if="store.activePlan">
          <span class="manifest-title">{{ store.activePlan.human_readable_id }}</span>
          <span class="status-badge" :class="statusClass">{{ displayStatus(store.activePlan) }}</span>
        </template>
        <span v-else class="manifest-title muted">Select a Manifest</span>
      </div>
      <div class="nav-right">
        <button class="btn btn-secondary" disabled title="Export PDF (Coming Soon)">
          <span>📄</span> Export PDF
        </button>
        <button 
          class="btn btn-sheets" 
          :disabled="!store.activePlan || sheetsLoading"
          @click="handlePushSheets"
        >
          <span>📊</span> {{ sheetsLoading ? 'Pushing...' : 'Google Sheets' }}
        </button>
        <RouterLink to="/operator" class="btn btn-outline">
          Operator HUD →
        </RouterLink>
      </div>
    </header>

    <!-- Sheets Status Toast -->
    <Transition name="toast">
      <div v-if="sheetsToast" class="sheets-toast" :class="sheetsToast.status">
        {{ sheetsToast.message }}
      </div>
    </Transition>

    <!-- Mobile Tabs (Visible only on < 1024px) -->
    <nav class="mobile-tabs">
      <button :class="{ active: activeMobileTab === 'list' }" @click="activeMobileTab = 'list'">
        Manifests
      </button>
      <button :class="{ active: activeMobileTab === 'stage' }" @click="activeMobileTab = 'stage'" :disabled="!store.activePlan">
        3D View
      </button>
      <button :class="{ active: activeMobileTab === 'kpi' }" @click="activeMobileTab = 'kpi'" :disabled="!store.activePlan">
        KPIs
      </button>
    </nav>

    <div class="flex flex-col md:flex-row flex-1 overflow-hidden">
      
      <!-- API Error Banner -->
      <div v-if="apiErrorBanner" class="absolute top-20 left-1/2 transform -translate-x-1/2 z-50 bg-red-600 text-white px-6 py-4 rounded shadow-2xl">
        <strong>API Error:</strong> {{ apiErrorBanner }}
        <button @click="apiErrorBanner = null" class="ml-4 underline">Dismiss</button>
      </div>

      <!-- Left Sidebar: Manifest Selector -->
      <aside class="left-sidebar">
        <div class="sidebar-header">
          <h2>Manifests</h2>
          <div class="plan-count">{{ store.plans.length }} plans</div>
        </div>
        <div class="search-wrap">
          <input v-model="searchQuery" class="search-input" placeholder="🔍 Search manifests..." />
        </div>
        <div class="plan-list" v-if="!store.isLoading || store.plans.length > 0">
          <div
            v-for="plan in filteredPlans"
            :key="plan.id"
            class="plan-card"
            :class="{ active: store.activePlan?.id === plan.id }"
            @click="onSelectPlan(plan)"
          >
            <div class="plan-card-id">{{ plan.human_readable_id }}</div>
            <div class="plan-card-meta">
              <span class="plan-status-dot" :class="plan.status === 'SUCCESS' ? 'ok' : 'warn'"></span>
              {{ displayStatus(plan) }}
            </div>
            <div class="plan-card-stats">
              <span>{{ ((plan.left_weight_kg || 0) + (plan.right_weight_kg || 0)).toFixed(0) }}kg</span>
              <span class="sep">·</span>
              <span>{{ plan.trucks?.name || plan.cargo_manifests?.name }}</span>
            </div>
          </div>
          <div v-if="filteredPlans.length === 0" class="empty-plans">
            No manifests match "{{ searchQuery }}"
          </div>
        </div>
        <div v-else class="plan-list-loading">
          <div class="spinner"></div>
          <span>Loading plans...</span>
        </div>
        <div class="polling-indicator">
          <div class="pulse-dot"></div>
          <span>Live • polling every 5s</span>
        </div>
      </aside>

      <!-- Main 3D Stage -->
      <main class="stage">
        <div v-if="!store.activePlan" class="stage-empty">
          <div class="stage-empty-icon">🚛</div>
          <h3>Select a Loading Plan</h3>
          <p>Choose a manifest from the left panel to visualize the 3D arrangement.</p>
        </div>
        <template v-else>
          <!-- Phase III.b Execution HUD -->
          <div class="execution-hud">
            <div class="hud-left">
              <label class="hud-label">View Mode</label>
              <select v-model="transStore.viewMode" class="hud-select">
                <option value="density">Density Heatmap</option>
                <option value="material">Material Textures</option>
              </select>
            </div>
          </div>
          
          <TrailerScene />
          <CargoTelemetryPanel />
        </template>
      </main>

      <!-- Right Sidebar: KPIs & Left Behind -->
      <aside class="right-sidebar" v-if="store.activePlan">
        <KpiPanel />
        
        <!-- Advanced Settings & Analytics (Phase 3) -->
        <div class="analytics-container" style="padding: 16px; border-top: 1px solid rgba(148,163,184,0.1);">
          <button 
            @click="showAdvancedSettings = !showAdvancedSettings" 
            style="color: #60a5fa; font-size: 13px; font-weight: 600; background: none; border: none; cursor: pointer; display: flex; align-items: center; gap: 8px; padding: 0;"
          >
            <span>{{ showAdvancedSettings ? '▼' : '▶' }}</span> 
            Advanced Operational Settings
          </button>
          
          <div v-show="showAdvancedSettings" style="margin-top: 12px; display: flex; flex-direction: column; gap: 8px;">
            <label style="font-size: 11px; color: #94a3b8; display: flex; flex-direction: column;">
              Base Handling (sec)
              <input type="number" v-model.number="operationalConfig.base_handling_sec" min="1" style="background: rgba(15,23,42,0.5); border: 1px solid rgba(148,163,184,0.2); color: white; padding: 4px; border-radius: 4px; margin-top: 4px;" />
            </label>
            <label style="font-size: 11px; color: #94a3b8; display: flex; flex-direction: column;">
              Rotation Penalty (sec)
              <input type="number" v-model.number="operationalConfig.rotation_penalty_sec" min="0" style="background: rgba(15,23,42,0.5); border: 1px solid rgba(148,163,184,0.2); color: white; padding: 4px; border-radius: 4px; margin-top: 4px;" />
            </label>
            <label style="font-size: 11px; color: #94a3b8; display: flex; flex-direction: column;">
              Z-Axis Stack Penalty (sec)
              <input type="number" v-model.number="operationalConfig.z_axis_penalty_sec" min="0" style="background: rgba(15,23,42,0.5); border: 1px solid rgba(148,163,184,0.2); color: white; padding: 4px; border-radius: 4px; margin-top: 4px;" />
            </label>
          </div>

          <button 
            @click="calculateEfficiency" 
            :disabled="isOptimizing"
            style="margin-top: 16px; width: 100%; padding: 8px; background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: 600; cursor: pointer;"
          >
            {{ isOptimizing ? 'Calculating...' : 'Calculate Efficiency' }}
          </button>
          
          <button 
            v-if="physicsStore.analytics"
            @click="showOptimizationSummary = true" 
            style="margin-top: 8px; width: 100%; padding: 8px; background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px; font-weight: 600; cursor: pointer;"
          >
            📋 AI Optimization Summary
          </button>

          <div v-if="physicsStore.analytics" style="margin-top: 16px; padding: 12px; background: rgba(30,41,59,0.8); border: 1px solid rgba(148,163,184,0.2); border-radius: 8px; position: relative;">
            <div v-if="physicsStore.isStale" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15,23,42,0.8); backdrop-filter: blur(2px); display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 8px; z-index: 10;">
              <span style="font-size: 24px; margin-bottom: 4px;">⚠️</span>
              <span style="color: #ef4444; font-weight: 700; font-size: 11px; text-transform: uppercase;">Manifest Mutated</span>
              <span style="color: #94a3b8; font-size: 10px;">Recalculate to verify safety</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
              <h4 style="font-size: 12px; color: #cbd5e1; margin: 0; font-weight: 700; text-transform: uppercase;">Projected Efficiency</h4>
              <div :style="{ 
                padding: '2px 6px', 
                borderRadius: '4px', 
                fontSize: '9px', 
                fontWeight: '800',
                background: physicsStore.isSafe ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                color: physicsStore.isSafe ? '#4ade80' : '#ef4444',
                border: physicsStore.isSafe ? '1px solid rgba(34,197,94,0.2)' : '1px solid rgba(239,68,68,0.2)'
              }">
                {{ physicsStore.isSafe ? 'CG SAFE' : 'CG DANGER' }}
              </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 12px;">
              <div>
                <div style="font-size: 10px; color: #94a3b8; text-transform: uppercase;">Loading ETA</div>
                <div style="font-size: 18px; color: #60a5fa; font-family: monospace; font-weight: 700;">{{ formattedETA }}</div>
              </div>
              <div>
                <div style="font-size: 10px; color: #94a3b8; text-transform: uppercase;">Complexity (HCS)</div>
                <div style="font-size: 18px; color: #facc15; font-family: monospace; font-weight: 700;">{{ physicsStore.analytics.handling_complexity_score }}%</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Phase III.b Inspector Mode -->
        <div class="left-behind-panel" v-if="transStore.leftBehind.length > 0">
          <h3 class="panel-title">⚠️ Left Behind ({{ transStore.leftBehind.length }})</h3>
          <p class="panel-desc">Click to trigger Inspector Mode</p>
          <div class="left-behind-list">
            <div 
              v-for="rej in transStore.leftBehind" 
              :key="rej.tracking_id"
              class="rej-card"
              :class="{ active: transStore.selectedRejection === rej.tracking_id }"
              @click="transStore.selectedRejection = transStore.selectedRejection === rej.tracking_id ? null : rej.tracking_id"
            >
              <div class="rej-id">{{ rej.tracking_id }}</div>
              <div class="rej-reason">{{ rej.reason }}</div>
            </div>
          </div>
        </div>
      </aside>
      <aside class="right-sidebar empty-kpi" v-else>
        <div class="kpi-placeholder">
          <div class="kpi-placeholder-icon">📊</div>
          <p>KPIs will appear after selecting a plan</p>
        </div>
      </aside>
    </div>
    
    <!-- Modals -->
    <FleetOptimizationSummaryModal 
      v-if="showOptimizationSummary" 
      @close="showOptimizationSummary = false" 
    />
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useLoadingStore } from '../stores/useLoadingStore'
import { useTransshipmentStore } from '../stores/useTransshipmentStore'
import TrailerScene from '../components/TrailerScene.vue'
import KpiPanel from '../components/ui/KpiPanel.vue'
import CargoTelemetryPanel from '../components/ui/CargoTelemetryPanel.vue'
import FleetOptimizationSummaryModal from '../components/ui/FleetOptimizationSummaryModal.vue'
import { optimizePlan } from '../api/loadingPlans'
import { usePhysicsStore } from '../stores/usePhysicsStore'

const store = useLoadingStore()
const transStore = useTransshipmentStore()
const physicsStore = usePhysicsStore()
const searchQuery = ref('')
const sheetsLoading = ref(false)
const sheetsToast = ref(null)
const apiErrorBanner = ref(null)

const activeMobileTab = ref('list')

const showAdvancedSettings = ref(false)
const operationalConfig = ref({
  base_handling_sec: 120,
  rotation_penalty_sec: 30,
  z_axis_penalty_sec: 90
})
const isOptimizing = ref(false)
const showOptimizationSummary = ref(false)

// Active watcher to enforce Cache Invalidation
watch(() => store.currentSteps, (newSteps) => {
  if (!newSteps || newSteps.length === 0) return
  const currentManifest = newSteps.map(step => step.cargo_items)
  physicsStore.validateCache(currentManifest)
}, { deep: true })

const formattedETA = computed(() => {
  if (!physicsStore.analytics) return '0h 0m'
  const totalSeconds = physicsStore.analytics.total_eta_seconds
  
  // Convert total to minutes, and mathematically round to the nearest whole minute
  const totalMinutesRounded = Math.round(totalSeconds / 60)
  
  const hours = Math.floor(totalMinutesRounded / 60)
  const minutes = totalMinutesRounded % 60
  
  return `${hours}h ${minutes}m`
})

const calculateEfficiency = async () => {
  if (!store.activePlan || !store.currentSteps.length) return
  isOptimizing.value = true
  
  const manifest = store.currentSteps.map(step => step.cargo_items)
  // Simulate fleet management API: Check maintenance schedule
  const truckData = { ...store.activePlan.trucks }
  // We simulate the flag being true for demonstration of the data pipeline
  truckData.requires_maintenance = true
  
  const payload = {
    truck: truckData,
    cargo: manifest
  }
  
  if (showAdvancedSettings.value) {
    payload.config = operationalConfig.value
  }
  
  try {
    apiErrorBanner.value = null
    const data = await optimizePlan(payload)
    if (data && data.analytics) {
      physicsStore.setOptimization(data, physicsStore.generateManifestHash(manifest))
    } else {
      apiErrorBanner.value = JSON.stringify(data)
    }
  } catch (err) {
    console.error("Optimization failed:", err)
    apiErrorBanner.value = err.message || JSON.stringify(err)
  } finally {
    isOptimizing.value = false
  }
}

onMounted(() => {
  store.startPolling()
})
onUnmounted(() => store.stopPolling())

function onSelectPlan(plan) {
  store.selectPlan(plan)
  activeMobileTab.value = 'stage'
}

// Link stores if needed when plan changes
watch(() => store.currentSteps, (newSteps) => {
  if (!newSteps || newSteps.length === 0) {
    transStore.loadingSequence = []
    return
  }
  
  // Set trailer dimensions based on the active plan's truck (convert cm to meters)
  const truck = store.activePlan?.trucks
  if (truck) {
    transStore.trailer = {
      length: truck.length / 100,
      width: truck.width / 100,
      height: truck.height / 100
    }
  }

  // Convert step data from cm to meters and map axes for the 3D engine
  // Backend axes: X=depth, Y=lateral, Z=vertical
  // Frontend expects: x=lateral, y=depth, z=vertical (based on TrailerScene.vue)
  transStore.loadingSequence = newSteps.map(step => ({
    tracking_id: step.cargo_item_id,
    x: step.y / 100, // lateral
    y: step.x / 100, // depth
    z: step.z / 100, // vertical
    w: step.orientation_width / 100,  // lateral size
    l: step.orientation_length / 100, // depth size
    h: step.orientation_height / 100, // vertical size
    weight: step.cargo_items?.weight || 0,
    material_class: (step.cargo_items?.is_fragile === 1) ? 'FRAGILE' : 'INERT'
  }))
  
  // Also load rejection data
  if (store.activePlan?.status === 'PARTIAL_SUCCESS') {
    transStore.leftBehind = [
      { tracking_id: 'REJECTED', dimensions: [1.2, 1.0, 1.0], reason: store.activePlan.rejection_reason }
    ]
  } else {
    transStore.leftBehind = []
  }
  
  transStore.scrubberIndex = transStore.loadingSequence.length - 1
})

const filteredPlans = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return store.plans
  return store.plans.filter(p =>
    (p.human_readable_id || '').toLowerCase().includes(q) ||
    (p.cargo_manifests?.name || '').toLowerCase().includes(q) ||
    (p.trucks?.name || '').toLowerCase().includes(q)
  )
})

const statusClass = computed(() => {
  const s = store.activePlan?.status
  if (s === 'SUCCESS') return 'badge-success'
  if (s === 'PARTIAL_SUCCESS') return 'badge-warn'
  return 'badge-error'
})

function displayStatus(plan) {
  if (!plan) return ''
  if (plan.status === 'SUCCESS') return 'LOAD COMPLETE'
  if (plan.status === 'PARTIAL_SUCCESS') {
    if (plan.rejection_reason === 'WEIGHT') return 'PAYLOAD WEIGHT EXCEEDED'
    return 'TRUCK FULL'
  }
  return plan.status
}

const actionAlert = computed(() => {
  if (!store.activePlan || !store.kpiData) return null
  const kpi = store.kpiData
  const plan = store.activePlan
  
  if (plan.status === 'PARTIAL_SUCCESS') {
    if (plan.rejection_reason === 'WEIGHT') {
      return { type: 'warn', icon: '⚠', title: 'HEAVY LOAD', message: `Payload weight limit reached (${kpi.totalWeight}kg). Engine halted packing to prevent axle overload.` }
    } else {
      return { type: 'warn', icon: '⚠', title: 'TRUCK FULL', message: `Volumetric limit reached. Remaining items cannot fit.` }
    }
  }
  
  let voidFillers = 0
  let airbags = 0
  let loadBars = 0
  let pallets = 0
  
  store.currentSteps.forEach(step => {
    const parseStr = (str) => {
      if (!str) return
      if (str.includes('Corrugated Void Filler')) voidFillers++
      if (str.includes('Woven Airbag')) airbags++
      if (str.includes('Load Bar')) loadBars++
      const palletMatch = str.match(/(\d+)x Empty Pallets/)
      if (palletMatch) {
        pallets += parseInt(palletMatch[1], 10)
      }
    }
    parseStr(step.dunnage_left)
    parseStr(step.dunnage_right)
    parseStr(step.dunnage_front)
    parseStr(step.dunnage_back)
  })
  
  if (voidFillers > 0 || airbags > 0 || loadBars > 0 || pallets > 0) {
    const parts = []
    if (loadBars > 0) parts.push(`${loadBars}x Load Bars`)
    if (airbags > 0) parts.push(`${airbags}x Woven Airbags`)
    if (voidFillers > 0) parts.push(`${voidFillers}x Corrugated Void Fillers`)
    if (pallets > 0) parts.push(`${pallets}x Empty Pallets`)
    
    return { type: 'warn', icon: '⚠', title: 'BRACING REQUIRED', message: `Install ${parts.join(', ')} for spatial support on ${plan.human_readable_id}.` }
  }
  
  if (kpi.cgStatus === 'SAFE') {
    return { type: 'ok', icon: '✓', title: 'BALANCE SECURE', message: `CGy lateral deviation is within the safe 10cm tolerance (${kpi.cgDeviation}cm).` }
  }
  
  return { type: 'error', icon: '⛔', title: 'UNSAFE BALANCE', message: `CGy deviation (${kpi.cgDeviation}cm) exceeds safety limits. Do not dispatch.` }
})

async function handlePushSheets() {
  if (!store.activePlan) return
  sheetsLoading.value = true
  sheetsToast.value = null
  const result = await store.pushToSheets(store.activePlan.id)
  sheetsLoading.value = false
  sheetsToast.value = result
  setTimeout(() => { sheetsToast.value = null }, 4000)
}
</script>

<style scoped>
/* ─── Layout Shell ────────────────────────────────── */
.manager-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: var(--bg);
  overflow: hidden;
}

/* ─── Top Navigation ──────────────────────────────── */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  z-index: 100;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.logo { display: flex; align-items: center; gap: 8px; }
.logo-icon { font-size: 20px; }
.logo-text {
  font-size: 17px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.3px;
}
.logo-badge {
  font-size: 10px;
  font-weight: 700;
  background: var(--primary-light);
  color: var(--primary);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--primary-border);
}

.nav-center { display: flex; align-items: center; gap: 10px; }
.manifest-title { font-size: 14px; font-weight: 600; color: var(--text); }
.manifest-title.muted { color: var(--text-faint); }

.status-badge {
  font-size: 10px; font-weight: 700;
  padding: 3px 10px; border-radius: 100px;
  letter-spacing: 0.5px; text-transform: uppercase;
}
.badge-success { background: var(--safe-light); color: var(--safe); border: 1px solid var(--safe-border); }
.badge-warn    { background: var(--warn-light);  color: var(--warn);  border: 1px solid var(--warn-border); }
.badge-error   { background: var(--danger-light);color: var(--danger);border: 1px solid var(--danger-border); }

.nav-right { display: flex; align-items: center; gap: 8px; }

/* Buttons */
.btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px; border-radius: 8px;
  font-size: 13px; font-weight: 500;
  cursor: pointer; border: 1px solid transparent;
  text-decoration: none; transition: all 0.18s;
  white-space: nowrap;
}
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-secondary {
  background: var(--surface-2); color: var(--text-muted);
  border-color: var(--border);
}
.btn-secondary:not(:disabled):hover { background: var(--border); }
.btn-sheets {
  background: var(--safe-light); color: var(--safe);
  border-color: var(--safe-border);
}
.btn-sheets:not(:disabled):hover { background: rgba(22,163,74,0.15); }
.btn-primary {
  background: var(--primary); color: #fff; font-weight: 600;
  border-color: var(--primary);
}
.btn-primary:hover { filter: brightness(1.12); transform: translateY(-1px); }

.btn-outline {
  background: transparent; color: var(--primary); font-weight: 600;
  border-color: var(--primary);
}
.btn-outline:hover { background: var(--primary-light); transform: translateY(-1px); }

/* Toast */
.sheets-toast {
  position: fixed; top: 68px; right: 20px;
  padding: 12px 20px; border-radius: 10px;
  font-size: 13px; font-weight: 500; z-index: 200;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
.sheets-toast.not_configured { background: var(--warn-light);   color: var(--warn);   border: 1px solid var(--warn-border); }
.sheets-toast.ok              { background: var(--safe-light);   color: var(--safe);   border: 1px solid var(--safe-border); }
.sheets-toast.error           { background: var(--danger-light); color: var(--danger); border: 1px solid var(--danger-border); }
.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-8px); }

/* ─── Three-Column Body ───────────────────────────── */

/* LEFT SIDEBAR */
.left-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 16px 12px;
}
.sidebar-header h2 {
  font-size: 11px; font-weight: 700; color: var(--text-faint);
  text-transform: uppercase; letter-spacing: 1.2px; margin: 0;
}
.plan-count {
  font-size: 11px; color: var(--text-muted);
  background: var(--surface-2); padding: 2px 8px;
  border-radius: 100px; border: 1px solid var(--border);
}

.search-wrap { padding: 0 12px 12px; }
.search-input {
  width: 100%; background: var(--surface-2);
  border: 1px solid var(--border); border-radius: 8px;
  padding: 8px 12px; color: var(--text); font-size: 13px;
  outline: none; transition: border-color 0.2s; box-sizing: border-box;
}
.search-input::placeholder { color: var(--text-faint); }
.search-input:focus { border-color: var(--primary-border); }

.plan-list { flex: 1; overflow-y: auto; padding: 4px 8px; }

.plan-card {
  padding: 12px; border-radius: 10px; cursor: pointer;
  margin-bottom: 6px; border: 1px solid var(--border);
  border-left: 4px solid transparent;
  background: var(--surface-2); transition: all 0.18s;
}
.plan-card:hover { border-color: var(--primary-border); background: var(--primary-light); border-left-color: var(--primary-border); }
.plan-card.active { background: var(--primary-light); border-color: var(--primary-border); border-left-color: var(--primary); }

.plan-card-id {
  font-size: 13px; font-weight: 700; color: var(--text);
  font-family: 'JetBrains Mono', monospace; margin-bottom: 4px;
}
.plan-card-meta { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
.plan-status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.plan-status-dot.ok   { background: var(--safe); }
.plan-status-dot.warn { background: var(--warn); }
.plan-card-stats { font-size: 12px; color: var(--text-faint); }
.sep { color: var(--border-mid); }

.empty-plans { text-align: center; padding: 32px 16px; color: var(--text-faint); font-size: 13px; }
.plan-list-loading {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
  color: var(--text-faint); font-size: 13px;
}
.spinner {
  width: 24px; height: 24px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.polling-indicator {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-top: 1px solid var(--border);
  font-size: 11px; color: var(--text-faint);
}
.pulse-dot {
  width: 6px; height: 6px; background: var(--safe);
  border-radius: 50%; animation: pulse 2s ease infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.8); }
}

/* MAIN 3D STAGE */
.stage {
  flex: 1; position: relative; overflow: hidden;
  display: flex; flex-direction: column;
  background: var(--bg);
}
.stage-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; gap: 16px;
  color: var(--text-faint);
}
.stage-empty-icon { font-size: 64px; opacity: 0.35; }
.stage-empty h3   { font-size: 18px; font-weight: 600; color: var(--text-muted); margin: 0; }
.stage-empty p    { font-size: 14px; color: var(--text-faint); text-align: center; max-width: 280px; margin: 0; }

/* Execution HUD */
.execution-hud {
  position: absolute; top: 16px; left: 16px; right: 16px;
  z-index: 10; display: flex; gap: 24px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 12px; padding: 10px 18px; align-items: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.hud-left { display: flex; flex-direction: column; gap: 4px; }
.hud-label { font-size: 10px; text-transform: uppercase; color: var(--text-faint); font-weight: 700; letter-spacing: 0.5px; }
.hud-select {
  background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text); padding: 6px 10px; border-radius: 6px;
  font-size: 13px; outline: none;
}

/* RIGHT SIDEBAR */
.right-sidebar {
  width: 290px; flex-shrink: 0;
  background: var(--surface);
  border-left: 1px solid var(--border);
  overflow-y: auto;
}

.empty-kpi { display: flex; align-items: center; justify-content: center; }
.kpi-placeholder { text-align: center; color: var(--text-faint); padding: 24px; }
.kpi-placeholder-icon { font-size: 40px; opacity: 0.3; margin-bottom: 12px; }
.kpi-placeholder p { font-size: 13px; }

/* Action Alert */
.action-alert {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; font-size: 13px; z-index: 10;
  border-bottom: 1px solid var(--border);
}
.action-alert.warn  { background: var(--warn-light);   border-bottom-color: var(--warn-border);   color: var(--warn); }
.action-alert.ok    { background: var(--safe-light);   border-bottom-color: var(--safe-border);   color: var(--safe); }
.action-alert.error { background: var(--danger-light); border-bottom-color: var(--danger-border); color: var(--danger); }
.alert-icon { font-size: 16px; }
.alert-content { color: var(--text); }
.action-alert.warn  .alert-content strong { color: var(--warn); }
.action-alert.ok    .alert-content strong { color: var(--safe); }
.action-alert.error .alert-content strong { color: var(--danger); }

/* Advanced Settings inline styles override */
.analytics-container input[type="number"] {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
}

/* Left Behind Panel */
.left-behind-panel { padding: 16px; border-top: 1px solid var(--border); }
.panel-title { color: var(--danger); font-size: 14px; font-weight: 700; margin-bottom: 4px; }
.panel-desc  { font-size: 11px; color: var(--text-faint); margin-bottom: 12px; }
.left-behind-list { display: flex; flex-direction: column; gap: 8px; }
.rej-card {
  background: var(--danger-light); border: 1px solid var(--danger-border);
  border-radius: 8px; padding: 10px; cursor: pointer; transition: all 0.18s;
}
.rej-card:hover  { background: rgba(220,38,38,0.15); }
.rej-card.active { background: rgba(220,38,38,0.2); border-color: rgba(220,38,38,0.5); }
.rej-id     { color: var(--danger); font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.rej-reason { color: var(--danger); font-size: 11px; }

/* ─── RESPONSIVE: Mobile-First Breakpoint ─────────── */
.mobile-tabs { display: none; }

@media (max-width: 1023px) {
  .mobile-tabs {
    display: flex;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 8px 16px;
    gap: 8px;
    flex-shrink: 0;
  }
  .mobile-tabs button {
    flex: 1; padding: 10px;
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 8px; font-size: 13px; font-weight: 600;
    color: var(--text-muted); transition: all 0.2s;
  }
  .mobile-tabs button.active {
    background: var(--primary); color: #fff;
    border-color: var(--primary);
  }
  .mobile-tabs button:disabled { opacity: 0.4; cursor: not-allowed; }

  /* By default on mobile, force display rules so data attribute controls visibility */
  .left-sidebar, .stage, .right-sidebar {
    display: none !important;
  }
  
  /* When tab is active, show the respective panel */
  .manager-layout[data-mobile-tab="list"] .left-sidebar { 
    display: flex !important; 
    width: 100% !important; 
    border-right: none; 
    flex: 1;
    height: 100%;
  }
  .manager-layout[data-mobile-tab="stage"] .stage { 
    display: flex !important; 
    flex: 1;
    height: 100%;
  }
  .manager-layout[data-mobile-tab="kpi"] .right-sidebar { 
    display: block !important; 
    width: 100% !important; 
    border-left: none; 
    flex: 1;
    height: 100%;
    overflow-y: auto;
  }

  /* Reduce nav on mobile — hide right nav buttons */
  .nav-right .btn-secondary,
  .nav-right .btn-sheets { display: none; }

  /* Stack nav items */
  .top-nav { padding: 0 16px; }
  .nav-center .manifest-title { font-size: 12px; }

  /* Larger touch targets on cards */
  .plan-card { padding: 14px; margin-bottom: 8px; }
  .plan-card-id { font-size: 14px; }
}

@media (max-width: 480px) {
  /* Extra small phones */
  .nav-center { display: none; }
  .plan-list { padding: 4px; }
}
</style>
