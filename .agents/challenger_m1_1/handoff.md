# Handoff & Challenge Report — Challenger 1 (Milestone 1)

**Verdict: REQUEST_CHANGES**

---

## 1. Observation

During empirical stress testing and adversarial edge-case analysis of Milestone 1 (`profile_manager.py`, `single_instance.py`), the following exact behaviors and failures were observed:

### Finding 1: Signal Duplication in SingleInstanceGuard (CRITICAL)
- **Command Executed**: `pytest tests/test_m1_stress_and_edge.py -v`
- **Error Output**:
  ```text
  FAILED tests/test_m1_stress_and_edge.py::TestM1SingleInstanceAdversarial::test_activation_signal_duplication_check
  AssertionError: 2 != 1 : Signal emitted 2 times, expected exactly 1.
  ```
- **Code Reference**: `single_instance.py`, lines 96–110 (`_on_new_connection`).
- **Observed Behavior**: Connecting a secondary instance via `QLocalSocket` triggers `SingleInstanceGuard._on_new_connection()`. Inside this method, line 104 invokes `client.waitForReadyRead(200)` synchronously within the `newConnection` signal handler. The nested Qt event loop execution causes Qt to re-enter or re-dispatch `_on_new_connection()`, emitting `self.activation_requested` **TWICE** for a single secondary application launch attempt.

### Finding 2: Silent Storage Save Failures in ProfileManager (MEDIUM)
- **Code Reference**: `profile_manager.py`, lines 140–163 (`save_profiles`), line 191 (`create_profile`), line 212 (`update_profile`), line 224 (`delete_profile`).
- **Observed Behavior**: `save_profiles()` catches all file writing exceptions (`except Exception as e: logger.error(...)`) and suppresses them without returning a boolean status or raising an exception. Callers (`create_profile`, `update_profile`, `delete_profile`, `set_active_profile`) proceed as if persistence succeeded. If the disk write fails (e.g., file lock, read-only filesystem, permission error), profile changes remain in-memory only and vanish upon application restart with no feedback to the user or caller.

### Positive Empirical Findings:
- **Ephemeral OTR Storage**: `create_otr_web_profile` correctly enforces `isOffTheRecord() == True`, `PersistentCookiesPolicy.NoPersistentCookies`, and `HttpCacheType.MemoryHttpCache`. Empirically verified zero persistent cookie databases or disk cache files created during page instantiation.
- **Corrupt JSON Matrix**: `ProfileManager` successfully recovers from 10 distinct JSON file corruptions (empty files, truncated strings, malformed syntax, array roots, null fields, invalid types) by re-initializing defaults.
- **Extreme Keys & Garbage IPC**: `SingleInstanceGuard` handles 1,000-character keys safely via SHA-256 hashing and withstands garbage binary streams (500KB random bytes) without crashing or hanging.

---

## 2. Logic Chain

1. **SingleInstanceGuard Event Loop Re-entrancy**:
   - `SingleInstanceGuard` connects `QLocalServer.newConnection` to `self._on_new_connection`.
   - When a secondary instance connects, `_on_new_connection` executes.
   - `client.bytesAvailable()` is 0 at the moment of connection establishment, causing `client.waitForReadyRead(200)` to execute.
   - `waitForReadyRead(200)` spins a nested Qt event loop while `_on_new_connection` is already active on the stack.
   - During nested event loop processing, readyRead / disconnection events trigger re-entrance, firing `self.activation_requested.emit()` a second time.
   - *Impact*: Any listener (e.g., `PhantomBrowser.activate_window_to_front`) receives duplicate activation signals for every secondary launch, causing redundant window operations and failing exact-signal contract requirements.

2. **Silent File Write Suppression in ProfileManager**:
   - `ProfileManager.save_profiles()` wraps atomic temporary file creation (`.tmp`) and `os.replace` inside `try...except Exception`.
   - When an exception occurs (e.g., `PermissionError`, disk full), `save_profiles()` logs an error and swallows the exception without returning `False` or re-raising.
   - Methods like `create_profile`, `update_profile`, `set_active_profile`, and `delete_profile` do not receive any failure signal and report success to callers.
   - *Impact*: In-memory state diverges silently from disk state. Users believe their profile was saved, but on restart all changes are lost.

---

## 3. Caveats

- **Offscreen Qt Rendering**: Verification was conducted in Windows environment using `QT_QPA_PLATFORM=offscreen`. `QLocalServer` / `QLocalSocket` utilize Windows Named Pipes (`\\.\pipe\...`), which operate independently of display drivers.
- **Implementation Scope**: As Challenger, implementation source code files (`single_instance.py`, `profile_manager.py`) were NOT modified. The stress test suite `tests/test_m1_stress_and_edge.py` was created to empirically document defects and verify fixes.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

The Milestone 1 implementation is mostly solid in profile schema validation and OTR security, but fails critical single-instance signal contract tests due to duplicate IPC signal emissions caused by event loop re-entrancy in `SingleInstanceGuard`. Additionally, `ProfileManager` suffers from silent persistence failures.

### Required Remediations for Worker:
1. **Fix `SingleInstanceGuard._on_new_connection`**: Avoid blocking `waitForReadyRead()` inside the `newConnection` slot. Connect to `client.readyRead` or process incoming socket data asynchronously without spinning nested event loops inside slots. Ensure `activation_requested` is emitted exactly once per secondary launch.
2. **Propagate Persistence Errors in `ProfileManager`**: Modify `save_profiles()` to return `bool` (or raise `IOError`/`OSError`) and update `create_profile`, `update_profile`, `delete_profile`, and `set_active_profile` to handle or return save success/failure status.

---

## 5. Verification Method

To verify the defects and validate future fixes:

1. **Run Full M1 Test Suite & Stress Suite**:
   ```powershell
   pytest tests/test_profiles.py tests/test_single_instance.py tests/test_m1_stress_and_edge.py -v
   ```
   *Current Result*: `test_activation_signal_duplication_check` FAILS (`AssertionError: 2 != 1`).
   *Passing Invalidation Condition*: All tests in `test_single_instance.py` and `test_m1_stress_and_edge.py` pass cleanly with 0 failures.

2. **Run Full Project Test Suite**:
   ```powershell
   pytest tests/ -v
   ```

---

## Stress Test Results Summary

| Stress Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|
| Rapid Profile CRUD (50 profiles create/update/delete) | Persist and manage active profiles cleanly | All 50 created/updated/deleted properly | **PASS** |
| JSON Corruption Matrix (10 malformed JSON variants) | Fall back to safe default profiles | Safely initialized clean defaults | **PASS** |
| Path Traversal / Script Injections in Profile Name | Sanitize and store safely | Handled intact without crash/corruption | **PASS** |
| Extreme App Keys (300-1000 chars) | Deterministic pipe name via SHA-256 hash | Truncated/hashed cleanly | **PASS** |
| Garbage IPC Payload Bombardment (500KB binary) | Server ignores garbage without crashing | Server remains responsive | **PASS** |
| Concurrent Acquisition Race (8 threads) | Exactly 1 acquires primary, 7 rejected | 1 acquired, 7 rejected | **PASS** |
| Single Secondary Launch Signal Check | Emit `activation_requested` exactly ONCE | Emitted TWICE (`2 != 1`) | **FAIL** |
| OTR Profile Disk Data Leakage | Zero cookies/cache written to disk | Ephemeral verified, zero cookies on disk | **PASS** |
