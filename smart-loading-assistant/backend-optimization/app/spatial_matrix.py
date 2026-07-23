import numpy as np
from typing import List, Dict, Any, Tuple

class CapacityExceeded(Exception):
    pass

class SpatialMatrixEngine:
    def __init__(self, trailer_dict: Dict[str, float], cargo_list: List[Dict[str, Any]]):
        self.trailer = trailer_dict
        self.cargo_list = cargo_list
        self.resolution = 0.02 # 2cm resolution
        
        # Dimensions in bins
        self.length_bins = int(self.trailer["length"] / self.resolution)
        self.width_bins = int(self.trailer["width"] / self.resolution)
        
        # Dual Matrices (X, Y) -> (width, length)
        self.floor_grid = np.zeros((self.width_bins, self.length_bins), dtype=np.float32)
        self.crush_grid = np.full((self.width_bins, self.length_bins), np.inf, dtype=np.float32)
        self.id_grid = np.full((self.width_bins, self.length_bins), "", dtype=object)
        
        self.staging_array = []
        self.loading_sequence = []
        self.left_behind = []
        
    def execute(self) -> Dict[str, List[Any]]:
        self._pre_flight_check()
        
        # Interleaved weight distribution
        heavy, medium, light = self._segment_cargo()
        
        # Staging array logic (grouping)
        self.staging_array = self._generate_staging_array(heavy, medium, light)
        
        # Target Mass Distribution Curve (Parabolic)
        # We will use a simplified physical packing loop to demonstrate the constraints
        
        process_queue = heavy + medium + light # Simplified for boilerplate
        
        for cargo in process_queue:
            result = self._attempt_placement(cargo)
            if result["status"] == "failed":
                self.left_behind.append({
                    "tracking_id": cargo["tracking_id"],
                    "dimensions": [cargo["length"], cargo["width"], cargo["height"]],
                    "best_attempt": result.get("best_attempt"),
                    "reason": result.get("reason", "Capacity Maxed"),
                    "collision_target_id": result.get("collision_target_id")
                })
                
        return {
            "staging_array": self.staging_array,
            "loading_sequence": self.loading_sequence,
            "left_behind": self.left_behind
        }

    def _pre_flight_check(self):
        total_weight = sum(c["weight"] for c in self.cargo_list)
        total_volume = sum(c["length"] * c["width"] * c["height"] for c in self.cargo_list)
        
        max_weight = self.trailer["max_weight"]
        max_volume = self.trailer["length"] * self.trailer["width"] * self.trailer["height"]
        
        if total_weight > max_weight:
            raise CapacityExceeded("Weight exceeds trailer capacity.")
        if total_volume > (max_volume * 0.9):
            raise CapacityExceeded("Volume exceeds 90% trailer capacity.")

    def _segment_cargo(self):
        # Sort by weight descending
        sorted_cargo = sorted(self.cargo_list, key=lambda x: x["weight"], reverse=True)
        n = len(sorted_cargo)
        if n == 0:
            return [], [], []
        # Basic tercile split
        heavy = sorted_cargo[:n//3]
        medium = sorted_cargo[n//3:2*n//3]
        light = sorted_cargo[2*n//3:]
        return heavy, medium, light

    def _generate_staging_array(self, heavy, medium, light):
        # Group by material_class first, then dimensions to minimize touches while enforcing safety
        staging = []
        for tier, name in [(heavy, "HEAVY"), (medium, "MEDIUM"), (light, "LIGHT")]:
            grouped = {}
            for c in tier:
                mat_class = c.get("material_class", "INERT")
                key = (mat_class, c["length"], c["width"], c["height"])
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(c)
            for key, items in grouped.items():
                mat_class, length, width, height = key
                staging.append({
                    "tier": name,
                    "material_class": mat_class,
                    "dimensions": (length, width, height),
                    "count": len(items),
                    "items": [i["tracking_id"] for i in items]
                })
        return staging

    def _attempt_placement(self, cargo: Dict[str, Any]) -> Dict[str, Any]:
        # Load from Y=0 to Y=L
        w_bin = int(cargo["width"] / self.resolution)
        l_bin = int(cargo["length"] / self.resolution)
        
        # Test rotations
        footprints = [
            (w_bin, l_bin, False),
            (l_bin, w_bin, True)
        ]
        
        best_placement = None
        best_cg_delta = float('inf')
        
        best_failed_placement = None
        best_failed_cg_delta = float('inf')
        
        target_cg_x = self.width_bins / 2.0
        
        for y in range(self.length_bins):
            for x in range(self.width_bins):
                for fw, fl, rotated in footprints:
                    if x + fw > self.width_bins or y + fl > self.length_bins:
                        continue
                    
                    target_area = self.floor_grid[x:x+fw, y:y+fl]
                    crush_area = self.crush_grid[x:x+fw, y:y+fl]
                    
                    placement_z = np.max(target_area)
                    
                    local_cg_x = x + (fw / 2.0)
                    delta = abs(local_cg_x - target_cg_x)
                    
                    # 1. Height constraint
                    if placement_z + cargo["height"] > self.trailer["height"]:
                        if delta < best_failed_cg_delta:
                            best_failed_cg_delta = delta
                            best_failed_placement = (x, y, placement_z, fw, fl, rotated, "Height Constraint Exceeded", None)
                        continue
                        
                    # 2. Crush constraint
                    if cargo["weight"] > np.min(crush_area):
                        if delta < best_failed_cg_delta:
                            best_failed_cg_delta = delta
                            # Extract who was crushed
                            min_idx = np.unravel_index(np.argmin(crush_area), crush_area.shape)
                            id_area = self.id_grid[x:x+fw, y:y+fl]
                            target_id = id_area[min_idx]
                            
                            best_failed_placement = (x, y, placement_z, fw, fl, rotated, "Crush Risk Detected", target_id)
                        continue
                        
                    # 3. Support Threshold constraint (90%)
                    support_ratio = np.sum(target_area == placement_z) / target_area.size
                    if placement_z > 0 and support_ratio < 0.90:
                        if delta < best_failed_cg_delta:
                            best_failed_cg_delta = delta
                            best_failed_placement = (x, y, placement_z, fw, fl, rotated, "No 90% Support Base Available", None)
                        continue
                        
                    # Calculate local Cg_x delta
                    if delta < best_cg_delta:
                        best_cg_delta = delta
                        best_placement = (x, y, placement_z, fw, fl, rotated)
            
            # If we found a valid placement on this Y-slice, break early to pack Nose to Door
            if best_placement:
                break
                
        if best_placement:
            x, y, z, fw, fl, rotated = best_placement
            # Commit to dual matrices
            self.floor_grid[x:x+fw, y:y+fl] = z + cargo["height"]
            self.crush_grid[x:x+fw, y:y+fl] = cargo.get("max_load_bearing", float('inf'))
            self.id_grid[x:x+fw, y:y+fl] = cargo["tracking_id"]
            
            # Convert bins back to meters for output
            self.loading_sequence.append({
                "tracking_id": cargo["tracking_id"],
                "x": x * self.resolution,
                "y": y * self.resolution,
                "z": float(z),
                "rotated": rotated
            })
            return {"status": "success"}
            
        if best_failed_placement:
            fx, fy, fz, ffw, ffl, frot, reason, collision_target_id = best_failed_placement
            return {
                "status": "failed",
                "reason": reason,
                "collision_target_id": collision_target_id,
                "best_attempt": {
                    "x": fx * self.resolution,
                    "y": fy * self.resolution,
                    "z": float(fz),
                    "rotated": frot
                }
            }
            
        return {"status": "failed", "reason": "Capacity Maxed", "collision_target_id": None}
