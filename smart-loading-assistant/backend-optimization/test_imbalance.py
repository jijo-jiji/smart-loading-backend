import json
from app.main import run_packing_algorithm, PackingRequest, Truck, CargoItem, OperationalConfig

def test():
    req = PackingRequest(
        truck=Truck(id="t1", name="truck", length=600, width=240, height=240, max_weight=15000, suspension_type="STANDARD", requires_maintenance=True),
        cargo=[
            CargoItem(id="obstacle1", length=600, width=140, height=240, weight=10, is_fragile=False, is_hazardous=0),
            CargoItem(id="heavy_side_load", length=100, width=100, height=100, weight=10000, is_fragile=False, is_hazardous=0)
        ],
        config=OperationalConfig()
    )
    res = run_packing_algorithm(req, degraded_mode=False)
    print("Packed Items:", len(res.packed_items))
    if len(res.packed_items) > 0:
        for pi in res.packed_items:
            print(f"Item {pi.id} Position:", pi.coordinates.model_dump())
    
    print("Unpacked Items:", len(res.unpacked_items))
    if len(res.unpacked_items) > 0:
        for ui in res.unpacked_items:
            print(f"Rejection {ui.id}:", ui.reason)
        
    print("Status:", res.status)
    print("Rejection Reason (Global):", res.rejection_reason)
    print("Is Safe:", res.analytics.is_safe)

if __name__ == "__main__":
    test()
