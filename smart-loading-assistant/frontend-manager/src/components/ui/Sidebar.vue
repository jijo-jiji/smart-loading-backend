<script setup>
import { onMounted } from 'vue'
import { useLoadingStore } from '../../stores/useLoadingStore'

const store = useLoadingStore()

onMounted(() => {
  store.loadPlans()
})
</script>

<template>
  <aside class="w-64 h-screen bg-gray-100 p-4 overflow-y-auto border-r border-gray-300">
    <h2 class="text-xl font-bold mb-4">Loading Plans</h2>
    
    <div v-if="store.isLoading && store.plans.length === 0">Loading database...</div>
    <div v-else-if="store.error" class="text-red-500">{{ store.error }}</div>
    
    <ul v-else class="space-y-2">
      <li 
        v-for="plan in store.plans" 
        :key="plan.id"
        @click="store.selectPlan(plan)"
        class="p-3 bg-white rounded shadow cursor-pointer hover:bg-blue-50 transition-colors"
        :class="{ 'border-2 border-blue-500': store.activePlan?.id === plan.id }"
      >
        <div class="text-sm text-gray-500">Plan ID:</div>
        <div class="font-mono text-xs truncate">{{ plan.id }}</div>
        <div class="mt-2 text-xs">
          L: {{ plan.left_weight_kg }}kg | R: {{ plan.right_weight_kg }}kg
        </div>
      </li>
    </ul>
  </aside>
</template>
