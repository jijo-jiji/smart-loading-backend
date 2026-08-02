import json
from app.main import run_packing_algorithm, PackingRequest, Truck, CargoItem, OperationalConfig

def test():
    req = PackingRequest(
        truck=Truck(id="t1", name="truck", length=600, width=240, height=240, max_weight=15000, suspension_type="STANDARD", requires_maintenance=True),
        cargo=[CargoItem(id="c1", length=100, width=100, height=100, weight=500, is_fragile=False, is_hazardous=0)],
        config=OperationalConfig()
    )
    res = run_packing_algorithm(req, degraded_mode=False)
    print("Packed Items:", len(res.packed_items))
    print("Volume Util:", res.analytics.volume_utilization)
    print("Alerts:", res.analytics.safety_alerts)

if __name__ == "__main__":
    test()
