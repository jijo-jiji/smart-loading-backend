class Truck:
    def __init__(self, length, width, height, max_weight):
        self.length = length
        self.width = width
        self.height = height
        self.max_weight = max_weight

class CargoItem:
    def __init__(self, id, length, width, height, weight, is_fragile):
        self.id = id
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
        self.is_fragile = is_fragile

class PackingRequest:
    def __init__(self, truck, cargo):
        self.truck = truck
        self.cargo = cargo

class Coordinate:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class PackedItem:
    def __init__(self, id, coordinates, rotated, step_sequence):
        self.id = id
        self.coordinates = coordinates
        self.rotated = rotated
        self.step_sequence = step_sequence

class PackingResponse:
    def __init__(self, status, packed_items, unpacked_ids, left_weight, right_weight):
        self.status = status
        self.packed_items = packed_items
        self.unpacked_ids = unpacked_ids
        self.left_weight = left_weight
        self.right_weight = right_weight

def optimize_packing(request: PackingRequest):
    sorted_cargo = sorted(request.cargo, key=lambda item: item.weight, reverse=True)
    
    packed_items = []
    unpacked_ids = []
    fragile_zones = [] # Stores tuples of (x_min, x_max, y_min, y_max)
    
    current_x, current_y, current_z = 0.0, 0.0, 0.0
    row_max_width, row_max_height = 0.0, 0.0
    
    left_side_weight, right_side_weight = 0.0, 0.0
    current_total_weight = 0.0
    
    truck_l = request.truck.length
    truck_w = request.truck.width
    truck_h = request.truck.height
    sequence_counter = 1
    
    for item in sorted_cargo:
        if current_total_weight + item.weight > request.truck.max_weight:
            unpacked_ids.append(item.id)
            continue
            
        l, w, h = item.length, item.width, item.height
        rotated = False
        
        # Z-Axis Rotation Check
        if current_x + l > truck_l and current_x + w <= truck_l:
            l, w = w, l
            rotated = True
            
        # Row/Layer Reset Adjustments
        if current_x + l > truck_l:
            current_x = 0.0
            current_y += row_max_width
            row_max_width = 0.0
            
        if current_y + w > truck_w:
            current_y = 0.0
            current_x = 0.0
            current_z += row_max_height
            row_max_height = 0.0
            
        if current_z + h > truck_h:
            unpacked_ids.append(item.id)
            continue
            
        # CRITIQUE FIX 3: Dynamic Lateral Snapping for Real-Time Weight Balancing
        if left_side_weight > right_side_weight:
            # Left is heavy -> Snap to the right wall
            target_y = truck_w - w
        else:
            # Right is heavy or balanced -> Snap to the left wall
            target_y = 0.0

        # Enforce Fragile Footprint Intersections using the targeted Y position
        overlap_fragile = False
        for fx_min, fx_max, fy_min, fy_max in fragile_zones:
            if not (current_x + l <= fx_min or current_x >= fx_max or 
                    target_y + w <= fy_min or target_y >= fy_max):
                overlap_fragile = True
                break
                
        if overlap_fragile and current_z > 0:
            unpacked_ids.append(item.id)
            continue

        if item.is_fragile:
            fragile_zones.append((current_x, current_x + l, target_y, target_y + w))
            
        # Update specific lateral weight tracking based on final center of mass
        if target_y + (w / 2) < (truck_w / 2):
            left_side_weight += item.weight
        else:
            right_side_weight += item.weight
            
        packed_items.append(PackedItem(
            id=item.id,
            coordinates=Coordinate(x=current_x, y=target_y, z=current_z),
            rotated=rotated,
            step_sequence=sequence_counter
        ))
        
        # Advance X pointer based on the current row progress
        current_x += l
        current_total_weight += item.weight
        row_max_width = max(row_max_width, w)
        row_max_height = max(row_max_height, h)
        sequence_counter += 1
        
    status = "SUCCESS" if not unpacked_ids else "PARTIAL_SUCCESS"
    
    return PackingResponse(
        status=status,
        packed_items=packed_items,
        unpacked_ids=unpacked_ids,
        left_weight=left_side_weight,
        right_weight=right_side_weight
    )

# Run Test
truck = Truck(length=600.0, width=240.0, height=240.0, max_weight=5000.0)
cargo_items = [
    CargoItem(id="ITEM-A-HUGE-FRAGILE", length=200.0, width=200.0, height=200.0, weight=50.0, is_fragile=True),
    CargoItem(id="ITEM-B-SMALL-HEAVY", length=100.0, width=100.0, height=100.0, weight=2000.0, is_fragile=False),
    CargoItem(id="ITEM-C-SMALL-HEAVY", length=100.0, width=100.0, height=100.0, weight=2000.0, is_fragile=False)
]

req = PackingRequest(truck=truck, cargo=cargo_items)
res = optimize_packing(req)

print(f"Status: {res.status}")
print(f"Left Weight: {res.left_weight} | Right Weight: {res.right_weight}")
print("--- PACKED STEPS ---")
for p in res.packed_items:
    print(f"[{p.step_sequence}] {p.id} -> x={p.coordinates.x}, y={p.coordinates.y}, z={p.coordinates.z} | rotated={p.rotated}")

print("\n--- UNPACKED ITEMS ---")
print(res.unpacked_ids)
