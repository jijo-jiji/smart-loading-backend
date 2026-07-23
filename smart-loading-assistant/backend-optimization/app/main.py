import os
import json
import uuid
import heapq
import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import concurrent.futures

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
import datetime
import asyncio
from contextlib import asynccontextmanager
from app.sheets_integration import append_to_sheets, clear_sheets

DB_PATH = os.getenv("DB_PATH", "smart_loading.db")
_env_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
ALLOWED_ORIGINS = list(set(_env_origins + ["https://smart-loading-dashboard.netlify.app", "https://smart-loading-backend.netlify.app"]))
API_KEY = os.getenv("API_KEY", "unikl_demo_secret_2026")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

def verify_api_key(api_key_header_val: str = Security(api_key_header)):
    if api_key_header_val != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key_header_val

# Process pool for CPU-bound spatial math bypassing the GIL
spatial_process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=2)

class ManifestCargoItem(BaseModel):
    tracking_id: str
    weight: float
    length: float
    width: float
    height: float
    max_load_bearing: float = float('inf')
    material_class: Optional[str] = "INERT"

class TrailerConstraintsRequest(BaseModel):
    length: float
    width: float
    height: float
    max_weight: float

class SyncManifestRequest(BaseModel):
    manifest_id: str
    operator_id: str
    timestamp: str
    device_id: str
    trailer: TrailerConstraintsRequest
    cargo: List[ManifestCargoItem]

load_dotenv()
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    # Enable WAL mode and strict timeout for concurrent reads/writes
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=10000;")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pending_transshipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manifest_id TEXT,
            operator_id TEXT,
            timestamp TEXT,
            status TEXT,
            staging_array TEXT,
            loading_sequence TEXT,
            left_behind TEXT,
            synced_to_cloud INTEGER DEFAULT 0,
            transaction_uuid TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value_int INTEGER,
            value_text TEXT
        )
    """)
    c.execute("INSERT OR IGNORE INTO system_state (key, value_int) VALUES ('current_sheet_row_count', 0)")
    
    # Try adding new columns if they don't exist (for prototype DB migration)
    try:
        c.execute("ALTER TABLE pending_transshipments ADD COLUMN synced_to_cloud INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE pending_transshipments ADD COLUMN transaction_uuid TEXT")
    except sqlite3.OperationalError:
        pass
        
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_locks (
            id TEXT PRIMARY KEY,
            locked_at TIMESTAMP,
            lock_owner TEXT
        )
    """)
    c.execute("INSERT OR IGNORE INTO system_locks (id, locked_at, lock_owner) VALUES ('packing_loop', NULL, NULL)")
    
    # Cache Tables for Frontend
    c.execute("""
        CREATE TABLE IF NOT EXISTS trucks (
            id TEXT PRIMARY KEY, name TEXT, length REAL, width REAL, height REAL, max_weight REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cargo_manifests (
            id TEXT PRIMARY KEY, name TEXT, description TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cargo_items (
            id TEXT PRIMARY KEY, manifest_id TEXT, label TEXT, length REAL, width REAL, height REAL, weight REAL, is_fragile INTEGER, max_load_bearing REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS loading_plans (
            id TEXT PRIMARY KEY,
            human_readable_id TEXT UNIQUE,
            truck_id TEXT,
            manifest_id TEXT,
            status TEXT,
            left_weight_kg REAL,
            right_weight_kg REAL,
            cg_x REAL,
            cg_y REAL,
            cg_z REAL,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS loading_plan_steps (
            plan_id TEXT, cargo_item_id TEXT, sequence_number INTEGER, x REAL, y REAL, z REAL, orientation_length REAL, orientation_width REAL, orientation_height REAL, requires_dunnage INTEGER, dunnage_margin REAL,
            dunnage_left TEXT, dunnage_right TEXT, dunnage_front TEXT, dunnage_back TEXT,
            gap_left_cm REAL, gap_right_cm REAL, gap_front_cm REAL, gap_back_cm REAL,
            PRIMARY KEY (plan_id, cargo_item_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

class TopologicalCycleError(Exception):
    pass

sheets_queue = asyncio.Queue()

async def _sheets_flusher():
    while True:
        try:
            manifest_id = await sheets_queue.get()
            
            # 1. Fetch payload from SQLite
            loop = asyncio.get_running_loop()
            def fetch_and_sync():
                conn = sqlite3.connect(DB_PATH, timeout=15.0)
                c = conn.cursor()
                c.execute("SELECT staging_array, loading_sequence, left_behind, timestamp, status, transaction_uuid FROM pending_transshipments WHERE manifest_id = ?", (manifest_id,))
                row = c.fetchone()
                if not row:
                    conn.close()
                    return None
                    
                staging_json, loading_json, left_behind_json, timestamp, status, txn_uuid = row
                
                # Mock a manifest_dict and spatial_result
                manifest_dict = {
                    "manifest_id": manifest_id,
                    "timestamp": timestamp,
                    "cargo": [] # Not fully rehydrated here, but we can compute total_mass if needed. Sheets_integration will need cargo weight. Let's fix that.
                }
                
                spatial_result = {
                    "status": status,
                    "staging_array": json.loads(staging_json),
                    "loading_sequence": json.loads(loading_json),
                    "left_behind": json.loads(left_behind_json)
                }
                
                return manifest_dict, spatial_result, txn_uuid, conn
                
            data = await loop.run_in_executor(None, fetch_and_sync)
            if not data:
                sheets_queue.task_done()
                continue
                
            manifest_dict, spatial_result, txn_uuid, conn = data
            
            # Since we lost the original cargo weight, let's fetch it from the spatial_result staging array or assume we can pass total mass.
            # We'll update append_to_sheets to not rely on original cargo.
            
            try:
                await append_to_sheets(manifest_dict, spatial_result, txn_uuid)
                
                # 2. Update SQLite on success
                def update_success(connection):
                    cur = connection.cursor()
                    cur.execute("UPDATE pending_transshipments SET synced_to_cloud = 1 WHERE manifest_id = ?", (manifest_id,))
                    
                    # Increment row count (1 for Manifest + N for Spatial)
                    num_rows_added = 1 + len(spatial_result["loading_sequence"])
                    cur.execute("UPDATE system_state SET value_int = value_int + ? WHERE key = 'current_sheet_row_count'", (num_rows_added,))
                    
                    cur.execute("SELECT value_int FROM system_state WHERE key = 'current_sheet_row_count'")
                    current_count = cur.fetchone()[0]
                    connection.commit()
                    connection.close()
                    
                    if current_count >= 1800000:
                        print(f"WARNING: Rotation Imminent. Sheet row count is {current_count}")
                        
                await loop.run_in_executor(None, update_success, conn)
                
            except Exception as e:
                print(f"Sheets append failed: {e}")
                conn.close()
            finally:
                sheets_queue.task_done()
        except asyncio.CancelledError:
            break

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 3. Boot-up scan for unsynced records
    def scan_unsynced():
        conn = sqlite3.connect(DB_PATH, timeout=15.0)
        c = conn.cursor()
        c.execute("SELECT manifest_id FROM pending_transshipments WHERE synced_to_cloud = 0 AND status = 'READY'")
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]
        
    unsynced = scan_unsynced()
    for uid in unsynced:
        sheets_queue.put_nowait(uid)

    task = asyncio.create_task(_sheets_flusher())
    yield
    await sheets_queue.join()
    task.cancel()

app = FastAPI(title="Smart Loading Assistant - Core Math Engine", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FORKLIFT_WIDTH = 150.0
MANUAL_LIFT_MAX = 25.0
MAX_CG_DEVIATION = 10.0
CUMULATIVE_MASS_THRESHOLD = 1500.0

# --- Models ---
class Truck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    length: float
    width: float
    height: float
    max_weight: float
    suspension_type: str = "STANDARD"

class CargoItem(BaseModel):
    id: str
    length: float
    width: float
    height: float
    weight: float
    is_fragile: bool
    max_load_bearing: float = 10000.0 # Default structural limit

class PackingRequest(BaseModel):
    truck: Truck
    cargo: List[CargoItem]

class Coordinate(BaseModel):
    x: float
    y: float
    z: float

class PackedItem(BaseModel):
    id: str
    coordinates: Coordinate
    rotated: bool
    step_sequence: int
    orientation_length: float
    orientation_width: float
    orientation_height: float
    requires_dunnage: bool = False
    dunnage_margin: float = 0.0
    dunnage_left: str = ""
    dunnage_right: str = ""
    dunnage_front: str = ""
    dunnage_back: str = ""
    gap_left_cm: float = 0.0
    gap_right_cm: float = 0.0
    gap_front_cm: float = 0.0
    gap_back_cm: float = 0.0

class PackingResponse(BaseModel):
    status: str
    rejection_reason: Optional[str] = None
    packed_items: List[PackedItem]
    unpacked_ids: List[str]
    left_weight: float
    right_weight: float
    payload_cg: Optional[Coordinate] = None

# --- Core Algorithm ---
def get_extreme_points(packed_items: List[PackedItem], truck_l: float, truck_w: float, truck_h: float) -> List[Coordinate]:
    xs = {0.0}
    ys = {0.0}
    zs = {0.0}
    
    for pi in packed_items:
        xs.add(round(pi.coordinates.x, 4))
        ys.add(round(pi.coordinates.y, 4))
        zs.add(round(pi.coordinates.z, 4))
        xs.add(round(pi.coordinates.x + pi.orientation_length, 4))
        ys.add(round(pi.coordinates.y + pi.orientation_width + pi.dunnage_margin, 4))
        zs.add(round(pi.coordinates.z + pi.orientation_height, 4))
        
    xs = {x for x in xs if x < truck_l}
    ys = {y for y in ys if y < truck_w}
    zs = {z for z in zs if z < truck_h}
    
    eps = []
    for x in xs:
        for y in ys:
            for z in zs:
                inside = False
                for pi in packed_items:
                    px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                    pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                    if px < x < px + pl and py < y < py + pw and pz < z < pz + ph:
                        inside = True
                        break
                if inside: continue
                
                supported_x = (x == 0.0)
                if not supported_x:
                    for pi in packed_items:
                        px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                        pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                        if px + pl == x and py <= y < py + pw and pz <= z < pz + ph:
                            supported_x = True
                            break
                if not supported_x: continue
                
                supported_y = True
                
                supported_z = (z == 0.0)
                if not supported_z:
                    for pi in packed_items:
                        px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                        pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                        if pz + ph == z and px <= x < px + pl and py <= y < py + pw:
                            supported_z = True
                            break
                if not supported_z: continue
                
                eps.append(Coordinate(x=x, y=y, z=z))
    return eps

import time

def apply_dunnage_rules(gap: float, anchor: str) -> str:
    if gap < 1.0: return ""
    if anchor == "wall":
        if gap <= 5.0: return "Corrugated Void Filler"
        if gap <= 30.0: return "Woven Airbag"
        return "Load Bar"
    else:
        if gap <= 5.0: return "Corrugated Void Filler"
        if gap <= 30.0: return "Woven Airbag"
        pallets = int(gap // 15)
        rem = gap % 15
        parts = [f"{pallets}x Empty Pallets"] if pallets > 0 else []
        if rem >= 1.0:
            if rem <= 5.0: parts.append("Corrugated Void Filler")
            elif rem <= 30.0: parts.append("Woven Airbag")
        return ", ".join(parts)

def run_packing_algorithm(request: PackingRequest, degraded_mode: bool, lock_token: str = None) -> PackingResponse:
    pending_items = sorted(request.cargo, key=lambda item: item.weight, reverse=True)
    item_map = {item.id: item for item in request.cargo}
    
    packed_items = []
    truck_l = round(request.truck.length, 4)
    truck_w = round(request.truck.width, 4)
    truck_h = round(request.truck.height, 4)
    
    left_weight, right_weight = 0.0, 0.0
    sequence_counter = 1
    
    cluster_mass = 0.0
    cluster_packed_items = []
    seek_y_max = False
    force_anchor_id = None
    last_heartbeat = time.time()
    
    while pending_items:
        if lock_token and time.time() - last_heartbeat > 45:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE system_locks SET locked_at = CURRENT_TIMESTAMP WHERE id = 'packing_loop' AND lock_owner = ?", (lock_token,))
            conn.commit()
            conn.close()
            last_heartbeat = time.time()
            
        placed_any = False
        
        for item in pending_items.copy():
            best_point = None
            best_orientation = None
            best_rotated = False
            best_dunnage = False
            best_margin = 0.0
            
            if force_anchor_id == item.id:
                orientations = [(item.length, item.width, False), (item.width, item.length, True)]
                if item.length == item.width: orientations = [orientations[0]]
                
                x_boundaries = {0.0}
                z_boundaries = {0.0}
                for pi in packed_items:
                    x_boundaries.add(round(pi.coordinates.x + pi.orientation_length, 4))
                    z_boundaries.add(round(pi.coordinates.z + pi.orientation_height, 4))
                
                x_boundaries = sorted(list(x_boundaries))
                z_boundaries = sorted(list(z_boundaries))
                
                for l, original_w, rotated in orientations:
                    h = item.height
                    w_effective = original_w
                    requires_dunnage = False
                    dunnage_margin = 0.0
                    if item.weight > MANUAL_LIFT_MAX:
                        aspect_ratio = h / max(1.0, original_w)
                        if aspect_ratio >= 1.5:
                            requires_dunnage = True
                            dunnage_margin = 30.0
                            w_effective += dunnage_margin
                            
                    y_anchor = (truck_w / 2.0) - (w_effective / 2.0)
                    if y_anchor < 0 or y_anchor + w_effective > truck_w: continue
                        
                    for z in z_boundaries:
                        if z + h > truck_h: continue
                        for x in x_boundaries:
                            if x + l > truck_l: continue
                            
                            collision = False
                            for pi in packed_items:
                                px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                                pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                                if not (x >= px + pl or x + l <= px or y_anchor >= py + pw or y_anchor + w_effective <= py or z >= pz + ph or z + h <= pz):
                                    collision = True
                                    break
                            if collision: continue
                            
                            supported = True
                            if z > 0:
                                supported_area = 0.0
                                for pi in packed_items:
                                    px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                                    pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                                    if round(pz + ph, 4) == round(z, 4):
                                        ix_min, ix_max = max(x, px), min(x + l, px + pl)
                                        iy_min, iy_max = max(y_anchor, py), min(y_anchor + w_effective, py + pw)
                                        if ix_max > ix_min and iy_max > iy_min:
                                            supported_area += (ix_max - ix_min) * (iy_max - iy_min)
                                if round(supported_area, 4) < round(l * w_effective, 4):
                                    supported = False
                            if not supported: continue
                            
                            crush_violation = False
                            if z > 0:
                                for pi in packed_items:
                                    px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                                    pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                                    if round(pz + ph, 4) == round(z, 4):
                                        ix_min, ix_max = max(x, px), min(x + l, px + pl)
                                        iy_min, iy_max = max(y_anchor, py), min(y_anchor + w_effective, py + pw)
                                        if ix_max > ix_min and iy_max > iy_min:
                                            dynamic_mass = item.weight * (1.5 if item_map[pi.id].is_fragile and request.truck.suspension_type == 'LEAF_SPRING' else 1.0)
                                            if dynamic_mass > item_map[pi.id].max_load_bearing:
                                                crush_violation = True
                                                break
                            if crush_violation: continue
                                
                            best_point = Coordinate(x=x, y=y_anchor, z=z)
                            best_orientation = (l, original_w, h)
                            best_rotated = rotated
                            best_dunnage = requires_dunnage
                            best_margin = dunnage_margin
                            break
                        if best_point: break
                    if best_point: break
                
                if not best_point:
                    return PackingResponse(status="FAILED", packed_items=packed_items, unpacked_ids=[i.id for i in pending_items], left_weight=left_weight, right_weight=right_weight, payload_cg=None)
                force_anchor_id = None
                
            else:
                eps = get_extreme_points(packed_items, truck_l, truck_w, truck_h)
                if seek_y_max:
                    eps.sort(key=lambda p: (p.z, -p.y, p.x))
                else:
                    eps.sort(key=lambda p: (p.z, p.y, p.x))
            

            
                for ep in eps:
                    orientations = [(item.length, item.width, False), (item.width, item.length, True)]
                    if item.length == item.width: orientations = [orientations[0]]
                        
                    for l, original_w, rotated in orientations:
                        h = item.height
                        
                        # Pre-emptive Volumetric Inflation (Dunnage)
                        w_effective = original_w
                        requires_dunnage = False
                        dunnage_margin = 0.0
                        if item.weight > MANUAL_LIFT_MAX:
                            aspect_ratio = h / max(1.0, original_w)
                            if aspect_ratio >= 1.5:
                                requires_dunnage = True
                                dunnage_margin = 30.0
                                w_effective += dunnage_margin
                                
                        y_coord = ep.y
                        
                        if item.weight > MANUAL_LIFT_MAX:
                            if degraded_mode:
                                y_coord = (truck_w / 2.0) - (w_effective / 2.0)
                            else:
                                margin = FORKLIFT_WIDTH / 2.0
                                item_center_y = y_coord + w_effective / 2.0
                                if item_center_y < margin: y_coord = margin - w_effective / 2.0
                                elif item_center_y > (truck_w - margin): y_coord = truck_w - margin - w_effective / 2.0
                                    
                        if ep.x + l > truck_l + 0.001 or y_coord + w_effective > truck_w + 0.001 or ep.z + h > truck_h + 0.001 or y_coord < -0.001:
                            continue
                            
                        collision = False
                        for pi in packed_items:
                            px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                            pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                            if not (ep.x >= px + pl or ep.x + l <= px or y_coord >= py + pw or y_coord + w_effective <= py or ep.z >= pz + ph or ep.z + h <= pz):
                                collision = True
                                break
                        if collision: continue

                        # Material Yield Enforcement (Crush Prevention)
                        crush_violation = False
                        if ep.z > 0:
                            for pi in packed_items:
                                px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                                pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                                if round(pz + ph, 4) == round(ep.z, 4):
                                    ix_min, ix_max = max(ep.x, px), min(ep.x + l, px + pl)
                                    iy_min, iy_max = max(y_coord, py), min(y_coord + w_effective, py + pw)
                                    if ix_max > ix_min and iy_max > iy_min:
                                        dynamic_mass = item.weight * (1.5 if item_map[pi.id].is_fragile and request.truck.suspension_type == 'LEAF_SPRING' else 1.0)
                                        if dynamic_mass > item_map[pi.id].max_load_bearing:
                                            crush_violation = True
                                            break
                        if crush_violation: continue
                            
                        crushes_fragile = False
                        for pi in packed_items:
                            if item_map[pi.id].is_fragile:
                                px, py, pz = round(pi.coordinates.x, 4), round(pi.coordinates.y, 4), round(pi.coordinates.z, 4)
                                pl, pw, ph = round(pi.orientation_length, 4), round(pi.orientation_width + pi.dunnage_margin, 4), round(pi.orientation_height, 4)
                                if pz + ph == ep.z:
                                    if not (ep.x >= px + pl or ep.x + l <= px or y_coord >= py + pw or y_coord + w_effective <= py):
                                        crushes_fragile = True
                                        break
                        if crushes_fragile: continue
                            
                        if sum(item_map[pi.id].weight for pi in packed_items) + item.weight > request.truck.max_weight:
                            continue
                            
                        best_point = Coordinate(x=ep.x, y=y_coord, z=ep.z)
                        best_orientation = (l, original_w, h)
                        best_rotated = rotated
                        best_dunnage = requires_dunnage
                        best_margin = dunnage_margin
                        break 
                    if best_point: break 
                    
            if best_point:
                if not best_point:
                    # Item could not be placed anywhere
                    continue
                    
                l, original_w, h = best_orientation
                w_effective = original_w + best_margin
                
                midline = truck_w / 2.0
                left_portion = max(0.0, min(midline - best_point.y, w_effective))
                right_portion = max(0.0, min((best_point.y + w_effective) - midline, w_effective))
                left_weight += item.weight * (left_portion / w_effective)
                right_weight += item.weight * (right_portion / w_effective)
                
                new_packed = PackedItem(
                    id=item.id, coordinates=best_point, rotated=best_rotated, step_sequence=sequence_counter,
                    orientation_length=l, orientation_width=original_w, orientation_height=h,
                    requires_dunnage=best_dunnage, dunnage_margin=best_margin
                )
                
                # Volumetric Sweeps for Dunnage (Chronological)
                if new_packed.coordinates.z == 0:
                    # Y overlap candidates for X sweep
                    y_overlap = [pi for pi in packed_items if pi.coordinates.y < new_packed.coordinates.y + new_packed.orientation_width + new_packed.dunnage_margin and pi.coordinates.y + pi.orientation_width + pi.dunnage_margin > new_packed.coordinates.y]
                    # X overlap candidates for Y sweep
                    x_overlap = [pi for pi in packed_items if pi.coordinates.x < new_packed.coordinates.x + new_packed.orientation_length and pi.coordinates.x + pi.orientation_length > new_packed.coordinates.x]
                    
                    # Left Sweep (-Y)
                    left_hit = None
                    left_max_y = 0.0
                    for pi in x_overlap:
                        pi_right_edge = pi.coordinates.y + pi.orientation_width + pi.dunnage_margin
                        if pi_right_edge <= new_packed.coordinates.y and pi_right_edge > left_max_y:
                            left_max_y = pi_right_edge
                            left_hit = pi
                    new_packed.gap_left_cm = new_packed.coordinates.y - left_max_y
                    new_packed.dunnage_left = apply_dunnage_rules(new_packed.gap_left_cm, "cargo" if left_hit else "wall")
                    
                    # Right Sweep (+Y)
                    right_hit = None
                    right_min_y = truck_w
                    new_packed_right_edge = new_packed.coordinates.y + new_packed.orientation_width + new_packed.dunnage_margin
                    for pi in x_overlap:
                        pi_left_edge = pi.coordinates.y
                        if pi_left_edge >= new_packed_right_edge and pi_left_edge < right_min_y:
                            right_min_y = pi_left_edge
                            right_hit = pi
                    new_packed.gap_right_cm = right_min_y - new_packed_right_edge
                    new_packed.dunnage_right = apply_dunnage_rules(new_packed.gap_right_cm, "cargo" if right_hit else "wall")
                    
                    # Front Sweep (-X towards cab)
                    front_hit = None
                    front_max_x = 0.0
                    for pi in y_overlap:
                        pi_back_edge = pi.coordinates.x + pi.orientation_length
                        if pi_back_edge <= new_packed.coordinates.x and pi_back_edge > front_max_x:
                            front_max_x = pi_back_edge
                            front_hit = pi
                    new_packed.gap_front_cm = new_packed.coordinates.x - front_max_x
                    new_packed.dunnage_front = apply_dunnage_rules(new_packed.gap_front_cm, "cargo" if front_hit else "wall")
                else:
                    new_packed.dunnage_left = "Stretch-Wrap to Base"
                    
                packed_items.append(new_packed)
                cluster_packed_items.append(new_packed)
                cluster_mass += item.weight
                
                sequence_counter += 1
                pending_items.remove(item)
                placed_any = True
                
                # Cumulative Mass CG Auditing (Heuristic Rollback)
                if cluster_mass >= CUMULATIVE_MASS_THRESHOLD and not degraded_mode:
                    cluster_cg_y = sum((pi.coordinates.y + (pi.orientation_width + pi.dunnage_margin)/2.0) * item_map[pi.id].weight for pi in cluster_packed_items) / cluster_mass
                    if abs(cluster_cg_y - (truck_w / 2.0)) > MAX_CG_DEVIATION:
                        # HEURISTIC ROLLBACK TRIGGERED
                        if not seek_y_max: # Only rollback once per cluster to prevent infinite loop
                            # Re-add items to pending
                            for pi in cluster_packed_items:
                                pending_items.append(item_map[pi.id])
                            # Remove from packed_items
                            packed_items = [p for p in packed_items if p not in cluster_packed_items]
                            # Reset cluster state
                        
                        cluster_mass = 0.0
                        cluster_packed_items = []
                        seek_y_max = True
                        # Recalculate weights
                        left_weight, right_weight = 0.0, 0.0
                        for pi in packed_items:
                            w_eff = pi.orientation_width + pi.dunnage_margin
                            left_p = max(0.0, min(midline - pi.coordinates.y, w_eff))
                            right_p = max(0.0, min((pi.coordinates.y + w_eff) - midline, w_eff))
                            left_weight += item_map[pi.id].weight * (left_p / w_eff)
                            right_weight += item_map[pi.id].weight * (right_p / w_eff)
                        # Sort pending items again
                        pending_items = sorted(pending_items, key=lambda i: i.weight, reverse=True)
                        placed_any = True
                        break # Restart placement with seek_y_max
                    else:
                        # Rollback again, triggering Centerline Anchor for heaviest item
                        heaviest_pi = max(cluster_packed_items, key=lambda pi: item_map[pi.id].weight)
                        force_anchor_id = heaviest_pi.id
                        
                        # Re-add items to pending
                        for pi in cluster_packed_items:
                            pending_items.append(item_map[pi.id])
                        packed_items = [p for p in packed_items if p not in cluster_packed_items]
                        cluster_mass = 0.0
                        cluster_packed_items = []
                        seek_y_max = False # Reset heuristic
                        
                        left_weight, right_weight = 0.0, 0.0
                        for pi in packed_items:
                            w_eff = pi.orientation_width + pi.dunnage_margin
                            left_p = max(0.0, min(midline - pi.coordinates.y, w_eff))
                            right_p = max(0.0, min((pi.coordinates.y + w_eff) - midline, w_eff))
                            left_weight += item_map[pi.id].weight * (left_p / w_eff)
                            right_weight += item_map[pi.id].weight * (right_p / w_eff)
                            
                        pending_items = sorted(pending_items, key=lambda i: (i.id == force_anchor_id, i.weight), reverse=True)
                        placed_any = True
                        break
                
                # Reset cluster if successful or already rolled back
                cluster_mass = 0.0
                cluster_packed_items = []
                seek_y_max = False
            
            break
            
        if not placed_any:
            break

    # === TOPOLOGICAL FILO SEQUENCER (DAG) ===
    machinery_width = 150.0
    in_degrees = {pi.id: 0 for pi in packed_items}
    graph = {pi.id: [] for pi in packed_items}
    
    def rect_intersect(x1, y1, w1, h1, x2, y2, w2, h2):
        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)
    
    # Post-Processing: Rear Doors
    for pi in packed_items:
        if pi.coordinates.z == 0:
            # Sweep +X towards doors
            y_overlap = [other for other in packed_items if other.id != pi.id and other.coordinates.y < pi.coordinates.y + pi.orientation_width + pi.dunnage_margin and other.coordinates.y + other.orientation_width + other.dunnage_margin > pi.coordinates.y]
            pi_back_edge = pi.coordinates.x + pi.orientation_length
            back_min_x = truck_l
            back_hit = None
            for other in y_overlap:
                other_front_edge = other.coordinates.x
                if other_front_edge >= pi_back_edge and other_front_edge < back_min_x:
                    back_min_x = other_front_edge
                    back_hit = other
            
            # If it hit the door (no cargo hit)
            if not back_hit:
                pi.gap_back_cm = truck_l - pi_back_edge
                pi.dunnage_back = apply_dunnage_rules(pi.gap_back_cm, "wall")

    for i in range(len(packed_items)):
        A = packed_items[i]
        for j in range(len(packed_items)):
            if i == j: continue
            B = packed_items[j]
            
            blocks_path = False
            if (B.coordinates.x + B.orientation_length) > (A.coordinates.x + A.orientation_length):
                A_center_y = A.coordinates.y + ((A.orientation_width + A.dunnage_margin) / 2.0)
                corridor_w = max(A.orientation_width + A.dunnage_margin, machinery_width)
                A_corridor_y_min = max(0, A_center_y - (corridor_w / 2.0))
                A_corridor_y_max = min(truck_w, A_center_y + (corridor_w / 2.0))
                B_y_min = B.coordinates.y
                B_y_max = B.coordinates.y + B.orientation_width + B.dunnage_margin
                if B_y_min < A_corridor_y_max and B_y_max > A_corridor_y_min:
                    blocks_path = True
                    
            blocks_gravity = False
            if abs(B.coordinates.z - (A.coordinates.z + A.orientation_height)) < 0.1:
                if rect_intersect(
                    A.coordinates.x, A.coordinates.y, A.orientation_length, A.orientation_width + A.dunnage_margin,
                    B.coordinates.x, B.coordinates.y, B.orientation_length, B.orientation_width + B.dunnage_margin
                ):
                    blocks_gravity = True
                    
            if blocks_path or blocks_gravity:
                graph[A.id].append(B.id)
                in_degrees[B.id] += 1
                
    pq = []
    pi_map = {pi.id: pi for pi in packed_items}
    for pi_id, deg in in_degrees.items():
        if deg == 0:
            pi = pi_map[pi_id]
            heapq.heappush(pq, (pi.coordinates.x, -item_map[pi_id].weight, pi.coordinates.z, pi.coordinates.y, pi.id))
            
    sorted_sequence = []
    while pq:
        _, _, _, _, current_id = heapq.heappop(pq)
        sorted_sequence.append(pi_map[current_id])
        for neighbor_id in graph[current_id]:
            in_degrees[neighbor_id] -= 1
            if in_degrees[neighbor_id] == 0:
                n_pi = pi_map[neighbor_id]
                heapq.heappush(pq, (n_pi.coordinates.x, -item_map[neighbor_id].weight, n_pi.coordinates.z, n_pi.coordinates.y, neighbor_id))
                
    if len(sorted_sequence) != len(packed_items):
        if not degraded_mode:
            return run_packing_algorithm(request, degraded_mode=True)
        else:
            raise TopologicalCycleError("Deadlock detected even in Degraded Mode!")
    else:
        packed_items = sorted_sequence
        
    if not degraded_mode and len(packed_items) != len(request.cargo):
        return run_packing_algorithm(request, degraded_mode=True)

    for index, pi in enumerate(packed_items):
        pi.step_sequence = index + 1
                
    unpacked_ids = [item.id for item in pending_items]
    status = "SUCCESS" if not unpacked_ids else "PARTIAL_SUCCESS"
    
    rejection_reason = None
    if status == "PARTIAL_SUCCESS":
        current_weight = sum(item_map[pi.id].weight for pi in packed_items)
        if any(current_weight + item_map[uid].weight > request.truck.max_weight for uid in unpacked_ids):
            rejection_reason = "WEIGHT"
        else:
            rejection_reason = "VOLUME"
    
    total_packed_weight = sum(item_map[pi.id].weight for pi in packed_items)
    payload_cg = None
    if total_packed_weight > 0:
        cg_x = sum((pi.coordinates.x + pi.orientation_length/2.0) * item_map[pi.id].weight for pi in packed_items) / total_packed_weight
        cg_y = sum((pi.coordinates.y + (pi.orientation_width + pi.dunnage_margin)/2.0) * item_map[pi.id].weight for pi in packed_items) / total_packed_weight
        cg_z = sum((pi.coordinates.z + pi.orientation_height/2.0) * item_map[pi.id].weight for pi in packed_items) / total_packed_weight
        payload_cg = Coordinate(x=cg_x, y=cg_y, z=cg_z)
    
    return PackingResponse(
        status=status,
        rejection_reason=rejection_reason,
        packed_items=packed_items,
        unpacked_ids=unpacked_ids,
        left_weight=left_weight,
        right_weight=right_weight,
        payload_cg=payload_cg
    )

@app.post("/api/v1/optimize", response_model=PackingResponse, dependencies=[Depends(verify_api_key)])
def optimize_packing(request: PackingRequest, degraded_mode: bool = False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    lock_token = str(uuid.uuid4())
    # TTL Mutex to prevent Zombie Locks and multi-click race conditions
    c.execute("""
        UPDATE system_locks 
        SET locked_at = CURRENT_TIMESTAMP, lock_owner = ? 
        WHERE id = 'packing_loop' 
          AND (locked_at IS NULL OR locked_at < datetime('now', '-5 minutes'))
    """, (lock_token,))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=429, detail="Engine Busy. Another packing loop is in progress.")
    conn.commit()
    conn.close()
    
    try:
        response = run_packing_algorithm(request, degraded_mode, lock_token)
        
        # Generous TTL extension before returning/writing (TOCTOU protection)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE system_locks 
            SET locked_at = datetime('now', '+30 seconds') 
            WHERE id = 'packing_loop' AND lock_owner = ?
        """, (lock_token,))
        conn.commit()
        conn.close()
        
        # TODO: Trigger push to Google Sheets API
        return response
    finally:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE system_locks SET locked_at = NULL, lock_owner = NULL WHERE id = 'packing_loop' AND lock_owner = ?", (lock_token,))
        conn.commit()
        conn.close()

@app.get("/api/v1/plans", dependencies=[Depends(verify_api_key)])
def get_plans():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM loading_plans ORDER BY created_at DESC")
    plans = [dict(row) for row in c.fetchall()]
    
    for plan in plans:
        c.execute("SELECT * FROM trucks WHERE id = ?", (plan["truck_id"],))
        plan["trucks"] = dict(c.fetchone())
        c.execute("SELECT * FROM cargo_manifests WHERE id = ?", (plan["manifest_id"],))
        plan["cargo_manifests"] = dict(c.fetchone())
        
    conn.close()
    return plans

@app.get("/api/v1/plans/{plan_id}/steps", dependencies=[Depends(verify_api_key)])
def get_steps(plan_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM loading_plan_steps WHERE plan_id = ? ORDER BY sequence_number ASC", (plan_id,))
    steps = [dict(row) for row in c.fetchall()]
    
    for step in steps:
        c.execute("SELECT * FROM cargo_items WHERE id = ?", (step["cargo_item_id"],))
        step["cargo_items"] = dict(c.fetchone())
        
    conn.close()
    return steps

@app.post("/api/v1/plans/{plan_id}/push-sheets", dependencies=[Depends(verify_api_key)])
def push_to_sheets(plan_id: str):
    """Push a loading plan to Google Sheets. Returns not_configured if env vars are absent."""
    google_creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not google_creds or not sheet_id:
        return {"status": "not_configured", "message": "Google Sheets integration is not configured. Set GOOGLE_SHEETS_CREDENTIALS and GOOGLE_SHEET_ID in .env to enable."}
    
    # TODO: Implement full Sheets push using the plan_id
    return {"status": "ok", "message": f"Plan {plan_id} queued for push."}

def background_spatial_math(manifest_dict: dict):
    # This runs in the separate process, bypassing GIL.
    from app.spatial_matrix import SpatialMatrixEngine, CapacityExceeded
    
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=10000;")
    c = conn.cursor()
    
    manifest_id = manifest_dict["manifest_id"]
    timestamp = manifest_dict["timestamp"]
    operator_id = manifest_dict["operator_id"]
    
    try:
        # Instantiate and execute the spatial matrix engine
        engine = SpatialMatrixEngine(trailer_dict=manifest_dict["trailer"], cargo_list=manifest_dict["cargo"])
        result = engine.execute()
        
        # Insert staging array and loading sequence into database
        staging_json = json.dumps(result["staging_array"])
        loading_json = json.dumps(result["loading_sequence"])
        left_behind_json = json.dumps(result["left_behind"])
        
        txn_uuid = str(uuid.uuid4())
        
        c.execute("""
            INSERT INTO pending_transshipments (manifest_id, operator_id, timestamp, status, staging_array, loading_sequence, left_behind, synced_to_cloud, transaction_uuid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (manifest_id, operator_id, timestamp, "READY", staging_json, loading_json, left_behind_json, 0, txn_uuid))
        conn.commit()
        result["status"] = "READY"
        return manifest_id
    except CapacityExceeded as e:
        c.execute("""
            INSERT INTO pending_transshipments (manifest_id, operator_id, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (manifest_id, operator_id, timestamp, "CAPACITY_EXCEEDED"))
        conn.commit()
        return None
    except Exception as e:
        # Catch unexpected mathematical crashes
        c.execute("""
            INSERT INTO pending_transshipments (manifest_id, operator_id, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (manifest_id, operator_id, timestamp, "FAILED"))
        conn.commit()
        return None
    finally:
        conn.close()

@app.post("/api/v1/sync", status_code=202, dependencies=[Depends(verify_api_key)])
async def sync_manifest(request: SyncManifestRequest, background_tasks: BackgroundTasks):
    manifest_dict = request.model_dump()
    
    async def process_and_queue():
        loop = asyncio.get_running_loop()
        try:
            # Run the synchronous CPU-bound function in the process pool
            mid = await loop.run_in_executor(spatial_process_pool, background_spatial_math, manifest_dict)
            if mid:
                await sheets_queue.put(mid)
        except Exception as e:
            print(f"Spatial math failed: {e}")
            
    background_tasks.add_task(process_and_queue)
    
    return {"status": "Accepted", "message": "Manifest queued for processing."}


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}

@app.post("/api/demo/reset", dependencies=[Depends(verify_api_key)])
async def demo_reset():
    """
    Cleans the slate for a live demonstration.
    Truncates local WAL state and clears the Google Sheets ledger.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Truncate the pending transshipments
    c.execute("DELETE FROM pending_transshipments")
    
    # Reset High-Water Mark
    c.execute("UPDATE system_state SET value_int = 0 WHERE key = 'current_sheet_row_count'")
    
    conn.commit()
    conn.close()
    
    # Wipe the Cloud Ledger
    await clear_sheets()
    
    return {"status": "SUCCESS", "message": "System state has been reset to zero for demonstration."}
