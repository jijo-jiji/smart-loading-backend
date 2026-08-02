import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const usePhysicsStore = defineStore('physics', () => {
  const packedItems = ref([])
  const leftWeight = ref(0)
  const rightWeight = ref(0)
  const payloadCg = ref(null)
  const analytics = ref(null)
  const payloadHash = ref(null)
  const isStale = ref(false)
  const isLoading = ref(false)
  const error = ref(null)

  // Optimization Summary State (Dynamic)
  const volumeUtilization = computed(() => analytics.value?.volume_utilization || 0.0)
  const decisionCodes = computed(() => analytics.value?.decision_codes || [])
  const safetyAlerts = computed(() => analytics.value?.safety_alerts || [])

  // Pure mathematical getter tied strictly to the backend's explicit 'is_safe' boolean.
  // NO double-compute or hardcoded thresholds are permitted on the frontend.
  const isSafe = computed(() => analytics.value?.is_safe ?? false)

  function generateManifestHash(manifest) {
    if (!manifest || !manifest.length) return ''
    const fingerprint = manifest.map(item => ({ id: item.id, weight: item.weight }))
      .sort((a, b) => a.id.localeCompare(b.id))
    return JSON.stringify(fingerprint)
  }

  function setOptimization(data, manifestHash) {
    packedItems.value = data.packed_items || []
    leftWeight.value = data.left_weight || 0
    rightWeight.value = data.right_weight || 0
    payloadCg.value = data.payload_cg || null
    analytics.value = data.analytics || null
    payloadHash.value = manifestHash
    isStale.value = false
  }

  function validateCache(currentManifest) {
    if (!payloadHash.value) return
    const currentHash = generateManifestHash(currentManifest)
    if (currentHash !== payloadHash.value) {
      isStale.value = true
    } else {
      isStale.value = false
    }
  }

  function invalidateState() {
    packedItems.value = []
    leftWeight.value = 0
    rightWeight.value = 0
    payloadCg.value = null
    analytics.value = null
    payloadHash.value = null
    isStale.value = false
  }

  return {
    packedItems,
    leftWeight,
    rightWeight,
    payloadCg,
    analytics,
    payloadHash,
    isStale,
    isLoading,
    error,
    volumeUtilization,
    decisionCodes,
    safetyAlerts,
    isSafe,
    generateManifestHash,
    setOptimization,
    validateCache,
    invalidateState
  }
})
