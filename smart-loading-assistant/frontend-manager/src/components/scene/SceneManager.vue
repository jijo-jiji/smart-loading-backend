<template>
  <div class="scene-manager">
    <TresCanvas clear-color="#060d1f">
      <TresPerspectiveCamera ref="cameraRef" :position="initialCameraPos" :look-at="[0, 0, 0]" />
      <OrbitControls v-if="mode === 'manager'" ref="controlsRef" />
      <TresAmbientLight :intensity="0.6" />
      <TresDirectionalLight :position="[800, 1200, 800]" :intensity="1.2" cast-shadow />
      <TresDirectionalLight :position="[-400, 400, -400]" :intensity="0.4" />

      <TruckContainer v-if="store.activePlan" :truck="store.activePlan.trucks" />
      <CargoMesh
        v-if="store.currentSteps.length"
        :steps="visibleSteps"
        :highlight-id="mode === 'operator' ? currentStepId : null"
        :operator-mode="mode === 'operator'"
        @box-hover="onBoxHover"
        @box-leave="onBoxLeave"
      />

      <!-- Global CG Sphere (Manager only) -->
      <TresMesh
        v-if="mode === 'manager' && store.activePlan?.cg_x"
        :position="[store.activePlan.cg_x, store.activePlan.cg_z, store.activePlan.cg_y]"
      >
        <TresSphereGeometry :args="[8, 32, 32]" />
        <TresMeshStandardMaterial
          color="#8b5cf6"
          :emissive="'#8b5cf6'"
          :emissive-intensity="0.8"
          :transparent="true"
          :opacity="0.9"
        />
      </TresMesh>

      <TresGridHelper :args="[3000, 30, '#1e293b', '#0f172a']" />
    </TresCanvas>

    <!-- Max Tonnage Overlay (Manager mode only) -->
    <div
      v-if="mode === 'manager' && store.activePlan?.rejection_reason === 'WEIGHT' && !hideTonnageOverlay"
      class="max-tonnage-overlay"
    >
      <div class="tonnage-banner">
        <span class="tonnage-icon">⚠</span>
        PAYLOAD WEIGHT EXCEEDED
        <button class="tonnage-close" @click="hideTonnageOverlay = true">×</button>
      </div>
    </div>

    <!-- Hover Tooltip (Manager mode) -->
    <Transition name="tooltip">
      <div
        v-if="mode === 'manager' && hoveredStep"
        class="hover-tooltip"
        :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
      >
        <div class="tooltip-title">{{ hoveredStep.cargo_items?.label || 'Item' }}</div>
        <div class="tooltip-row"><span>Weight</span><span>{{ hoveredStep.cargo_items?.weight }}kg</span></div>
        <div class="tooltip-row">
          <span>Dims</span>
          <span>{{ hoveredStep.orientation_length }}×{{ hoveredStep.orientation_width }}×{{ hoveredStep.orientation_height }}</span>
        </div>
        <div class="tooltip-row" v-if="hoveredStep.requires_dunnage">
          <span>Dunnage</span><span class="dunnage-tag">{{ hoveredStep.dunnage_margin }}cm</span>
        </div>
        <div class="tooltip-row fragile-row" v-if="hoveredStep.cargo_items?.is_fragile">
          <span>⚠ FRAGILE</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import * as THREE from 'three'
import { TresCanvas, useRenderLoop } from '@tresjs/core'
import { OrbitControls } from '@tresjs/cientos'
import TruckContainer from './TruckContainer.vue'
import CargoMesh from './CargoMesh.vue'
import { useLoadingStore } from '@/stores/useLoadingStore'

const props = defineProps({
  mode: { type: String, default: 'manager' }, // 'manager' | 'operator'
})

const store = useLoadingStore()
const cameraRef = ref(null)
const controlsRef = ref(null)
const hoveredStep = ref(null)
const tooltipPos = ref({ x: 0, y: 0 })
const hideTonnageOverlay = ref(false)

watch(() => store.activePlan, () => {
  hideTonnageOverlay.value = false
})

// Camera lerp targets for fly-to animation
const cameraTarget = new THREE.Vector3(0, 0, 0)
const lookTarget = new THREE.Vector3(0, 0, 0)
let lerpActive = false
const ISOMETRIC_OFFSET = new THREE.Vector3(600, 700, 600)

const initialCameraPos = computed(() => {
  return props.mode === 'operator' ? [600, 700, 600] : [1000, 1000, 1000]
})

const visibleSteps = computed(() => {
  if (props.mode === 'operator') {
    // Show already placed items + the current item we are about to place
    return store.currentSteps.slice(0, store.currentStepIndex + 1)
  }
  // Manager mode: show all items up to the current index (which is usually all of them)
  return store.currentSteps.slice(0, store.currentStepIndex)
})

const currentStepId = computed(() => {
  if (store.currentStepIndex >= store.currentSteps.length) return null
  return store.currentSteps[store.currentStepIndex]?.cargo_item_id
})

// Watch for step changes in operator mode to trigger fly-to
watch(() => store.currentStepIndex, (newIdx) => {
  if (props.mode !== 'operator') return
  const nextStep = store.currentSteps[newIdx]
  if (!nextStep) return

  // Compute centroid of next item in Three.js coordinate space (X, Z, Y mapping)
  const cx = nextStep.x + nextStep.orientation_length / 2
  const cy = nextStep.z + nextStep.orientation_height / 2
  const cz = nextStep.y + nextStep.orientation_width / 2

  lookTarget.set(cx, cy, cz)
  cameraTarget.set(cx + ISOMETRIC_OFFSET.x, cy + ISOMETRIC_OFFSET.y, cz + ISOMETRIC_OFFSET.z)
  lerpActive = true
})

// Render loop: lerp camera to target
const { onLoop } = useRenderLoop()
onLoop(() => {
  if (!lerpActive || !cameraRef.value) return

  const camera = cameraRef.value
  camera.position.lerp(cameraTarget, 0.06)

  if (controlsRef.value) {
    controlsRef.value.target.lerp(lookTarget, 0.06)
    controlsRef.value.update()
  } else {
    // Operator mode: no controls, manually look at target
    camera.lookAt(lookTarget)
  }

  const distToTarget = camera.position.distanceTo(cameraTarget)
  if (distToTarget < 0.5) lerpActive = false
})

// Expose hover handlers for CargoMesh to call via emits
function onBoxHover(step, event) {
  hoveredStep.value = step
  if (event?.clientX) {
    tooltipPos.value = { x: event.clientX + 16, y: event.clientY - 8 }
  }
}
function onBoxLeave() {
  hoveredStep.value = null
}
</script>

<style scoped>
.scene-manager {
  width: 100%;
  height: 100%;
  position: relative;
}

.hover-tooltip {
  position: fixed;
  background: rgba(10, 15, 30, 0.92);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 10px;
  padding: 12px 14px;
  min-width: 180px;
  pointer-events: none;
  z-index: 300;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.tooltip-title {
  font-size: 13px;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(148,163,184,0.1);
}
.tooltip-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
  padding: 2px 0;
}
.tooltip-row span:last-child { color: #94a3b8; font-weight: 500; }
.dunnage-tag { color: #fbbf24 !important; }
.fragile-row span { color: #f87171 !important; font-weight: 700; }

.tooltip-enter-active, .tooltip-leave-active { transition: opacity 0.15s; }
.tooltip-enter-from, .tooltip-leave-to { opacity: 0; }

.max-tonnage-overlay {
  position: absolute;
  top: 24px;
  left: 0;
  right: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  pointer-events: none; /* Crucial: allows orbit controls to work */
  z-index: 50;
}
.tonnage-banner {
  pointer-events: auto; /* Re-enable pointer events for the banner/close button */
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #f87171;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 2px;
  padding: 16px 24px 16px 20px;
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(239, 68, 68, 0.15);
  display: flex;
  align-items: center;
  gap: 16px;
  text-transform: uppercase;
  position: relative;
}
.tonnage-icon { font-size: 24px; }
.tonnage-close {
  background: rgba(239, 68, 68, 0.1);
  border: none;
  color: #f87171;
  font-size: 20px;
  line-height: 1;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 12px;
  transition: all 0.2s;
}
.tonnage-close:hover { background: rgba(239, 68, 68, 0.25); color: #fff; }
</style>
