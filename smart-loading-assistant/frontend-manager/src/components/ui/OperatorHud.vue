<template>
  <div class="hud-wrap">
    <div class="hud-glass">
      <!-- Left Data Block -->
      <div class="hud-block left-block">
        <div class="hud-item-id">{{ currentItem?.cargo_items?.label || 'Next Item' }}</div>
        <div class="hud-weight">
          <span class="weight-num">{{ currentItem?.cargo_items?.weight || '–' }}</span>
          <span class="weight-unit">kg</span>
        </div>
        <div class="hud-fragile" v-if="currentItem?.cargo_items?.is_fragile">
          <span class="fragile-dot"></span> FRAGILE
        </div>
      </div>

      <!-- Center Action Block -->
      <div class="hud-center">
        <div class="step-counter">Step {{ store.currentStepIndex + 1 }} of {{ store.currentSteps.length }}</div>
        <button
          class="confirm-btn"
          :disabled="isComplete"
          @click="handleConfirm"
          :class="{ 'confirm-pulse': !isComplete }"
        >
          <span v-if="isComplete">✓ Complete</span>
          <span v-else>CONFIRM PLACEMENT</span>
        </button>
        <div class="step-progress">
          <div class="step-track">
            <div class="step-fill" :style="{ width: progressPct + '%' }"></div>
          </div>
          <span class="step-pct">{{ progressPct.toFixed(0) }}%</span>
        </div>
      </div>

      <!-- Right Data Block -->
      <div class="hud-block right-block">
        <div class="hud-block-label">DUNNAGE INSTRUCTIONS</div>
        <div class="dunnage-list" v-if="currentItem">
          <div v-if="currentItem.dunnage_left" class="d-dir">L: {{ currentItem.dunnage_left }}</div>
          <div v-if="currentItem.dunnage_right" class="d-dir">R: {{ currentItem.dunnage_right }}</div>
          <div v-if="currentItem.dunnage_front" class="d-dir">F: {{ currentItem.dunnage_front }}</div>
          <div v-if="currentItem.dunnage_back" class="d-dir">B: {{ currentItem.dunnage_back }}</div>
          <div v-if="!currentItem.dunnage_left && !currentItem.dunnage_right && !currentItem.dunnage_front && !currentItem.dunnage_back" class="d-dir clear">CLEAR (Friction Fit)</div>
        </div>
        <div class="hud-dims" v-if="currentItem" style="margin-top: 12px;">
          {{ currentItem.orientation_length }}L × {{ currentItem.orientation_width }}W × {{ currentItem.orientation_height }}H
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useLoadingStore } from '../../stores/useLoadingStore'

const store = useLoadingStore()

const isComplete = computed(() =>
  store.currentStepIndex >= store.currentSteps.length
)

const currentItem = computed(() => {
  if (isComplete.value || store.currentSteps.length === 0) return null
  return store.currentSteps[store.currentStepIndex]
})

const progressPct = computed(() => {
  if (!store.currentSteps.length) return 0
  return (store.currentStepIndex / store.currentSteps.length) * 100
})

function handleConfirm() {
  store.confirmStep()
}
</script>

<style scoped>
.hud-wrap {
  position: absolute;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 150;
  width: min(820px, calc(100vw - 48px));
}

.hud-glass {
  display: flex;
  align-items: center;
  gap: 0;
  background: rgba(10, 15, 30, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 20px;
  padding: 20px 28px;
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.04) inset,
    0 24px 80px rgba(0,0,0,0.6),
    0 0 40px rgba(99,102,241,0.08);
}

/* Left Block */
.hud-block {
  flex: 1;
}
.left-block { padding-right: 24px; border-right: 1px solid rgba(148,163,184,0.1); }
.right-block { padding-left: 24px; border-left: 1px solid rgba(148,163,184,0.1); }

.hud-item-id {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}
.hud-weight { display: flex; align-items: baseline; gap: 4px; margin-bottom: 6px; }
.weight-num { font-size: 36px; font-weight: 800; color: #f1f5f9; line-height: 1; }
.weight-unit { font-size: 14px; color: #64748b; font-weight: 500; }
.hud-fragile {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  color: #f87171;
  letter-spacing: 1px;
}
.fragile-dot {
  width: 6px; height: 6px;
  background: #f87171;
  border-radius: 50%;
  animation: pulse 1.2s ease infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Center Block */
.hud-center {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 0 32px;
}

.step-counter {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.5px;
}

.confirm-btn {
  padding: 16px 40px;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  color: white;
  transition: all 0.2s;
  white-space: nowrap;
  box-shadow: 0 4px 24px rgba(99,102,241,0.4);
  position: relative;
  overflow: hidden;
}
.confirm-btn:disabled {
  background: rgba(74,222,128,0.2);
  color: #4ade80;
  box-shadow: none;
  cursor: default;
  letter-spacing: 0.5px;
}
.confirm-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(99,102,241,0.5);
}
.confirm-btn:not(:disabled):active {
  transform: translateY(0);
}
.confirm-pulse::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent);
  animation: shimmer 2s ease infinite;
}
@keyframes shimmer {
  0% { opacity: 0; transform: translateX(-100%); }
  50% { opacity: 1; }
  100% { opacity: 0; transform: translateX(100%); }
}

.step-progress { width: 100%; display: flex; align-items: center; gap: 8px; }
.step-track {
  flex: 1;
  height: 4px;
  background: rgba(148,163,184,0.12);
  border-radius: 2px;
  overflow: hidden;
}
.step-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  border-radius: 2px;
  transition: width 0.5s cubic-bezier(0.4,0,0.2,1);
}
.step-pct { font-size: 11px; color: #64748b; width: 32px; text-align: right; }

/* Right Block */
.hud-block-label {
  font-size: 10px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 4px;
}
.dunnage-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
}
.d-dir {
  font-size: 13px;
  font-weight: 700;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}
.d-dir.clear {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}
.hud-dims {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 600;
  background: rgba(255,255,255,0.03);
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.05);
}
</style>
