import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTransshipmentStore = defineStore('transshipment', () => {
  // Mock Data (will be replaced by API call later)
  const trailer = ref({ length: 16.15, width: 2.59, height: 2.74 })
  const loadingSequence = ref([])
  const leftBehind = ref([])
  
  // UI State
  const scrubberIndex = ref(0)
  const viewMode = ref('density') // 'density' or 'material'
  const selectedRejection = ref(null) // tracking_id

  // Load a mock payload to test the dashboard
  const loadMockPayload = () => {
    loadingSequence.value = [
      { tracking_id: 'box1', x: 0.1, y: 0.1, z: 0.0, w: 1.2, l: 1.0, h: 1.0, weight: 1000, material_class: 'INERT' },
      { tracking_id: 'box2', x: 1.3, y: 0.1, z: 0.0, w: 1.2, l: 1.0, h: 1.0, weight: 200, material_class: 'HAZMAT' },
      { tracking_id: 'box3', x: 0.1, y: 1.1, z: 0.0, w: 1.2, l: 1.0, h: 1.0, weight: 800, material_class: 'INERT' },
      { tracking_id: 'box4', x: 0.1, y: 0.1, z: 1.0, w: 1.2, l: 1.0, h: 0.5, weight: 50, material_class: 'FRAGILE' }
    ]
    leftBehind.value = [
      { tracking_id: 'fail1', dimensions: [1.2, 1.0, 1.5], reason: 'Max Axle Weight Exceeded' },
      { tracking_id: 'fail2', dimensions: [0.8, 0.8, 1.0], reason: 'No 90% Support Base Available', best_attempt: { x: 0.5, y: 1.1, z: 1.0, rotated: false } },
      { tracking_id: 'fail3', dimensions: [1.0, 1.0, 1.0], reason: 'Crush Risk Detected', best_attempt: { x: 0.1, y: 0.1, z: 1.0, rotated: false }, collision_target_id: 'box4' }
    ]
    scrubberIndex.value = loadingSequence.value.length - 1
  }

  // Deduplicate incoming raw Google Sheets rows by Transaction_UUID
  const setLedgerData = (rawRows) => {
    // rawRows: array of [Manifest_ID, Tracking_ID, Material_Class, X, Y, Z, Transaction_UUID]
    // Group by Manifest_ID, then group by Transaction_UUID, keeping only the latest UUID batch
    const grouped = {}
    
    rawRows.forEach(row => {
      const manifest_id = row[0]
      const txn_uuid = row[6]
      if (!grouped[manifest_id]) {
        grouped[manifest_id] = {}
      }
      if (!grouped[manifest_id][txn_uuid]) {
        grouped[manifest_id][txn_uuid] = []
      }
      grouped[manifest_id][txn_uuid].push(row)
    })
    
    // For the active manifest, find the latest Transaction_UUID (assuming sequential retrieval or based on timestamp if available)
    // Here we just take the last UUID seen for the manifest
    const activeManifest = Object.keys(grouped)[0] // simplified for single-manifest view
    if (activeManifest) {
      const uuids = Object.keys(grouped[activeManifest])
      const latestUuid = uuids[uuids.length - 1] // The last append wins
      const validRows = grouped[activeManifest][latestUuid]
      
      loadingSequence.value = validRows.map(r => ({
        tracking_id: r[1],
        material_class: r[2],
        x: parseFloat(r[3]),
        y: parseFloat(r[4]),
        z: parseFloat(r[5]),
        w: 1.2, l: 1.0, h: 1.0, weight: 500 // Dummy data for visual
      }))
      scrubberIndex.value = loadingSequence.value.length - 1
    }
  }

  // Precompute Y-slice mass totals
  const ySliceMass = computed(() => {
    const massMap = {}
    loadingSequence.value.forEach(p => {
      // Group by nearest 10cm slice to avoid micro-layer fragmentation
      const sliceKey = Math.round(p.y * 10) / 10 
      massMap[sliceKey] = (massMap[sliceKey] || 0) + p.weight
    })
    return massMap
  })

  // Get color based on active mode
  const getPalletColor = (pallet) => {
    if (viewMode.value === 'density') {
      const sliceKey = Math.round(pallet.y * 10) / 10
      const sliceTotal = ySliceMass.value[sliceKey] || 0
      
      // Calculate heat ratio based on expected mass per slice (e.g., 2500kg is very hot)
      const maxSafeSliceMass = 2500 // kg
      const ratio = Math.min(sliceTotal / maxSafeSliceMass, 1.0)
      
      const r = Math.floor(255 * ratio)
      const b = Math.floor(255 * (1 - ratio))
      return `rgb(${r}, 0, ${b})`
    } else {
      // Material mode
      switch(pallet.material_class) {
        case 'HAZMAT': return '#ffaa00'
        case 'FRAGILE': return '#00ffff'
        default: return '#cccccc'
      }
    }
  }

  // Compute distinct Y-axis layers for the scrubber demarcations
  const yAxisLayers = computed(() => {
    const layers = new Set()
    loadingSequence.value.forEach(p => layers.add(p.y))
    return Array.from(layers).sort((a, b) => a - b)
  })

  return {
    trailer,
    loadingSequence,
    leftBehind,
    scrubberIndex,
    viewMode,
    selectedRejection,
    loadMockPayload,
    setLedgerData,
    getPalletColor,
    yAxisLayers
  }
})
