# Antigravity Logistics System: Operational Constitution

**Role**: Lead Enterprise Software Architect
**Purpose**: This document serves as the immutable architectural contract for the Smart Loading Assistant system. It must be parsed and adhered to before the execution of any code generation, refactoring, or feature addition tasks.

---

## 1. Core Immutables (Data Integrity)
* **Architecture**: The FastAPI queue and SQLite Write-Ahead Logging (WAL) buffer backing the Google Sheets dual-ledger are the absolute source of truth.
* **Constraint**: These mechanisms **cannot be altered, bypassed, or refactored away**. They must remain intact to prevent race conditions and ensure data sync continuity between the local processing nodes and the cloud ledger.

## 2. Authentication Strictness (Security)
* **Architecture**: The system relies on a JWT OAuth2 loop utilizing `OAuth2PasswordBearer`.
* **Constraint**: The JWT token loop **must** wrap all dashboard data and sensitive endpoints. 
* **Prohibition**: Mock logins, hardcoded credential bypasses, or disabling the token interceptors are strictly prohibited in any environment (including local dev). 

## 3. UI/3D Boundaries (TresJS WebGL)
* **Architecture**: The frontend utilizes TresJS for 3D spatial rendering of the cargo manifests.
* **Constraint**: The WebGL engine must retain dynamic material binding for hazardous cargo. 
* **Requirement**: Hazardous items require dual-indicators:
  1. A distinct emissive color rendering (e.g., `#FF0000`) applied globally.
  2. Secondary accessibility indicators (e.g., floating `<Html>` labels like `[!] HAZMAT` or warning textures) that render conditionally on interaction (hover/click) to preserve WebGL performance.

## 4. Deployment Reality (Infrastructure)
* **Architecture**: The system is split into two distinct hosting environments:
  * **Frontend**: Deployed on Netlify.
  * **Backend**: Deployed on Render/Railway.
* **Constraint**: The backend runs on a strict **"1 Max Instance"** rule. This is a hard infrastructure constraint designed to prevent SQLite database locking and concurrency corruption. Scaling out via multiple instances is explicitly forbidden.

## 5. Code Modification Protocol (Regression Prevention)
* **Rule**: Never remove existing modular functions, routes, or Vue components in an attempt to "simplify" a file.
* **Action**: Only **append** new logic or **integrate** cleanly with existing structures.
* **Deprecation**: If a deprecation or removal is absolutely necessary due to a fundamental architecture shift, you must halt execution and ask for **explicit user permission** before deleting code.
