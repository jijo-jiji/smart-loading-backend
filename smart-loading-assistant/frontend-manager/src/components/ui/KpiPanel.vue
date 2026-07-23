<template>
  <div class="kpi-panel">
    <div class="kpi-header">
      <h2>Logistics KPIs</h2>
    </div>

    <template v-if="kpi">
      <!-- Weight Utilization -->
      <div class="kpi-section">
        <div class="kpi-label">
          <span>Weight Utilization</span>
          <span class="kpi-value">{{ kpi.totalWeight.toFixed(0) }}kg / {{ kpi.truckCapacity.toFixed(0) }}kg</span>
        </div>
        <div class="gauge-track">
          <div
            class="gauge-fill weight"
            :style="{ width: kpi.weightPct + '%' }"
            :class="kpi.weightPct > 90 ? 'danger' : kpi.weightPct > 70 ? 'warn' : 'ok'"
          ></div>
        </div>
        <div class="gauge-pct">{{ kpi.weightPct.toFixed(1) }}%</div>
      </div>

      <!-- Volumetric Utilization -->
      <div class="kpi-section">
        <div class="kpi-label">
          <span>Volume Utilization</span>
          <span class="kpi-value">{{ kpi.volumePct.toFixed(1) }}%</span>
        </div>
        <div class="gauge-track">
          <div
            class="gauge-fill volume"
            :style="{ width: kpi.volumePct + '%' }"
            :class="kpi.volumePct > 90 ? 'danger' : kpi.volumePct > 70 ? 'warn' : 'ok'"
          ></div>
        </div>
      </div>

      <!-- CG Balance Scale -->
      <div class="kpi-section">
        <div class="kpi-label">
          <span>CG<sub>y</sub> Lateral Balance</span>
          <span class="cg-badge" :class="kpi.cgStatus === 'SAFE' ? 'safe' : 'unsafe'">
            {{ kpi.cgStatus }} · {{ kpi.cgDeviation }}cm dev
          </span>
        </div>

        <!-- Balance Scale Visual -->
        <div class="balance-scale">
          <div class="balance-side left" :style="{ height: Math.max(20, kpi.leftPct * 0.8) + 'px' }">
            <span class="balance-label">LEFT</span>
            <span class="balance-weight">{{ kpi.leftW.toFixed(0) }}kg</span>
          </div>
          <div class="balance-pivot" :class="kpi.cgStatus === 'SAFE' ? 'pivot-safe' : 'pivot-unsafe'">
            <div class="pivot-line" :style="{ transform: `rotate(${(kpi.rightPct - kpi.leftPct) * 0.4}deg)` }"></div>
            <div class="pivot-base">▲</div>
          </div>
          <div class="balance-side right" :style="{ height: Math.max(20, kpi.rightPct * 0.8) + 'px' }">
            <span class="balance-label">RIGHT</span>
            <span class="balance-weight">{{ kpi.rightW.toFixed(0) }}kg</span>
          </div>
        </div>

        <div class="cg-meter">
          <div class="cg-track">
            <div class="cg-center-line"></div>
            <div
              class="cg-indicator"
              :style="{ left: Math.min(95, Math.max(5, (kpi.leftPct))) + '%' }"
              :class="kpi.cgStatus === 'SAFE' ? 'cg-safe' : 'cg-unsafe'"
            ></div>
          </div>
          <div class="cg-track-labels">
            <span>L</span>
            <span>Centerline</span>
            <span>R</span>
          </div>
        </div>
      </div>

      <!-- CG XYZ -->
      <div class="kpi-section">
        <div class="kpi-label"><span>Center of Gravity</span></div>
        <div class="cg-coords">
          <div class="coord">
            <span class="coord-label">X</span>
            <span class="coord-val">{{ (store.activePlan?.cg_x || 0).toFixed(1) }}cm</span>
          </div>
          <div class="coord">
            <span class="coord-label">Y</span>
            <span class="coord-val" :class="kpi.cgStatus === 'SAFE' ? 'safe' : 'unsafe'">
              {{ (store.activePlan?.cg_y || 0).toFixed(1) }}cm
            </span>
          </div>
          <div class="coord">
            <span class="coord-label">Z</span>
            <span class="coord-val">{{ (store.activePlan?.cg_z || 0).toFixed(1) }}cm</span>
          </div>
        </div>
      </div>

      <!-- Selected Item -->
      <div class="kpi-section" v-if="store.selectedStep">
        <div class="kpi-label">
          <span>Selected Item</span>
          <button class="clear-btn" @click="store.selectStep(null)">×</button>
        </div>
        <div class="selected-item-info">
          <div class="selected-title">{{ store.selectedStep.cargo_items?.label || 'Item' }}</div>
          <div class="selected-row">
            <span>Weight:</span> <span>{{ store.selectedStep.cargo_items?.weight }}kg</span>
          </div>
          <div class="selected-row">
            <span>Dimensions:</span> <span>{{ store.selectedStep.orientation_length }}L × {{ store.selectedStep.orientation_width }}W × {{ store.selectedStep.orientation_height }}H</span>
          </div>
          <div class="selected-row">
            <span>Center (X,Y,Z):</span> <span>{{ store.selectedStep.x.toFixed(1) }}, {{ store.selectedStep.y.toFixed(1) }}, {{ store.selectedStep.z.toFixed(1) }}</span>
          </div>
          <div class="selected-row" v-if="store.selectedStep.requires_dunnage">
            <span class="dunnage-warn">Dunnage Required:</span> <span>{{ store.selectedStep.dunnage_margin }}cm</span>
          </div>
          <div class="selected-row" v-if="store.selectedStep.cargo_items?.is_fragile">
            <span class="fragile-warn">⚠ FRAGILE</span>
          </div>
        </div>
      </div>

      <!-- Manifest ID -->
      <div class="kpi-section">
        <div class="kpi-label"><span>Manifest</span></div>
        <div class="manifest-id-display">{{ store.activePlan?.human_readable_id }}</div>
        <div class="manifest-sub">{{ store.activePlan?.cargo_manifests?.name }}</div>
        <div class="manifest-sub muted">{{ store.activePlan?.trucks?.name }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useLoadingStore } from '../../stores/useLoadingStore'

const store = useLoadingStore()
const kpi = computed(() => store.kpiData)
</script>

<style scoped>
.kpi-panel {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.kpi-header {
  padding: 20px 16px 12px;
  border-bottom: 1px solid rgba(148,163,184,0.08);
}
.kpi-header h2 {
  font-size: 13px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.kpi-section {
  padding: 16px;
  border-bottom: 1px solid rgba(148,163,184,0.06);
}

.kpi-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}
.kpi-value { font-size: 12px; color: #64748b; }

.gauge-track {
  height: 6px;
  background: rgba(148,163,184,0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}
.gauge-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
.gauge-fill.ok { background: linear-gradient(90deg, #22c55e, #4ade80); }
.gauge-fill.warn { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.gauge-fill.danger { background: linear-gradient(90deg, #ef4444, #f87171); }
.gauge-pct { font-size: 11px; color: #64748b; text-align: right; }

/* Balance Scale */
.balance-scale {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 8px;
  height: 80px;
  margin: 12px 0;
}
.balance-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  width: 72px;
  background: rgba(99,102,241,0.15);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 6px 6px 0 0;
  padding: 6px 4px;
  transition: height 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
.balance-label { font-size: 9px; color: #64748b; font-weight: 700; letter-spacing: 1px; }
.balance-weight { font-size: 13px; font-weight: 700; color: #e2e8f0; }

.balance-pivot { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; }
.pivot-line {
  width: 4px;
  height: 40px;
  border-radius: 2px;
  transition: transform 0.6s ease;
}
.pivot-safe .pivot-line { background: #4ade80; }
.pivot-unsafe .pivot-line { background: #f87171; }
.pivot-base { font-size: 10px; color: #475569; }

/* CG Meter */
.cg-meter { margin-top: 12px; }
.cg-track {
  position: relative;
  height: 8px;
  background: rgba(148,163,184,0.1);
  border-radius: 4px;
  overflow: visible;
  margin-bottom: 4px;
}
.cg-center-line {
  position: absolute;
  left: 50%;
  top: -4px;
  width: 2px;
  height: 16px;
  background: rgba(148,163,184,0.3);
  border-radius: 1px;
}
.cg-indicator {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: left 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid rgba(0,0,0,0.3);
}
.cg-safe { background: #4ade80; box-shadow: 0 0 8px rgba(74,222,128,0.5); }
.cg-unsafe { background: #f87171; box-shadow: 0 0 8px rgba(248,113,113,0.5); }
.cg-track-labels { display: flex; justify-content: space-between; font-size: 10px; color: #475569; }

.cg-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 100px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.cg-badge.safe { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); }
.cg-badge.unsafe { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }

.cg-coords { display: flex; gap: 8px; }
.coord {
  flex: 1;
  background: rgba(30,41,59,0.6);
  border: 1px solid rgba(148,163,184,0.1);
  border-radius: 8px;
  padding: 8px;
  text-align: center;
}
.coord-label { display: block; font-size: 10px; color: #64748b; font-weight: 700; margin-bottom: 4px; }
.coord-val { font-size: 13px; font-weight: 600; color: #e2e8f0; }
.coord-val.safe { color: #4ade80; }
.coord-val.unsafe { color: #f87171; }

.manifest-id-display {
  font-size: 20px;
  font-weight: 800;
  color: #e2e8f0;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1px;
  margin-bottom: 4px;
}
.manifest-sub { font-size: 12px; color: #64748b; margin-top: 2px; }
.manifest-sub.muted { color: #475569; }

/* Selected Item */
.clear-btn {
  background: none; border: none;
  color: #94a3b8; font-size: 16px;
  cursor: pointer; padding: 0 4px;
}
.clear-btn:hover { color: #f1f5f9; }
.selected-item-info {
  background: rgba(99,102,241,0.08);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 8px;
  padding: 12px;
}
.selected-title {
  font-size: 14px; font-weight: 700; color: #f1f5f9;
  margin-bottom: 8px; padding-bottom: 8px;
  border-bottom: 1px solid rgba(148,163,184,0.1);
}
.selected-row {
  display: flex; justify-content: space-between;
  font-size: 12px; color: #64748b; margin-bottom: 4px;
}
.selected-row span:last-child { color: #e2e8f0; font-family: monospace; }
.dunnage-warn { color: #fbbf24 !important; font-weight: 600; }
.fragile-warn { color: #f87171 !important; font-weight: 700; }
</style>
