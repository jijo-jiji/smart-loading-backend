<template>
  <div class="manager-layout">
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
        <RouterLink to="/operator" class="btn btn-primary">
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

    <div class="main-body">
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
            @click="store.selectPlan(plan)"
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
            
            <div class="hud-center">
              <label class="hud-label">Temporal Scrubber</label>
              <input 
                type="range" 
                min="0" 
                :max="transStore.loadingSequence.length - 1" 
                v-model="transStore.scrubberIndex" 
                class="hud-slider" 
              />
              <div class="scrubber-ticks">
                <div 
                  v-for="y in transStore.yAxisLayers" 
                  :key="y" 
                  class="tick"
                  :title="'Layer at Y=' + y"
                ></div>
              </div>
            </div>
          </div>
          
          <TrailerScene />
        </template>
      </main>

      <!-- Right Sidebar: KPIs & Left Behind -->
      <aside class="right-sidebar" v-if="store.activePlan">
        <KpiPanel />
        
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
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useLoadingStore } from '../stores/useLoadingStore'
import { useTransshipmentStore } from '../stores/useTransshipmentStore'
import TrailerScene from '../components/TrailerScene.vue'
import KpiPanel from '../components/ui/KpiPanel.vue'

const store = useLoadingStore()
const transStore = useTransshipmentStore()
const searchQuery = ref('')
const sheetsLoading = ref(false)
const sheetsToast = ref(null)

onMounted(() => {
  store.startPolling()
})
onUnmounted(() => store.stopPolling())

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
.manager-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: #0a0f1e;
  overflow: hidden;
}

/* Top Nav */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  background: rgba(15, 23, 42, 0.95);
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  backdrop-filter: blur(12px);
  z-index: 100;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo-icon { font-size: 20px; }
.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.logo-badge {
  font-size: 10px;
  font-weight: 700;
  background: rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(99, 102, 241, 0.4);
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 12px;
}
.manifest-title {
  font-size: 15px;
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}
.manifest-title.muted { color: #475569; }

.status-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 100px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.badge-success { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.badge-warn { background: rgba(251, 191, 36, 0.2); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-error { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }

.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  text-decoration: none;
  transition: all 0.2s;
}
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-secondary { background: rgba(148,163,184,0.1); color: #94a3b8; border: 1px solid rgba(148,163,184,0.2); }
.btn-secondary:not(:disabled):hover { background: rgba(148,163,184,0.2); }
.btn-sheets { background: rgba(52, 211, 153, 0.1); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.btn-sheets:not(:disabled):hover { background: rgba(52, 211, 153, 0.2); }
.btn-primary { background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; font-weight: 600; }
.btn-primary:hover { filter: brightness(1.15); transform: translateY(-1px); }

/* Toast */
.sheets-toast {
  position: fixed;
  top: 72px;
  right: 24px;
  padding: 12px 20px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  z-index: 200;
  backdrop-filter: blur(12px);
}
.sheets-toast.not_configured { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.sheets-toast.ok { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.sheets-toast.error { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-8px); }

/* Main Body */
.main-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Left Sidebar */
.left-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.8);
  border-right: 1px solid rgba(148,163,184,0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px 12px;
}
.sidebar-header h2 { font-size: 13px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
.plan-count { font-size: 12px; color: #475569; background: rgba(148,163,184,0.1); padding: 2px 8px; border-radius: 100px; }

.search-wrap { padding: 0 12px 12px; }
.search-input {
  width: 100%;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(148,163,184,0.15);
  border-radius: 8px;
  padding: 8px 12px;
  color: #f1f5f9;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}
.search-input::placeholder { color: #475569; }
.search-input:focus { border-color: rgba(99,102,241,0.5); }

.plan-list { flex: 1; overflow-y: auto; padding: 4px 8px; }
.plan-list::-webkit-scrollbar { width: 4px; }
.plan-list::-webkit-scrollbar-track { background: transparent; }
.plan-list::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.2); border-radius: 4px; }

.plan-card {
  padding: 12px 12px;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 6px;
  border: 1px solid rgba(148,163,184,0.08);
  background: rgba(30, 41, 59, 0.4);
  transition: all 0.2s;
}
.plan-card:hover { background: rgba(30, 41, 59, 0.8); border-color: rgba(99,102,241,0.3); }
.plan-card.active { background: rgba(99,102,241,0.1); border-color: rgba(99,102,241,0.5); }

.plan-card-id { font-size: 14px; font-weight: 700; color: #e2e8f0; font-family: 'JetBrains Mono', monospace; margin-bottom: 4px; }
.plan-card-meta { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #64748b; margin-bottom: 4px; }
.plan-status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.plan-status-dot.ok { background: #4ade80; }
.plan-status-dot.warn { background: #fbbf24; }
.plan-card-stats { font-size: 12px; color: #94a3b8; }
.sep { color: #334155; }

.empty-plans { text-align: center; padding: 32px 16px; color: #475569; font-size: 13px; }
.plan-list-loading { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: #475569; font-size: 13px; }
.spinner {
  width: 24px; height: 24px;
  border: 2px solid rgba(148,163,184,0.2);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.polling-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(148,163,184,0.08);
  font-size: 11px;
  color: #475569;
}
.pulse-dot {
  width: 6px; height: 6px;
  background: #4ade80;
  border-radius: 50%;
  animation: pulse 2s ease infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

/* Stage */
.stage { flex: 1; position: relative; overflow: hidden; display: flex; flex-direction: column; }
.stage-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #475569;
}
.stage-empty-icon { font-size: 64px; opacity: 0.4; }
.stage-empty h3 { font-size: 18px; font-weight: 600; color: #64748b; }
.stage-empty p { font-size: 14px; color: #475569; text-align: center; max-width: 280px; }

/* Action Alert */
.action-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid rgba(148,163,184,0.1);
  font-size: 13px;
  z-index: 10;
}
.action-alert.warn { background: rgba(251,191,36,0.1); border-bottom-color: rgba(251,191,36,0.2); color: #fbbf24; }
.action-alert.warn .alert-icon { color: #f59e0b; }
.action-alert.ok { background: rgba(74,222,128,0.1); border-bottom-color: rgba(74,222,128,0.2); color: #4ade80; }
.action-alert.ok .alert-icon { color: #22c55e; }
.action-alert.error { background: rgba(239,68,68,0.1); border-bottom-color: rgba(239,68,68,0.2); color: #f87171; }
.action-alert.error .alert-icon { color: #ef4444; }
.alert-icon { font-size: 16px; }
.alert-content { color: #e2e8f0; }
.action-alert.warn .alert-content strong { color: #fbbf24; }
.action-alert.ok .alert-content strong { color: #4ade80; }
.action-alert.error .alert-content strong { color: #f87171; }

/* Right Sidebar */
.right-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.8);
  border-left: 1px solid rgba(148,163,184,0.08);
  overflow-y: auto;
}
.right-sidebar::-webkit-scrollbar { width: 4px; }
.right-sidebar::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.2); border-radius: 4px; }

.empty-kpi { display: flex; align-items: center; justify-content: center; }
.kpi-placeholder { text-align: center; color: #475569; padding: 24px; }
.kpi-placeholder-icon { font-size: 40px; opacity: 0.3; margin-bottom: 12px; }
.kpi-placeholder p { font-size: 13px; }

/* Execution HUD (Phase III.b) */
.execution-hud {
  position: absolute;
  top: 16px;
  left: 16px;
  right: 16px;
  z-index: 10;
  display: flex;
  gap: 24px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 12px;
  padding: 12px 20px;
  align-items: center;
}
.hud-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.hud-label {
  font-size: 10px;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.hud-select {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}
.hud-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hud-slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}
.scrubber-ticks {
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
}
.scrubber-ticks .tick {
  width: 2px;
  height: 6px;
  background: #475569;
  border-radius: 2px;
}

/* Left Behind Panel */
.left-behind-panel {
  padding: 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.08);
  margin-top: 16px;
}
.panel-title {
  color: #f87171;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 4px;
}
.panel-desc {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 12px;
}
.left-behind-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.rej-card {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.rej-card:hover {
  background: rgba(239, 68, 68, 0.15);
}
.rej-card.active {
  background: rgba(239, 68, 68, 0.25);
  border-color: rgba(239, 68, 68, 0.5);
}
.rej-id {
  color: #fca5a5;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}
.rej-reason {
  color: #f87171;
  font-size: 11px;
}
</style>
