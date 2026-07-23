import os
import json
import uuid
import hashlib
import sqlite3
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")

from app.main import optimize_packing, PackingRequest, Truck, CargoItem

def get_or_create_worksheet(sh, title, headers):
    try:
        ws = sh.worksheet(title)
        ws.clear()
        ws.append_row(headers)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows="1000", cols="20")
        ws.append_row(headers)
    return ws

def seed():
    print("Seeding database with the Crucible Tests to Google Sheets...")
    
    # Drop and recreate the DB to pick up schema changes (dev mode)
    if os.path.exists("smart_loading.db"):
        os.remove("smart_loading.db")
        print("Dropped old smart_loading.db — recreating with updated schema.")
    from app.main import init_db
    init_db()
    
    if not GOOGLE_CREDENTIALS_JSON or not SHEET_ID:
        print("Error: GOOGLE_SHEETS_CREDENTIALS or GOOGLE_SHEET_ID not set in .env. Skipping Google Sheets push, running tests locally.")
        gc, sh = None, None
    else:
        try:
            creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            gc = gspread.authorize(creds)
            sh = gc.open_by_key(SHEET_ID)
            
            ws_trucks = get_or_create_worksheet(sh, "Trucks", ["id", "name", "length", "width", "height", "max_weight"])
            ws_manifests = get_or_create_worksheet(sh, "Manifests", ["id", "name", "description"])
            ws_cargo = get_or_create_worksheet(sh, "Cargo Items", ["id", "manifest_id", "label", "length", "width", "height", "weight", "is_fragile"])
            ws_plans = get_or_create_worksheet(sh, "Loading Plans", ["id", "truck_id", "manifest_id", "status", "left_weight_kg", "right_weight_kg", "cg_x", "cg_y", "cg_z", "rejection_reason"])
            ws_steps = get_or_create_worksheet(sh, "Loading Plan Steps", [
                "plan_id", "cargo_item_id", "sequence_number", "x", "y", "z", 
                "orientation_length", "orientation_width", "orientation_height", 
                "requires_dunnage", "dunnage_margin",
                "dunnage_left", "dunnage_right", "dunnage_front", "dunnage_back",
                "gap_left_cm", "gap_right_cm", "gap_front_cm", "gap_back_cm"
            ])
        except Exception as e:
            print(f"Failed to connect to Google Sheets: {e}")
            gc, sh = None, None

    # --- TEST CASE 1: The Crush Test ---
    truck1 = Truck(id=str(uuid.uuid4()), length=200.0, width=240.0, height=240.0, max_weight=5000.0)
    cargo1 = [
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=10.0, is_fragile=True, max_load_bearing=50.0), # Item A
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=2000.0, is_fragile=False, max_load_bearing=5000.0), # Item B
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=2000.0, is_fragile=False, max_load_bearing=5000.0), # Item C
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=400.0, is_fragile=False, max_load_bearing=1000.0), 
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=400.0, is_fragile=False, max_load_bearing=1000.0), 
    ]
    
    # --- TEST CASE 2: The Tetris Test ---
    truck2 = Truck(id=str(uuid.uuid4()), length=600.0, width=240.0, height=240.0, max_weight=5000.0)
    cargo2 = [
        CargoItem(id=str(uuid.uuid4()), length=150.0, width=100.0, height=100.0, weight=500.0, is_fragile=False, max_load_bearing=5000.0),
        CargoItem(id=str(uuid.uuid4()), length=140.0, width=150.0, height=100.0, weight=500.0, is_fragile=False, max_load_bearing=5000.0),
    ]
    
    # --- TEST CASE 3: The Imbalance Test ---
    truck3 = Truck(id=str(uuid.uuid4()), length=200.0, width=200.0, height=240.0, max_weight=5000.0)
    cargo3 = [
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=1000.0, is_fragile=False, max_load_bearing=5000.0),
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=800.0, is_fragile=False, max_load_bearing=5000.0),
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=600.0, is_fragile=False, max_load_bearing=5000.0),
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=400.0, is_fragile=False, max_load_bearing=5000.0),
    ]
    
    # --- TEST CASE 4: The Overflow Rejection ---
    truck4 = Truck(id=str(uuid.uuid4()), length=600.0, width=240.0, height=240.0, max_weight=5000.0)
    cargo4 = [
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=3000.0, is_fragile=False, max_load_bearing=5000.0),
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=100.0, height=100.0, weight=3000.0, is_fragile=False, max_load_bearing=5000.0),
    ]

    # --- TEST CASE 5: Dunnage Flag Test ---
    truck5 = Truck(id=str(uuid.uuid4()), length=600.0, width=240.0, height=240.0, max_weight=10000.0)
    cargo5 = [
        # Heavy & High Aspect Ratio -> Should trigger Pre-emptive Volumetric Inflation
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=50.0, height=120.0, weight=1000.0, is_fragile=False, max_load_bearing=5000.0),
        CargoItem(id=str(uuid.uuid4()), length=100.0, width=50.0, height=120.0, weight=1000.0, is_fragile=False, max_load_bearing=5000.0)
    ]
    
    tests = [
        ("Test 1: The Crush Test", truck1, cargo1),
        ("Test 2: The Tetris Test", truck2, cargo2),
        ("Test 3: The Imbalance Test", truck3, cargo3),
        ("Test 4: The Overflow Rejection", truck4, cargo4),
        ("Test 5: Dunnage Flag Test", truck5, cargo5),
    ]
    
    for test_name, truck_model, cargo_models in tests:
        print(f"\nRunning {test_name}...")
        
        request = PackingRequest(truck=truck_model, cargo=cargo_models)
        response = optimize_packing(request)
        
        manifest_id = str(uuid.uuid4())
        plan_id = str(uuid.uuid4())
        
        if sh:
            ws_trucks.append_row([truck_model.id, f"Rig for {test_name}", truck_model.length, truck_model.width, truck_model.height, truck_model.max_weight])
            ws_manifests.append_row([manifest_id, test_name, "Aggressive Crucible Test"])
            
            cargo_rows = []
            for i, c in enumerate(cargo_models):
                label = f"ITEM-{i+1} ({c.weight}kg)"
                cargo_rows.append([c.id, manifest_id, label, c.length, c.width, c.height, c.weight, c.is_fragile])
            ws_cargo.append_rows(cargo_rows)
            
            ws_plans.append_row([
                plan_id, truck_model.id, manifest_id, response.status, response.left_weight, response.right_weight,
                response.payload_cg.x if response.payload_cg else 0,
                response.payload_cg.y if response.payload_cg else 0,
                response.payload_cg.z if response.payload_cg else 0,
                response.rejection_reason
            ])
            
            steps_rows = []
            for p_item in response.packed_items:
                steps_rows.append([
                    plan_id, p_item.id, p_item.step_sequence,
                    p_item.coordinates.x, p_item.coordinates.y, p_item.coordinates.z,
                    p_item.orientation_length, p_item.orientation_width, p_item.orientation_height,
                    p_item.requires_dunnage, p_item.dunnage_margin,
                    p_item.dunnage_left, p_item.dunnage_right, p_item.dunnage_front, p_item.dunnage_back,
                    p_item.gap_left_cm, p_item.gap_right_cm, p_item.gap_front_cm, p_item.gap_back_cm
                ])
            if steps_rows:
                ws_steps.append_rows(steps_rows)
                
        # Insert into SQLite Cache
        import sqlite3
        conn = sqlite3.connect("smart_loading.db")
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO trucks VALUES (?, ?, ?, ?, ?, ?)", 
                  (truck_model.id, f"Rig for {test_name}", truck_model.length, truck_model.width, truck_model.height, truck_model.max_weight))
        c.execute("INSERT OR REPLACE INTO cargo_manifests VALUES (?, ?, ?)", 
                  (manifest_id, test_name, "Aggressive Crucible Test"))
        
        for i, cargo in enumerate(cargo_models):
            label = f"ITEM-{i+1} ({cargo.weight}kg)"
            c.execute("INSERT OR REPLACE INTO cargo_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                      (cargo.id, manifest_id, label, cargo.length, cargo.width, cargo.height, cargo.weight, int(cargo.is_fragile), cargo.max_load_bearing))
            
        # Generate immutable human-readable ID: SHA-256 of UUID → first 8 hex chars
        human_readable_id = 'MAN-' + hashlib.sha256(plan_id.encode()).hexdigest()[:8].upper()
        
        c.execute("INSERT OR REPLACE INTO loading_plans (id, human_readable_id, truck_id, manifest_id, status, left_weight_kg, right_weight_kg, cg_x, cg_y, cg_z, rejection_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                  (plan_id, human_readable_id, truck_model.id, manifest_id, response.status, response.left_weight, response.right_weight, 
                   response.payload_cg.x if response.payload_cg else 0, 
                   response.payload_cg.y if response.payload_cg else 0, 
                   response.payload_cg.z if response.payload_cg else 0,
                   response.rejection_reason))
        
        for p_item in response.packed_items:
            c.execute("INSERT OR REPLACE INTO loading_plan_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                      (plan_id, p_item.id, p_item.step_sequence, 
                       p_item.coordinates.x, p_item.coordinates.y, p_item.coordinates.z, 
                       p_item.orientation_length, p_item.orientation_width, p_item.orientation_height, 
                       int(p_item.requires_dunnage), p_item.dunnage_margin,
                       p_item.dunnage_left, p_item.dunnage_right, p_item.dunnage_front, p_item.dunnage_back,
                       p_item.gap_left_cm, p_item.gap_right_cm, p_item.gap_front_cm, p_item.gap_back_cm))
        conn.commit()
        conn.close()
            
        if response.packed_items:
            print(f"Packed {len(response.packed_items)} items. L:{response.left_weight} R:{response.right_weight}")
        else:
            print("No items packed!")
        
        if response.unpacked_ids:
            print(f"Rejected {len(response.unpacked_ids)} items")

if __name__ == "__main__":
    seed()
