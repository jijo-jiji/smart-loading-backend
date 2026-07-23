from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

def test_sync_manifest_returns_202_fast():
    payload = {
        "manifest_id": "test-uuid-1234",
        "operator_id": "test-op-456",
        "timestamp": "2026-07-19T20:06:00Z",
        "device_id": "test-device-789",
        "trailer": {
            "length": 16.15,
            "width": 2.59,
            "height": 2.74,
            "max_weight": 20000.0
        },
        "cargo": [
            {
                "tracking_id": "crypto-hash-abc",
                "weight": 12.5,
                "length": 1.2,
                "width": 0.8,
                "height": 1.0,
                "material_class": "INERT"
            }
        ]
    }
    
    start_time = time.time()
    response = client.post("/api/v1/sync", json=payload)
    end_time = time.time()
    
    assert response.status_code == 202
    assert response.json() == {"status": "Accepted", "message": "Manifest queued for processing."}
    
    # Assert it returns quickly (under 100ms) despite the background math sleeping for 1s
    assert (end_time - start_time) < 0.1

def test_spatial_matrix_cpu_time():
    import time
    from app.spatial_matrix import SpatialMatrixEngine
    
    trailer = {
        "length": 16.15,
        "width": 2.59,
        "height": 2.74,
        "max_weight": 20000.0
    }
    
    cargo = [] # Generate 10 random pallets for pure python timing
    # Generate 10 random pallets
    import random
    for i in range(10):
        cargo.append({
            "tracking_id": f"pallet-{i}",
            "weight": random.uniform(50, 150),
            "length": 1.2,
            "width": 1.0,
            "height": random.uniform(0.5, 1.5),
            "max_load_bearing": random.uniform(500, 5000),
            "material_class": random.choice(["INERT", "HAZMAT", "FRAGILE"])
        })
        
    engine = SpatialMatrixEngine(trailer, cargo)
    
    start_time = time.process_time()
    result = engine.execute()
    cpu_time = time.process_time() - start_time
    
    # Assert execution took less than 1.0 second CPU time
    assert cpu_time < 1.0
    
    # Ensure keys exist
    assert "loading_sequence" in result
    assert "staging_array" in result
    assert "left_behind" in result
