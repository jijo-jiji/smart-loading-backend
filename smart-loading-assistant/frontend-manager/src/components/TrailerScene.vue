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

      <!-- Trailer Bounds Outline -->
      <TresLineSegments :position="[store.trailer.width / 2, store.trailer.height / 2, store.trailer.length / 2]">
        <TresEdgesGeometry>
          <TresBoxGeometry :args="[store.trailer.width, store.trailer.height, store.trailer.length]" />
        </TresEdgesGeometry>
        <TresLineBasicMaterial color="#4B5563" />
      </TresLineSegments>

      <!-- Loading Sequence (Zero-Cost GPU Scrubbing) -->
      <TresGroup>
        <TresMesh
          v-for="(pallet, index) in store.loadingSequence"
          :key="pallet.tracking_id"
          :position="[pallet.x + (pallet.w / 2), pallet.z + (pallet.h / 2), pallet.y + (pallet.l / 2)]"
          :visible="index <= store.scrubberIndex"
        >
          <TresBoxGeometry :args="[pallet.w, pallet.h, pallet.l]" />
          <TresMeshStandardMaterial 
            :color="isCollisionTarget(pallet.tracking_id) ? '#ffff00' : store.getPalletColor(pallet)"
            :transparent="!!store.selectedRejection && !isCollisionTarget(pallet.tracking_id)"
            :opacity="(store.selectedRejection && !isCollisionTarget(pallet.tracking_id)) ? 0.2 : 1.0"
            :wireframe="store.viewMode === 'material' && pallet.material_class === 'HAZMAT'"
          />
        </TresMesh>
      </TresGroup>

      <!-- Inspector Mode: Floating Ghost (contextual) -->
      <TresGroup v-if="store.selectedRejection">
        <TresMesh
          :position="ghostPosition"
        >
          <TresBoxGeometry :args="[ghostW, ghostH, ghostL]" />
          <TresMeshStandardMaterial 
            color="#ef4444" 
            transparent 
            :opacity="0.8" 
          />
        </TresMesh>
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

const store = useTransshipmentStore()
const cameraRef = ref(null)

const isCollisionTarget = (trackingId) => {
  if (!store.selectedRejection) return false
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej && rej.collision_target_id === trackingId
}

// Ghost Box dimensions
const ghostW = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej ? rej.dimensions[0] : 1
})
const ghostL = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej ? rej.dimensions[1] : 1
})
const ghostH = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  return rej ? rej.dimensions[2] : 1
})
const ghostPosition = computed(() => {
  const rej = store.leftBehind.find(i => i.tracking_id === store.selectedRejection)
  if (!rej) return [0, 0, 0]
  
  const w = rej.dimensions[0]
  const l = rej.dimensions[1]
  const h = rej.dimensions[2]
  
  if (rej.best_attempt) {
    // If it has a best attempt, place it exactly where it failed inside the truck
    const { x, y, z, rotated } = rej.best_attempt
    const actualW = rotated ? l : w
    const actualL = rotated ? w : l
    return [x + (actualW / 2), z + (h / 2), y + (actualL / 2)]
  } else {
    // Capacity Maxed: Place it floating outside the trailer doors
    return [store.trailer.width / 2, 0.5 + (h / 2), store.trailer.length + 2]
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
