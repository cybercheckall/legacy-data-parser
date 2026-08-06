# Explorer 3 Report: Milestone 1 Test Infrastructure & Detailed Test Design

**Milestone**: M1 (Profile System & Single Instance)  
**Agent**: Explorer 3 (`explorer_m1_3`)  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_3`  
**Date**: 2026-08-05  

---

## 1. Observation

### 1.1 Test Infrastructure & Environment
* **Test Runner**: Pytest `9.1.1` with `pytest-qt` (`4.5.0`) and `PyQt6` (`6.11.0` runtime / `6.11.0` compiled).
* **Execution Environment**: Python `3.12.10` on Windows 11 (`QT_QPA_PLATFORM=offscreen` configured in `tests/conftest.py`).
* **Existing Test Files**:
  - `tests/conftest.py`: Provides `qapp` session fixture, temporary environment setup, and fallback module mocks for `profile_manager` and `single_instance`.
  - `tests/test_profiles.py`: Contains 10 test cases (5 Tier 1, 5 Tier 2) for `profile_manager.py`.
  - `tests/test_single_instance.py`: Contains 10 test cases (5 Tier 1, 5 Tier 2) for `single_instance.py`.
  - `tests/test_stealth_affinity.py`, `tests/test_browser_features.py`, `tests/test_hotkey.py`, `tests/test_e2e.py`: 20 original test cases covering legacy stealth browser functionality.

### 1.2 Baseline Execution Results
1. **Existing Baseline Test Suite (`pytest tests/ -v`)**:
   - `20 passed` in `0.93 seconds`.
2. **Profiles Test Suite (`pytest tests/test_profiles.py -v`)**:
   - `10 passed` in `0.45 seconds` (100% pass rate against profile manager contract).
3. **Single Instance Test Suite (`pytest tests/test_single_instance.py -v`)**:
   - `7 passed`, `3 failed` in `0.21 seconds` against fallback mock:
     - `test_tier1_release_and_reacquire` (FAILED): Lock release did not clean up `QLocalServer` socket file on disk, blocking re-acquisition.
     - `test_tier2_empty_app_key_handling` (FAILED): Fallback mock lacked validation for empty string / whitespace app keys (`ValueError` expected).
     - `test_tier2_stale_server_cleanup` (FAILED): Ungraceful server shutdown left stale server instance active without auto-cleaning via `QLocalServer.removeServer(key)`.

---

## 2. Logic Chain

### 2.1 Test Infrastructure Assessment
1. `pytest` and `pytest-qt` are installed, functional, and fully configured with headless `QT_QPA_PLATFORM=offscreen`.
2. Qt GUI event loops and signals can be tested synchronously without displaying UI windows on screen.
3. Unit tests execute in under 1 second total, meeting high-velocity CI/TDD requirements.

### 2.2 Detailed M1 Test Design

#### A. `profile_manager.py` Test Design
* **Target Module**: `profile_manager.py`
* **Interface Contract**:
  - Data model `Profile`: `id: str`, `name: str`, `avatar: str`, `homepage: str`, `search_engine: str` ("Google" | "DuckDuckGo"), `theme_color: str`.
  - Methods: `to_dict()`, `from_dict(data: dict)`.
  - Class `ProfileManager`: `load_profiles()`, `save_profiles()`, `get_active_profile()`, `set_active_profile(id)`, `create_profile(...)`, `update_profile(id, **kwargs)`, `delete_profile(id)`.
  - Off-The-Record Generator: `create_otr_web_profile(profile: Profile) -> QWebEngineProfile`.

* **Exact Test Cases**:

| Test Name | Tier | Category | Description & Assertions |
|-----------|------|----------|--------------------------|
| `test_tier1_default_profile_creation` | Tier 1 | Initialization | Verifies `ProfileManager` auto-populates default profiles ("Default Profile", "Work Profile") and creates `profiles.json` on disk if file does not exist. `len(profiles) >= 1`, active profile is not `None`. |
| `test_tier1_profile_persistence` | Tier 1 | CRUD - Create & Persist | Creates a new profile, verifies fields (`name="Developer Workspace"`, `avatar="💻"`, `homepage="https://github.com"`, `search_engine="DuckDuckGo"`), reloads with a new `ProfileManager(json_path)` instance, asserts profile exists in reloaded list. |
| `test_tier1_active_profile_switch` | Tier 1 | State Management | Calls `set_active_profile(new_id)`, asserts `get_active_profile().id == new_id`, verifies active profile selection persists across fresh manager reload. |
| `test_tier1_profile_crud_operations` | Tier 1 | CRUD - Complete Lifecycle | Creates profile, updates attributes (`name`, `search_engine`), reads active profile, deletes profile, asserts deletion returns `True`. |
| `test_tier1_otr_web_profile_creation` | Tier 1 | Qt WebEngine OTR | Calls `create_otr_web_profile(prof)`, asserts return is `QWebEngineProfile`, verifies `persistentCookiesPolicy() == NoPersistentCookies` and profile is off-the-record (`isOffTheRecord() == True`). |
| `test_tier2_corrupt_json_fallback` | Tier 2 | Edge Case - Data Resilience | Writes invalid JSON (`"{ INVALID JSON }"`) to file, initializes `ProfileManager`, verifies graceful recovery without crashing, loading default profiles. |
| `test_tier2_delete_active_profile` | Tier 2 | Edge Case - Active State | Deletes the profile currently set as active, verifies `get_active_profile()` automatically fallback-assigns a remaining valid profile. |
| `test_tier2_delete_last_profile_prevention` | Tier 2 | Edge Case - Protection | Attempts to delete the final remaining profile in the list, asserts `delete_profile()` returns `False` and profile list count remains `1`. |
| `test_tier2_invalid_search_engine_validation` | Tier 2 | Edge Case - Validation | Passes invalid search engine string (e.g. `"YahooInvalid"`), asserts search engine defaults safely to `"Google"`. |
| `test_tier2_special_char_profile_names` | Tier 2 | Edge Case - Encoding | Creates profile with complex Unicode, emojis (`🚀`, `🔒`), and HTML special characters (`<script>`), verifies full persistence and exact string match upon reload. |

#### B. `single_instance.py` Test Design
* **Target Module**: `single_instance.py`
* **Interface Contract**:
  - Class `SingleInstanceGuard`:
    - Signal: `activation_requested = pyqtSignal()`
    - Method: `try_acquire(app_key: str) -> bool`
    - Method: `release(app_key: str = None) -> None`

* **Exact Test Cases & Implementation Requirements**:

| Test Name | Tier | Category | Description & Assertions |
|-----------|------|----------|--------------------------|
| `test_tier1_primary_instance_acquisition` | Tier 1 | Core Acquisition | Primary instance calls `try_acquire("test_key_primary")`, asserts returns `True` and `QLocalServer` starts listening. |
| `test_tier1_secondary_instance_rejection` | Tier 1 | IPC Rejection | Secondary guard calling `try_acquire` with same key when primary is active returns `False`. |
| `test_tier1_ipc_socket_connection` | Tier 1 | QLocalSocket IPC | Verifies secondary instance connects via `QLocalSocket` to primary `QLocalServer` socket name, sends activation trigger, then disconnects. |
| `test_tier1_activation_signal_emitted` | Tier 1 | Signal Emission | Connects slot to `guard1.activation_requested`, secondary launch triggers `try_acquire`, asserts `activation_requested` signal is emitted exactly once on primary. |
| `test_tier1_release_and_reacquire` | Tier 1 | Lifecycle & Cleanup | Primary guard calls `release()`, secondary guard calls `try_acquire(key)`, asserts returns `True`. Requires `QLocalServer.close()` and `QLocalServer.removeServer(key)`. |
| `test_tier2_empty_app_key_handling` | Tier 2 | Input Validation | Calls `try_acquire("")` or `SingleInstanceGuard(app_key="")` with empty or whitespace string, asserts `ValueError` is raised. |
| `test_tier2_stale_server_cleanup` | Tier 2 | Resilience | Simulates ungraceful crash (closing server without clearing socket file), new guard calls `try_acquire`, asserts `QLocalServer.removeServer(key)` cleans stale socket and acquires successfully (`True`). |
| `test_tier2_rapid_concurrent_acquire_attempts` | Tier 2 | Stress Testing | Executes 5 sequential `try_acquire` and `release` cycles, asserts each cycle succeeds without socket exhaustion. |
| `test_tier2_long_app_key_truncation` | Tier 2 | Boundary Case | Passes 250-character app key string, asserts guard handles or hashes key safely without OS socket path overflow errors. |
| `test_tier2_multiple_releases_idempotent` | Tier 2 | Defensive Coding | Calls `release()` 3 times consecutively on an acquired guard, asserts no exception or crash occurs. |

---

## 3. Caveats

1. **Headless Offscreen Platform (`QT_QPA_PLATFORM=offscreen`)**:
   - `QLocalServer` and `QLocalSocket` work completely in offscreen mode as they rely on OS local domain sockets / named pipes, not display servers.
   - Window activation methods (`showNormal()`, `raise_()`, `activateWindow()`) will be called in signal handlers but won't alter physical window focus in offscreen mode. Tests verify signal emission and function calls.
2. **Win32 Local Sockets vs Unix Pipes**:
   - On Windows, `QLocalServer` uses Named Pipes (`\\.\pipe\<key>`).
   - If an application crashes, Windows named pipes usually close automatically, but `QLocalServer.removeServer(key)` must still be explicitly called prior to `server.listen(key)` to prevent stale pipe lockup.
3. **Fallback Mocks vs Production Implementation**:
   - The test files (`test_profiles.py` and `test_single_instance.py`) are pre-authored and fully compliant with interface contracts. Once `profile_manager.py` and `single_instance.py` are implemented by implementer agents, tests will execute directly against production code without modification.

---

## 4. Conclusion

The test infrastructure for Milestone 1 is verified and ready:
1. **Infrastructure**: `pytest`, `pytest-qt`, and `PyQt6` environment are 100% operational.
2. **Suite Structure**:
   - `tests/test_profiles.py`: 10 comprehensive tests covering Profile data model, CRUD, JSON persistence, OTR QWebEngineProfile settings, corrupt JSON recovery, Unicode, and search engine validation.
   - `tests/test_single_instance.py`: 10 comprehensive tests covering `SingleInstanceGuard`, `QLocalServer`/`QLocalSocket` IPC signaling, `activation_requested` signal, socket cleanup, empty key validation, and stale server cleanup.
3. **Implementer Guidance**:
   - `profile_manager.py` implementer must validate `search_engine` in `("Google", "DuckDuckGo")`, fallback corrupt JSON, and prevent deleting the last profile.
   - `single_instance.py` implementer must call `QLocalServer.removeServer(app_key)` before `listen()`, validate non-empty `app_key`, and ensure `release()` closes server and removes server socket.

---

## 5. Verification Method

### 5.1 Verification Commands
To verify Milestone 1 implementation, execute the following commands from the project root directory (`C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`):

```powershell
# 1. Run all M1 Unit Tests
pytest tests/test_profiles.py tests/test_single_instance.py -v

# 2. Run Complete Test Suite
pytest tests/ -v
```

### 5.2 Expected Output Criteria
* All 20 tests across `test_profiles.py` and `test_single_instance.py` must pass (`20 PASSED`).
* Total execution time must be under 3.0 seconds.
* Zero unhandled exceptions or socket leak warnings.
