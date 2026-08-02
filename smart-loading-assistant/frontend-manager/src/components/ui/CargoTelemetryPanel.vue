<template>
  <div v-if="cargoData" class="telemetry-panel">
    <button class="close-btn" @click="closePanel">×</button>
    
    <div class="panel-header">
      <div class="cargo-id">{{ cargoData.tracking_id || cargoData.id }}</div>
    </div>
    
    <div class="panel-body">
      <div class="data-row" v-if="cargoData.is_hazardous">
        <span class="label text-red-500 font-bold flex items-center gap-1">
          <span class="icon">[!]</span> HAZARD WARNING
        </span>
        <span class="value text-red-400">RESTRICTED</span>
      </div>
      
      <div class="data-row">
        <span class="label">Temperature Req:</span>
        <span class="value font-mono" :class="isCold ? 'text-blue-300' : 'text-gray-300'">
          {{ cargoData.required_temperature || 'Ambient' }}
        </span>
      </div>

      <div class="data-row mt-2 pt-2 border-t border-gray-700">
        <span class="label">Mass:</span>
        <span class="value font-mono text-yellow-300">
          {{ cargoData.weight }} kg
        </span>
      </div>
      
      <div class="data-row mt-2 pt-2 border-t border-gray-700">
        <span class="label">Dimensions:</span>
        <span class="value text-gray-400 text-sm">
          {{ formatDim(cargoData.orientation_length) }} x {{ formatDim(cargoData.orientation_width) }} x {{ formatDim(cargoData.orientation_height) }} m
        </span>
      </div>

      <div class="data-row mt-2 pt-2 border-t border-gray-700">
        <span class="label">Coordinates (Audit):</span>
        <span class="value text-blue-300 font-mono text-xs">
          X:{{ cargoData.coordinates?.x?.toFixed(1) }} 
          Y:{{ cargoData.coordinates?.y?.toFixed(1) }} 
          Z:{{ cargoData.coordinates?.z?.toFixed(1) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useLoadingStore } from '../../stores/useLoadingStore'

const store = useLoadingStore()

// We get the selected step from the store
const cargoData = computed(() => {
  const step = store.selectedStep
  if (!step) return null
  
  // Merge step info with underlying cargo_items payload
  return {
    ...step,
    is_hazardous: step.cargo_items?.is_hazardous === 1 || step.cargo_items?.is_hazardous === true,
    required_temperature: step.cargo_items?.required_temperature || 'Ambient',
    weight: step.cargo_items?.weight || 0
  }
})

const isCold = computed(() => {
  const temp = cargoData.value?.required_temperature || ''
  return temp.includes('Cold') || temp.includes('-20') || temp.includes('2-8')
})

function closePanel() {
  store.selectedStep = null
}

function formatDim(cm) {
  if (!cm) return '0.00'
  return (cm / 100).toFixed(2)
}
</script>

<style scoped>
.telemetry-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(75, 85, 99, 0.6);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  color: white;
  z-index: 50; /* Ensure it floats over canvas */
  font-family: 'Inter', sans-serif;
  animation: slideIn 0.3s ease-out forwards;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 16px;
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #ffffff;
}

.panel-header {
  margin-bottom: 12px;
}

.cargo-id {
  font-size: 16px;
  font-weight: 700;
  color: #60a5fa;
  letter-spacing: 0.5px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.label {
  font-size: 13px;
  color: #9ca3af;
}

.value {
  font-size: 14px;
  font-weight: 600;
}
</style>
