<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity">
    <!-- Modal Container -->
    <div class="relative w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
        <h2 class="text-lg font-bold text-slate-200 tracking-wide uppercase">AI Fleet Optimization Summary</h2>
        <button 
          @click="$emit('close')" 
          class="text-slate-400 hover:text-white transition-colors p-1 rounded-md hover:bg-slate-800"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Scrollable Content Area -->
      <div class="p-6 overflow-y-auto custom-scrollbar">
        
        <!-- Stale State Lock -->
        <div v-if="physicsStore.isStale" class="bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-red-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 class="text-red-400 font-bold text-lg mb-1">MANIFEST MUTATED</h3>
          <p class="text-red-300/80 text-sm">Optimization payload hash mismatch. Please recalculate.</p>
        </div>

        <!-- Valid Reports -->
        <template v-else>
          <!-- Model Run Output Banner -->
          <div class="flex flex-col sm:flex-row gap-4 mb-8">
            <div class="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-lg p-5 flex items-center justify-between">
              <span class="text-slate-400 text-sm font-semibold uppercase tracking-wider">Volume Utilization</span>
              <span class="text-2xl font-black text-slate-100">{{ (physicsStore.volumeUtilization || 0).toFixed(1) }}%</span>
            </div>
            <div 
              class="flex-1 border rounded-lg p-5 flex items-center justify-between"
              :class="physicsStore.isSafe ? 'bg-green-900/10 border-green-500/30' : 'bg-red-900/10 border-red-500/30'"
            >
              <span class="text-slate-400 text-sm font-semibold uppercase tracking-wider">Safety Status</span>
              <span 
                class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border"
                :class="physicsStore.isSafe ? 'bg-green-500/20 text-green-400 border-green-500/50' : 'bg-red-500/20 text-red-400 border-red-500/50'"
              >
                {{ physicsStore.isSafe ? 'SAFE' : 'DANGER' }}
              </span>
            </div>
          </div>

          <div class="space-y-8">
            <!-- Automated Decisions Log -->
            <section v-if="physicsStore.decisionCodes && physicsStore.decisionCodes.length > 0">
              <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 border-b border-slate-800 pb-2">
                Automated Decisions Log
              </h3>
              <ul class="space-y-3">
                <li 
                  v-for="(code, idx) in physicsStore.decisionCodes" 
                  :key="idx"
                  class="flex items-start gap-3 bg-slate-800/30 p-3 rounded-lg border border-slate-700/30"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                  <span class="text-slate-300 text-sm leading-relaxed">
                    {{ decisionCodeMap[code] || `Automated Optimization: ${code}` }}
                  </span>
                </li>
              </ul>
            </section>

            <!-- Active Safety & Axle Alerts -->
            <section v-if="physicsStore.safetyAlerts && physicsStore.safetyAlerts.length > 0">
              <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 border-b border-slate-800 pb-2">
                Active Safety & Axle Alerts
              </h3>
              <ul class="space-y-3">
                <li 
                  v-for="(alert, idx) in physicsStore.safetyAlerts" 
                  :key="idx"
                  class="flex items-start gap-3 bg-orange-900/10 p-3 rounded-lg border border-orange-500/20"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-orange-400 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  <span class="text-orange-200/90 text-sm leading-relaxed">
                    {{ alertLogs[alert] || `Unknown System Alert: ${alert}` }}
                  </span>
                </li>
              </ul>
            </section>
          </div>
        </template>

      </div>
    </div>
  </div>
</template>

<script setup>
import { usePhysicsStore } from '../../stores/usePhysicsStore'

defineEmits(['close'])

const physicsStore = usePhysicsStore()

// Strict presentation layer mapping: Raw backend physics engine codes to human-readable strings
const decisionCodeMap = {
  'FORCED_CENTER': 'Dominant payload strictly centered to neutralize lateral rollover threat.',
  'MAX_DENSITY': 'Light cargo staggered along left axle to maximize spatial density.',
  'CLASS_VENTILATION': 'Temp-controlled cargo assigned to specific slots to meet ventilation standards.'
}

// Strict presentation layer mapping for Safety Alerts
const alertLogs = {
  'MAINTENANCE_WARNING': 'SLA-3304-L (Day Cab) is nearing its 25-day standard inspection cycle limit.',
}
</script>

<style scoped>
/* Custom scrollbar for webkit */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.5); 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.8); 
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 1); 
}
</style>
