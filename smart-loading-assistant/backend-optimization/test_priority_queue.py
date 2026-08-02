import json
import sqlite3
import time
from app.main import run_packing_algorithm, PackingRequest, Truck, CargoItem, OperationalConfig, persist_overflow_items, init_db, DB_PATH

def test():
    # Ensure tables are created
    init_db()

    # Create a truck with 15000 max weight and 240 width
    truck = Truck(id="t1", name="truck", length=600, width=240, height=240, max_weight=15000)
    
    # We want 5 heavy items. 
    # Item 1: 5000kg (Priority 5)
    # Item 2: 5000kg (Priority 5)
    # Item 3: 5000kg (Priority 0)
    # Item 4: 5000kg (Priority 0)
    # Item 5: 5000kg (Priority 0)
    # Wait, total weight is 25000kg. Max weight is 15000. 
    # The first 3 should fit (5000 * 3 = 15000). But wait, we want the algorithm to prioritize Priority 5 items!
    cargo = [
        CargoItem(id="low1", length=100, width=100, height=100, weight=5000, is_fragile=False, sla_priority=0),
        CargoItem(id="low2", length=100, width=100, height=100, weight=5000, is_fragile=False, sla_priority=0),
        CargoItem(id="low3", length=100, width=100, height=100, weight=5000, is_fragile=False, sla_priority=0),
        CargoItem(id="high1", length=100, width=100, height=100, weight=5000, is_fragile=False, sla_priority=5),
        CargoItem(id="high2", length=100, width=100, height=100, weight=5000, is_fragile=False, sla_priority=5),
    ]
    
    req = PackingRequest(truck=truck, cargo=cargo, config=OperationalConfig())
    
    # Run the packing logic (this will sort them)
    res = run_packing_algorithm(req, degraded_mode=False)
    
    packed_ids = [pi.id for pi in res.packed_items]
    print("Packed Items:", packed_ids)
    
    unpacked_ids = [ui.id for ui in res.unpacked_items]
    print("Unpacked Items:", unpacked_ids)
    
    # Manually trigger the background worker (since we aren't calling the API endpoint directly in this test)
    persist_overflow_items(res.unpacked_items)
    
    # Verify the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT cargo_id, reason FROM overflow_queue ORDER BY id DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()
    
    print("Recent Overflow DB Entries:", rows)

if __name__ == "__main__":
    test()
