<script setup>
import { useLoadingStore } from '../../stores/useLoadingStore'

const store = useLoadingStore()
</script>

<template>
  <div class="w-[400px] shrink-0 p-6 bg-gray-50 overflow-y-auto border-r border-gray-200">
    <h2 class="text-2xl font-bold mb-4">Pipeline Diagnostics</h2>
    
    <div v-if="!store.activePlan" class="text-gray-500 italic">
      Select a loading plan from the sidebar to verify database connection...
    </div>
    
    <div v-else>
      <!-- Selected Item Panel (Moved to the very top for instant visibility!) -->
      <div v-if="store.selectedStep" class="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 shadow">
        <h3 class="font-bold text-lg mb-2">Selected Item: {{ store.selectedStep.cargo_items?.label || 'Unknown' }}</h3>
        <ul class="text-sm space-y-1">
          <li><strong>Load Sequence:</strong> Step {{ store.selectedStep.sequence_number }}</li>
          <li><strong>Weight:</strong> {{ store.selectedStep.cargo_items?.weight }} kg</li>
          <li><strong>Fragile:</strong> {{ store.selectedStep.cargo_items?.is_fragile ? 'YES' : 'NO' }}</li>
          <li><strong>Dimensions:</strong> {{ store.selectedStep.orientation_length }}L x {{ store.selectedStep.orientation_width }}W x {{ store.selectedStep.orientation_height }}H</li>
        </ul>
      </div>

      <div class="mb-6 p-4 bg-white border border-gray-200 rounded shadow">
        <h3 class="font-bold text-lg mb-2">Active Plan Metadata</h3>
        <pre class="bg-gray-800 text-green-400 p-4 rounded text-sm overflow-x-auto">{{ JSON.stringify(store.activePlan, null, 2) }}</pre>
      </div>

      <div class="p-4 bg-white border border-gray-200 rounded shadow">
        <h3 class="font-bold text-lg mb-2">Coordinate Steps (Raw Data)</h3>
        <div v-if="store.isLoading">Fetching coordinates from PostgreSQL...</div>
        <pre v-else class="bg-gray-800 text-blue-400 p-4 rounded text-sm overflow-x-auto max-h-[500px]">{{ JSON.stringify(store.currentSteps, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>
