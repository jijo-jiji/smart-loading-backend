import { defineStore } from 'pinia'
import { fetchAllPlans, fetchStepsForPlan, pushPlanToSheets } from '../api/loadingPlans'

export const useLoadingStore = defineStore('loading', {
  state: () => ({
    plans: [],
    activePlan: null,
    currentSteps: [],
    currentStepIndex: 0,
    selectedStep: null,
    isLoading: false,
    error: null,
    pollingInterval: null,
    sheetsStatus: null,
  }),

  getters: {
    kpiData: (state) => {
      if (!state.activePlan) return null
      const truck = state.activePlan.trucks
      const totalWeight = (state.activePlan.left_weight_kg || 0) + (state.activePlan.right_weight_kg || 0)
      const truckCapacity = truck?.max_weight || 1
      const weightPct = Math.min(100, (totalWeight / truckCapacity) * 100)

      const truckVol = (truck?.length || 1) * (truck?.width || 1) * (truck?.height || 1)
      const usedVol = state.currentSteps.reduce((acc, s) => {
        return acc + (s.orientation_length * s.orientation_width * s.orientation_height)
      }, 0)
      const volumePct = Math.min(100, (usedVol / truckVol) * 100)

      // CG deviation from centerline (truck_w / 2)
      const truckW = truck?.width || 240
      const cgY = state.activePlan.cg_y || 0
      const cgDeviation = Math.abs(cgY - (truckW / 2))
      const cgStatus = cgDeviation <= 10 ? 'SAFE' : 'UNSAFE'
      
      const leftW = state.activePlan.left_weight_kg || 0
      const rightW = state.activePlan.right_weight_kg || 0
      const total = leftW + rightW || 1
      const leftPct = (leftW / total) * 100
      const rightPct = (rightW / total) * 100

      return {
        totalWeight,
        truckCapacity,
        weightPct,
        volumePct,
        cgDeviation: cgDeviation.toFixed(1),
        cgStatus,
        leftPct,
        rightPct,
        leftW,
        rightW,
      }
    },

    currentItem: (state) => {
      if (state.currentStepIndex === 0 || state.currentSteps.length === 0) return null
      return state.currentSteps[state.currentStepIndex - 1]
    },

    nextItem: (state) => {
      if (state.currentStepIndex >= state.currentSteps.length) return null
      return state.currentSteps[state.currentStepIndex]
    },
  },

  actions: {
    selectStep(step) {
      this.selectedStep = step
    },

    updateStepIndex(index) {
      this.currentStepIndex = index
    },

    confirmStep() {
      if (this.currentStepIndex < this.currentSteps.length) {
        this.currentStepIndex++
      }
    },

    async loadPlans() {
      this.isLoading = true
      this.error = null
      try {
        this.plans = await fetchAllPlans()
      } catch (err) {
        console.error('Failed to fetch plans:', err)
        this.error = err.message
      } finally {
        this.isLoading = false
      }
    },

    async selectPlan(plan) {
      this.activePlan = plan
      this.selectedStep = null
      this.currentStepIndex = 0
      this.isLoading = true
      this.error = null
      try {
        this.currentSteps = await fetchStepsForPlan(plan.id)
        this.currentStepIndex = this.currentSteps.length
      } catch (err) {
        console.error('Failed to fetch steps:', err)
        this.error = err.message
      } finally {
        this.isLoading = false
      }
    },

    startPolling() {
      this.loadPlans()
      this.pollingInterval = setInterval(() => {
        this.loadPlans()
      }, 5000)
    },

    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }
    },

    async pushToSheets(planId) {
      try {
        const result = await pushPlanToSheets(planId)
        this.sheetsStatus = result
        return result
      } catch (err) {
        this.sheetsStatus = { status: 'error', message: err.message }
        return this.sheetsStatus
      }
    },
  }
})
