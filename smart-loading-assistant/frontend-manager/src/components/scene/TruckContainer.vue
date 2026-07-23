<template>
  <TresGroup :position="[truck.width / 2, truck.height / 2, truck.length / 2]">
    <TresMesh>
      <TresBoxGeometry :args="[truck.width, truck.height, truck.length]" />
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
