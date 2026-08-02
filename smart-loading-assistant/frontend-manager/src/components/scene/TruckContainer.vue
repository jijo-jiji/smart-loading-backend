<template>
  <TresGroup :position="[truck.width / 2, truck.height / 2, truck.length / 2]">
    <!-- Main Trailer Wireframe -->
    <TresMesh>
      <TresBoxGeometry :args="[truck.width, truck.height, truck.length]" />
      <TresMeshBasicMaterial color="#00ff00" :wireframe="true" :transparent="true" :opacity="0.2" />
    </TresMesh>
    
    <!-- Solid Front Wall (Headboard) at backend X=0 (frontend Z=0) -->
    <TresMesh :position="[0, 0, -truck.length / 2]">
      <TresPlaneGeometry :args="[truck.width, truck.height]" />
      <TresMeshStandardMaterial color="#374151" />
    </TresMesh>
  </TresGroup>
</template>

<script setup>
const props = defineProps({
  truck: {
    type: Object,
    required: true
  }
})
</script>
