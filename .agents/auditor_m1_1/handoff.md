# Forensic Audit Report — Milestone 1 (M1: Profile System & Single Instance)

**Work Product**: `profile_manager.py`, `single_instance.py`, `main.py`, `browser.py`
**Profile**: General Project
**Integrity Mode**: Development (from `ORIGINAL_REQUEST.md`, line 8)
**Verdict**: CLEAN

---

## 1. Observation

### Source Code Analysis
1. **`profile_manager.py`** (`C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\profile_manager.py`):
   - **Data Model & Validation** (Lines 38–68): `@dataclass class Profile` defines fields (`id`, `name`, `avatar`, `homepage`, `search_engine`, `theme_color`). Post-init sanitizes `search_engine` using `sanitize_search_engine()`. Features `to_dict()`, `from_dict()`, and `get_search_url()`.
   - **Persistence & Atomic Write** (Lines 140–163): `save_profiles()` writes JSON data to a `.tmp` file (`self.json_path + ".tmp"`) and performs atomic replacement using `os.replace()`. Exception handler removes temporary file if an error occurs.
   - **CRUD Operations** (Lines 164–239): Implements `get_all_profiles()`, `get_profile_by_id()`, `get_active_profile()`, `set_active_profile()`, `create_profile()`, `update_profile()`, and `delete_profile()`. Prevents deleting the last profile (`len(self.profiles) <= 1` check on line 225) and auto-reassigns active profile if active profile is deleted (lines 234–235).
   - **Off-The-Record Web Engine Profile** (Lines 241–252): `create_otr_web_profile()` instantiates a `QWebEngineProfile`, sets `NoPersistentCookies` policy, `MemoryHttpCache` cache type, and sets `persistentStoragePath` and `cachePath` to `""`.

2. **`single_instance.py`** (`C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\single_instance.py`):
   - **Signal Declaration** (Lines 31–32): `activation_requested = pyqtSignal()` with alias `activated = activation_requested`.
   - **Deterministic Server Naming** (Lines 40–47): `_get_server_name()` generates OS-safe socket server names using `getpass.getuser()` and `hashlib.sha256` for long keys.
   - **IPC Client/Server Acquisition** (Lines 49–95): `try_acquire()` validates non-empty keys, attempts `QLocalSocket.connectToServer(server_name)`, writes `b"ACTIVATE\n"` on connection success, flushes socket, flushes event loop via `QCoreApplication.processEvents()`, and returns `False` for secondary instances. If connection fails, invokes `QLocalServer.removeServer(server_name)` to clear stale pipe files, instantiates `QLocalServer`, calls `listen(server_name)`, and connects `newConnection` signal to `_on_new_connection()`.
   - **IPC Signal Handling** (Lines 96–111): `_on_new_connection()` processes pending client connections, reads byte streams, emits `activation_requested`, and closes socket connections cleanly.
   - **Lock Release** (Lines 112–130): `release()` idempotently closes the server and invokes `QLocalServer.removeServer()`.

3. **`main.py` & `browser.py` Integration**:
   - `main.py` (Lines 44–49): Instantiates `SingleInstanceGuard("PhantomBrowserApp")`. If `try_acquire()` returns `False`, logs secondary instance detection and executes `sys.exit(0)`. Connects `guard.activated` to `browser.activate_window_to_front`.
   - `browser.py` (Lines 74–76, 88–96): Initializes `ProfileManager` and `create_otr_web_profile`. Implements `activate_window_to_front()` invoking `show()`, `showNormal()`, `raise_()`, and `activateWindow()`.

### Empirical Test Execution Results

- **Command 1**: `pytest tests/test_profiles.py tests/test_single_instance.py -v`
  - Output: `20 passed in 3.99s`
  - Test list:
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier1_active_profile_switch PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier1_default_profile_creation PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier1_otr_web_profile_creation PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier1_profile_crud_operations PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier1_profile_persistence PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier2_corrupt_json_fallback PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier2_delete_active_profile PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier2_delete_last_profile_prevention PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier2_invalid_search_engine_validation PASSED`
    - `tests/test_profiles.py::TestProfilesManagerAndSchema::test_tier2_special_char_profile_names PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier1_activation_signal_emitted PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier1_ipc_socket_connection PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier1_primary_instance_acquisition PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier1_release_and_reacquire PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier1_secondary_instance_rejection PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier2_empty_app_key_handling PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier2_long_app_key_truncation PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier2_multiple_releases_idempotent PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier2_rapid_concurrent_acquire_attempts PASSED`
    - `tests/test_single_instance.py::TestSingleInstanceEnforcement::test_tier2_stale_server_cleanup PASSED`

- **Command 2**: `pytest tests/ -v`
  - Output: `91 passed in 11.62s`

---

## 2. Logic Chain

1. **Verification of Non-Hardcoding & Authentic Logic**:
   - Source code analysis of `profile_manager.py` and `single_instance.py` demonstrates that all methods execute actual data processing (JSON encoding/decoding, atomic file replacement, OS-level IPC socket creation, signal emissions).
   - No hardcoded string comparisons or shortcut values exist to pass unit tests without performing real work.

2. **Verification of Single-Instance IPC**:
   - `SingleInstanceGuard` uses Qt's native `QLocalServer` and `QLocalSocket` to create local IPC server/sockets on Windows named pipes.
   - Secondary process connects, writes activation bytes (`b"ACTIVATE\n"`), and cleanly yields execution to the primary instance. Primary instance server slot reads the connection, emits `activation_requested`, which triggers `browser.activate_window_to_front()`.

3. **Verification of Persistence & Ephemeral OTR Profiles**:
   - `ProfileManager` implements complete CRUD operations backed by atomic JSON writes (`.tmp` file + `os.replace`).
   - `create_otr_web_profile` configures `QWebEngineProfile` with `NoPersistentCookies`, memory cache, and empty storage/cache paths, ensuring zero cookie or browsing history persistence on disk.

4. **Verification of Facade Absences**:
   - No dummy functions, unimplemented placeholders, or stub methods were detected in `profile_manager.py`, `single_instance.py`, `main.py`, or `browser.py`.

---

## 3. Caveats

- Tests were run in a Windows environment using Qt offscreen platform (`QT_QPA_PLATFORM=offscreen`). OS IPC mechanisms (`QLocalServer`/`QLocalSocket`) function identically regardless of GUI rendering engine.
- No caveats regarding code completeness or integrity.

---

## 4. Conclusion

**Verdict: CLEAN**

All code written for Milestone 1 (`profile_manager.py`, `single_instance.py`, `main.py`, `browser.py`) represents genuine, authentic implementation. No hardcoded test responses, facades, shortcuts, or integrity violations were found. All 20 targeted unit tests and all 91 total project tests pass cleanly.

---

## 5. Verification Method

To independently re-verify this forensic verdict:

1. **Run M1 Unit Tests**:
   ```powershell
   pytest tests/test_profiles.py tests/test_single_instance.py -v
   ```
   *Expected Result*: 20 PASSED.

2. **Run Entire Project Test Suite**:
   ```powershell
   pytest tests/ -v
   ```
   *Expected Result*: 91 PASSED.

3. **Inspect Source Files**:
   - `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\profile_manager.py`
   - `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\single_instance.py`
   - `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\main.py`
   - `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\browser.py`
