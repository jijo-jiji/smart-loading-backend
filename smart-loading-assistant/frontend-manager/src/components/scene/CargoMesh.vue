<template>
  <TresGroup>
    <TresGroup
      v-for="step in steps"
      :key="step.id || step.cargo_item_id"
      :position="[
        step.y + step.orientation_width / 2,
        step.z + step.orientation_height / 2,
        step.x + step.orientation_length / 2
      ]"
    >
      <!-- True Cargo Box -->
      <TresMesh
        @click="(e) => onClick(e, step)"
        @pointer-enter="(e) => onHover(e, step)"
        @pointer-leave="onLeave"
      >
        <TresBoxGeometry :args="[step.orientation_width, step.orientation_height, step.orientation_length]" />
        <TresMeshStandardMaterial
          :color="boxColor(step)"
          :emissive="boxEmissive(step)"
          :emissive-intensity="isHighlighted(step) ? 0.6 : (isSelected(step) ? 0.4 : 0)"
          :opacity="boxOpacity(step)"
          :transparent="true"
        />

        <!-- Edge outline for selected/highlighted items -->
        <TresLineSegments :visible="isHighlighted(step) || isSelected(step)">
          <TresEdgesGeometry>
            <TresBoxGeometry :args="[step.orientation_width, step.orientation_height, step.orientation_length]" />
          </TresEdgesGeometry>
          <TresLineBasicMaterial :color="isHighlighted(step) ? '#60a5fa' : '#ffffff'" :linewidth="2" />
        </TresLineSegments>
      </TresMesh>

      <TresGroup
        v-for="(strut, i) in getDunnageStruts(step)"
        :key="'dunnage-' + step.id + '-' + i"
        :position="[strut.localX, 0, strut.localZ]"
      >
        <!-- Wood Pallets -->
        <TresMesh v-if="strut.type === 'pallets'">
          <TresBoxGeometry :args="[strut.len, strut.h, strut.w]" />
          <TresMeshBasicMaterial color="#8B5A2B" />
        </TresMesh>
        <TresLineSegments v-if="strut.type === 'pallets'">
          <TresEdgesGeometry>
            <TresBoxGeometry :args="[strut.len, strut.h, strut.w]" />
          </TresEdgesGeometry>
          <TresLineBasicMaterial color="#3E2723" :linewidth="2" />
        </TresLineSegments>

        <!-- Woven Airbag -->
        <TresMesh v-if="strut.type === 'airbag'">
          <TresCylinderGeometry :args="[Math.min(strut.len, strut.w)/2, Math.min(strut.len, strut.w)/2, strut.h, 16]" />
          <TresMeshBasicMaterial color="#FFFFFF" :opacity="0.6" :transparent="true" :depthWrite="false" />
        </TresMesh>

        <!-- Load Bar -->
        <TresGroup v-if="strut.type === 'loadbar'">
          <TresMesh :position="[0, strut.h/3, 0]" :rotation="strut.axis === 'y' ? [0, 0, Math.PI/2] : [Math.PI/2, 0, 0]">
            <TresCylinderGeometry :args="[2, 2, strut.axis === 'y' ? strut.len : strut.w, 8]" />
            <TresMeshStandardMaterial color="#94A3B8" metalness="0.8" roughness="0.2" />
          </TresMesh>
          <TresMesh :position="[0, -strut.h/3, 0]" :rotation="strut.axis === 'y' ? [0, 0, Math.PI/2] : [Math.PI/2, 0, 0]">
            <TresCylinderGeometry :args="[2, 2, strut.axis === 'y' ? strut.len : strut.w, 8]" />
            <TresMeshStandardMaterial color="#94A3B8" metalness="0.8" roughness="0.2" />
          </TresMesh>
        </TresGroup>

        <!-- Corrugated Void Filler -->
        <TresMesh v-if="strut.type === 'corrugated'">
          <TresBoxGeometry :args="[strut.len, strut.h, strut.w]" />
          <TresMeshBasicMaterial color="#A0522D" :opacity="0.8" :transparent="true" />
        </TresMesh>
      </TresGroup>
    </TresGroup>
  </TresGroup>
</template>

<script setup>
import { ref } from 'vue'
import * as THREE from 'three'
import { useLoadingStore } from '../../stores/useLoadingStore'

const props = defineProps({
  steps: { type: Array, required: true },
  highlightId: { type: String, default: null },
  operatorMode: { type: Boolean, default: false },
})

const emit = defineEmits(['box-hover', 'box-leave', 'box-click'])

const store = useLoadingStore()
const hoveredId = ref(null)

function getDunnageStruts(step) {
  const struts = []
  
  const parseDunnage = (dStr, gap, axis, dir) => {
    if (!dStr || dStr === 'Stretch-Wrap to Base' || gap < 1) return null
    
    let type = 'corrugated'
    if (dStr.includes('Pallets')) type = 'pallets'
    else if (dStr.includes('Load Bar')) type = 'loadbar'
    else if (dStr.includes('Airbag')) type = 'airbag'
    
    let localX = 0, localZ = 0
    let len = 0, w = 0
    
    if (axis === 'y') {
      // Lateral gap (left/right) -> Offset on X axis
      localX = dir === -1 ? -(step.orientation_width / 2) - (gap / 2) : (step.orientation_width / 2) + (gap / 2)
      len = gap
      w = step.orientation_length * 0.8
    } else {
      // Depth gap (front/back) -> Offset on Z axis
      localZ = dir === -1 ? -(step.orientation_length / 2) - (gap / 2) : (step.orientation_length / 2) + (gap / 2)
      len = step.orientation_width * 0.8
      w = gap
    }
    
    return {
      type,
      localX,
      localY: 0,
      localZ,
      len,
      w,
      h: step.orientation_height * 0.6,
      axis
    }
  }

  const left = parseDunnage(step.dunnage_left, step.gap_left_cm, 'y', -1)
  if (left) struts.push(left)
  
  const right = parseDunnage(step.dunnage_right, step.gap_right_cm, 'y', 1)
  if (right) struts.push(right)
  
  const front = parseDunnage(step.dunnage_front, step.gap_front_cm, 'x', -1)
  if (front) struts.push(front)
  
  const back = parseDunnage(step.dunnage_back, step.gap_back_cm, 'x', 1)
  if (back) struts.push(back)

  return struts
}

function stepId(step) {
  return step.cargo_item_id || step.id
}

function isHighlighted(step) {
  return props.highlightId === stepId(step)
}

function isSelected(step) {
  return store.selectedStep && (store.selectedStep.cargo_item_id || store.selectedStep.id) === stepId(step)
}

function boxColor(step) {
  if (props.operatorMode) {
    if (isHighlighted(step)) return '#3b82f6'
    return '#1e3a5f'
  }
  if (isSelected(step)) return '#6366f1'
  return step.cargo_items?.is_fragile ? '#ef4444' : '#3b82f6'
}

function boxEmissive(step) {
  if (isHighlighted(step)) return '#1d4ed8'
  if (isSelected(step)) return '#312e81'
  return '#000000'
}

function boxOpacity(step) {
  if (props.operatorMode) {
    if (isHighlighted(step)) return 1.0
    return 0.2
  }
  if (hoveredId.value === stepId(step)) return 0.75
  return 1.0
}

function onClick(event, step) {
  if (event?.stopPropagation) event.stopPropagation()
  store.selectStep(step)
  emit('box-click', step)
}

function onHover(event, step) {
  hoveredId.value = stepId(step)
  // ThreeJS pointer-enter gives nativeEvent with DOM coords
  const domEvent = event?.nativeEvent || event
  emit('box-hover', step, domEvent)
}

function onLeave() {
  hoveredId.value = null
  emit('box-leave')
}
</script>
