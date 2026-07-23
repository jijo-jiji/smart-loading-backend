<template>
  <TresGroup :position="[truck.length / 2, truck.height / 2, truck.width / 2]">
    <TresMesh>
      <TresBoxGeometry :args="[truck.length, truck.height, truck.width]" />
      <TresMeshBasicMaterial color="#00ff00" :wireframe="true" :transparent="true" :opacity="0.2" />
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
