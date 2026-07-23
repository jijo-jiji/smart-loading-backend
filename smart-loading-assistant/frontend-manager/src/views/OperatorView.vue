<template>
  <div class="operator-layout">
    <!-- Back to Manager link -->
    <RouterLink to="/manager" class="back-link">← Manager</RouterLink>

    <!-- Full-screen 3D Canvas -->
    <div class="canvas-wrap">
      <SceneManager v-if="store.activePlan" mode="operator" />
      <div v-else class="no-plan">
        <div class="no-plan-icon">🚛</div>
        <p>No active plan. <RouterLink to="/manager">Select one →</RouterLink></p>
      </div>
    </div>

    <!-- Floating Operator HUD -->
    <OperatorHud v-if="store.activePlan && store.currentSteps.length" />

    <!-- Completion Banner -->
    <Transition name="complete">
      <div v-if="isComplete" class="complete-banner">
        <div class="complete-icon">✅</div>
        <div>
          <div class="complete-title">Load Complete</div>
          <div class="complete-sub">{{ store.currentSteps.length }} items placed successfully</div>
        </div>
        <RouterLink to="/manager" class="btn-done">Back to Dashboard</RouterLink>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useLoadingStore } from '../stores/useLoadingStore'
import SceneManager from '../components/scene/SceneManager.vue'
import OperatorHud from '../components/ui/OperatorHud.vue'

const store = useLoadingStore()

// Reset to step 0 so operator sees the sequence from the start
onMounted(() => {
  store.updateStepIndex(0)
})

const isComplete = computed(() =>
  store.currentSteps.length > 0 && store.currentStepIndex >= store.currentSteps.length
)
</script>

<style scoped>
.operator-layout {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: #050a14;
}

.back-link {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 100;
  font-size: 13px;
  font-weight: 600;
  color: rgba(148,163,184,0.7);
  text-decoration: none;
  background: rgba(15,23,42,0.7);
  backdrop-filter: blur(8px);
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(148,163,184,0.15);
  transition: all 0.2s;
}
.back-link:hover { color: #f1f5f9; border-color: rgba(148,163,184,0.4); }

.canvas-wrap { width: 100%; height: 100%; }

.no-plan {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #475569;
  font-size: 15px;
}
.no-plan-icon { font-size: 56px; opacity: 0.3; }
.no-plan a { color: #6366f1; text-decoration: none; font-weight: 600; }

/* Completion Banner */
.complete-banner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(15,23,42,0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(74,222,128,0.4);
  border-radius: 20px;
  padding: 32px 40px;
  display: flex;
  align-items: center;
  gap: 20px;
  z-index: 200;
  box-shadow: 0 0 60px rgba(74,222,128,0.15);
}
.complete-icon { font-size: 48px; }
.complete-title { font-size: 22px; font-weight: 800; color: #4ade80; margin-bottom: 4px; }
.complete-sub { font-size: 14px; color: #64748b; }
.btn-done {
  margin-left: 20px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
  border-radius: 12px;
  font-weight: 700;
  text-decoration: none;
  font-size: 14px;
  transition: filter 0.2s;
}
.btn-done:hover { filter: brightness(1.15); }

.complete-enter-active, .complete-leave-active { transition: all 0.4s cubic-bezier(0.4,0,0.2,1); }
.complete-enter-from, .complete-leave-to { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
</style>
