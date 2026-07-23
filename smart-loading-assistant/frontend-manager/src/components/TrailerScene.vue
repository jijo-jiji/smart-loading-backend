<template>
  <div class="w-full h-full relative bg-gray-900">
    <TresCanvas clear-color="#111827" shadows>
      <TresPerspectiveCamera
        ref="cameraRef"
        :position="[store.trailer.width / 2, 10, store.trailer.length + 15]"
        :look-at="[store.trailer.width / 2, 0, store.trailer.length / 2]"
      />
      
      <!-- Constrained Panning/Zooming -->
      <MapControls 
        :enableRotate="true"
        :enableDamping="true"
        :dampingFactor="0.05"
        :minDistance="2"
        :maxDistance="50"
      />

      <TresAmbientLight :intensity="1" />
      <TresDirectionalLight :position="[10, 20, 10]" :intensity="1" cast-shadow />

      <!-- Trailer Floor Grid -->
      <TresMesh :position="[store.trailer.width / 2, -0.01, store.trailer.length / 2]" :rotation="[-Math.PI / 2, 0, 0]">
        <TresPlaneGeometry :args="[store.trailer.width, store.trailer.length, Math.ceil(store.trailer.width), Math.ceil(store.trailer.length)]" />
        <TresMeshBasicMaterial color="#374151" wireframe />
      </TresMesh>

      <!-- Scaled Group for Centimeter-based Components -->
      <TresGroup :scale="[0.01, 0.01, 0.01]">
        <!-- Trailer Bounds Outline (Green Wireframe) -->
        <TruckContainer v-if="loadingStore.activePlan" :truck="loadingStore.activePlan.trucks" />

        <!-- Cargo Boxes and Dunnage -->
        <CargoMesh
          v-if="loadingStore.currentSteps.length"
          :steps="visibleSteps"
          :highlight-id="store.selectedRejection"
        />

        <!-- Inspector Mode: Floating Ghost -->
        <TresGroup v-if="store.selectedRejection">
          <TresMesh :position="ghostPosition">
            <TresBoxGeometry :args="[ghostW, ghostH, ghostL]" />
            <TresMeshStandardMaterial 
              color="#ef4444" 
              transparent 
              :opacity="0.8" 
            />
          </TresMesh>
        </TresGroup>
      </TresGroup>

    </TresCanvas>
    
    <!-- Camera Snap Controls -->
    <div class="absolute top-4 right-4 flex space-x-2">
      <button @click="snapCamera('top')" class="px-3 py-1 bg-gray-800 text-white rounded shadow border border-gray-700 hover:bg-gray-700 text-sm font-semibold">Top (Z)</button>
      <button @click="snapCamera('side')" class="px-3 py-1 bg-gray-800 text-white rounded shadow border border-gray-700 hover:bg-gray-700 text-sm font-semibold">Side (X)</button>
      <button @click="snapCamera('nose')" class="px-3 py-1 bg-gray-800 text-white rounded shadow border border-gray-700 hover:bg-gray-700 text-sm font-semibold">Nose (Y)</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { MapControls } from '@tresjs/cientos'
import { useTransshipmentStore } from '../stores/useTransshipmentStore'
import { useLoadingStore } from '../stores/useLoadingStore'
import TruckContainer from './scene/TruckContainer.vue'
import CargoMesh from './scene/CargoMesh.vue'

const store = useTransshipmentStore()
const loadingStore = useLoadingStore()
const cameraRef = ref(null)

const visibleSteps = computed(() => {
  return loadingStore.currentSteps.slice(0, store.scrubberIndex + 1)
})

const isCollisionTarget = (trackingId) => {
  if (!store.selectedRejection) return false
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej && rej.collision_target_id === trackingId
}

// Ghost Box dimensions
const ghostW = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej ? rej.dimensions[1] : 1 // lateral
})
const ghostH = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej ? rej.dimensions[2] : 1 // vertical
})
const ghostL = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej ? rej.dimensions[0] : 1 // depth
})
const ghostPosition = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  if (!rej) return [0, 0, 0]
  
  const w = rej.dimensions[1] // lateral
  const h = rej.dimensions[2] // vertical
  const l = rej.dimensions[0] // depth
  
  if (rej.best_attempt) {
    // If it has a best attempt, place it exactly where it failed inside the truck
    const { x, y, z, rotated } = rej.best_attempt
    const actualW = rotated ? l : w
    const actualL = rotated ? w : l
    return [y + (actualW / 2), z + (h / 2), x + (actualL / 2)]
  } else {
    // Capacity Maxed: Place it floating outside the trailer doors
    return [(store.trailer.width * 100) / 2, 50 + (h / 2), (store.trailer.length * 100) + 200]
  }
})

const snapCamera = (profile) => {
  if (!cameraRef.value) return
  const cam = cameraRef.value
  const tw = store.trailer.width
  const tl = store.trailer.length
  const th = store.trailer.height
  
  // Look at center
  cam.lookAt(tw / 2, th / 2, tl / 2)
  
  if (profile === 'top') {
    cam.position.set(tw / 2, 20, tl / 2)
  } else if (profile === 'side') {
    cam.position.set(20, th / 2, tl / 2)
  } else if (profile === 'nose') {
    cam.position.set(tw / 2, th / 2, -10)
  }
}
</script>
