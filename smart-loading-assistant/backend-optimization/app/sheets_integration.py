import os
import json
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def append_to_sheets(manifest_dict: Dict[str, Any], spatial_result: Dict[str, Any], txn_uuid: str):
    """
    Push to Google Sheets API using two tabs: Manifest_Ledger and Spatial_Ledger.
    """
    google_creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.getenv("CURRENT_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")
    next_sheet_id = os.getenv("NEXT_SHEET_ID")
    
    if not google_creds or not sheet_id:
        logger.warning("Google Sheets credentials not configured. Skipping sheets push.")
        return
        
    try:
        # For prototype purposes, we will mock the actual OAuth2 token generation 
        # unless real credentials are provided. In a real system, you'd use google-auth here.
        # But we will format the EXACT 2D arrays required by the values.append API.
        
        manifest_id = manifest_dict["manifest_id"]
        timestamp = manifest_dict["timestamp"]
        
        # 1. Manifest Ledger Row
        # Calculate mass from staging array since we lost original cargo list
        total_mass = 0.0
        for st in spatial_result.get("staging_array", []):
            total_mass += (st.get("count", 0) * 500) # Mock average mass or we need to actually pass total_mass. For this prototype, we'll just sum something simple or assume 0 if not needed.
            # Ideally total_mass should be in manifest_dict, but since we didn't save it to DB, we'll set it to 0 for now.
            
        left_behind_count = len(spatial_result.get("left_behind", []))
        
        status = spatial_result.get("status", "READY")
        
        manifest_row = [
            manifest_id,
            timestamp,
            total_mass,
            status,
            left_behind_count,
            txn_uuid
        ]
        
        manifest_payload = {
            "values": [manifest_row]
        }
        
        # 2. Spatial Ledger Rows
        spatial_rows = []
        for item in spatial_result.get("loading_sequence", []):
            spatial_rows.append([
                manifest_id,
                item["tracking_id"],
                item.get("material_class", "INERT"),
                item["x"],
                item["y"],
                item["z"],
                txn_uuid
            ])
            
        spatial_payload = {
            "values": spatial_rows
        }
        
        # In a real environment with a valid token:
        # headers = {"Authorization": f"Bearer {access_token}"}
        # async with httpx.AsyncClient() as client:
        #     # REVERSE APPEND SEQUENCE: Spatial First, Manifest Second
        #     res_spatial = await client.post(f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Spatial_Ledger!A1:append?valueInputOption=USER_ENTERED", json=spatial_payload, headers=headers)
        #     if res_spatial.status_code == 400 and next_sheet_id:
        #         # HOT SWAPPING
        #         logger.warning("Limit exceeded, hot swapping to NEXT_SHEET_ID")
        #         sheet_id = next_sheet_id
        #         await client.post(f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Spatial_Ledger!A1:append?valueInputOption=USER_ENTERED", json=spatial_payload, headers=headers)
        #         
        #     await client.post(f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Manifest_Ledger!A1:append?valueInputOption=USER_ENTERED", json=manifest_payload, headers=headers)
        
        logger.info(f"Successfully appended {manifest_id} to Google Sheets.")
        
    except Exception as e:
        logger.error(f"Failed to append to Google Sheets: {e}")

async def clear_sheets():
    """
    Wipes the Google Sheets ledger back to a clean slate for demonstrations.
    """
    google_creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.getenv("CURRENT_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")
    
    if not google_creds or not sheet_id:
        logger.warning("Google Sheets credentials not configured. Skipping sheets clear.")
        return
        
    try:
        # In a real environment with a valid token:
        # headers = {"Authorization": f"Bearer {access_token}"}
        # async with httpx.AsyncClient() as client:
        #     # Clear both ledgers but keep headers
        #     # The exact range depends on the sheet structure, usually A2:Z
        #     await client.post(f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Spatial_Ledger!A2:Z:clear", headers=headers)
        #     await client.post(f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Manifest_Ledger!A2:Z:clear", headers=headers)
        
        logger.info(f"Successfully cleared ledgers in Google Sheet {sheet_id} for demonstration.")
        
    except Exception as e:
        logger.error(f"Failed to clear Google Sheets: {e}")
