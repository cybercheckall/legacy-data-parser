# Scope: Milestone 1 (M1: Profile System & Single Instance)

## Architecture
- Module: `profile_manager.py` (Profile management data model, persistence, and OTR Qt WebEngine profile generation)
- Module: `single_instance.py` (Single instance application guard using Qt Local IPC server/socket)

## Scope Detail

### 1. `profile_manager.py`
- **Data Model**:
  - `Profile` class / schema with fields: `id` (str/UUID), `name` (str), `avatar` (str/path/icon), `homepage` (str), `search_engine` (str), `theme_color` (str).
- **Persistence**:
  - `profiles.json` storage management (loading, saving, defaulting).
- **CRUD Operations**:
  - Create profile
  - Get profile by ID
  - List all profiles
  - Update profile attributes
  - Delete profile (and clean associated data)
- **Qt WebEngine Ephemeral Profile Generator**:
  - Generator function/method producing Off-The-Record (OTR) `QWebEngineProfile` instance (or off-the-record profile configuration) ensuring:
    - Ephemeral session (isOffTheRecord() returns True)
    - No cookies, browsing history, or disk cache saved to disk.

### 2. `single_instance.py`
- **`SingleInstanceGuard` class**:
  - Uses `QLocalServer` and `QLocalSocket` for cross-process IPC on local machine (named socket / pipe).
  - On launch: attempts connection to `QLocalServer` socket name.
  - If connection succeeds (existing instance running):
    - Sends activation message/signal to existing primary instance.
    - Instructs existing instance to bring window to foreground (`showNormal()`, `show()`, `raise_()`, `activateWindow()`).
    - Second instance exits cleanly with exit code 0.
  - If connection fails (primary instance):
    - Starts `QLocalServer` listening for subsequent instance activation messages.
    - Connects server signal to activate/raise window callback.

## Unit Testing & Verification Requirements
- Verification unit tests for profile CRUD and json persistence.
- Verification unit tests for ephemeral OTR QWebEngineProfile properties.
- Verification unit tests for single instance IPC server/socket detection and message dispatch.
