# Handoff Report — Challenger 2 (Milestone 1: Profile System & Single Instance)

## 1. Observation

- **Environment & Commands**:
  - Windows 11, Python `3.12.10`, PyQt6 `6.11.0`, Qt Runtime `6.11.1`, pytest `9.1.1`.
  - Created and executed adversarial test suite: `tests/test_challenger_m1_2.py` (13 tests).
  - Executed full project test suite: `pytest tests/ -v` (116 tests).

- **Direct Empirical Test Results**:
  1. `pytest tests/test_challenger_m1_2.py -v`: **13 PASSED** in 6.64s.
  2. `pytest tests/test_profiles.py tests/test_single_instance.py -v`: **20 PASSED** in 3.79s.
  3. `pytest tests/ -v`: **115 PASSED, 1 FAILED** in 28.12s.

- **Observed Bug (Failure Details)**:
  - **File**: `profile_manager.py`, line 150.
  - **Code**: `tmp_path = self.json_path + ".tmp"`
  - **Test Failure**: `FAILED tests/test_m1_stress_and_edge.py::TestM1ProfileSystemAdversarial::test_concurrent_profile_manager_access`
  - **Verbatim Error Log**:
    ```
    ERROR profile_manager:profile_manager.py:162 Failed to save profiles atomically: [WinError 5] Access is denied: 'C:\Users\RAGHUV~1\AppData\Local\Temp\tmpvs4ca520\profiles.json.tmp' -> 'C:\Users\RAGHUV~1\AppData\Local\Temp\tmpvs4ca520\profiles.json'
    ERROR profile_manager:profile_manager.py:162 Failed to save profiles atomically: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\Users\RAGHUV~1\AppData\Local\Temp\tmpvs4ca520\profiles.json.tmp' -> 'C:\Users\RAGHUV~1\AppData\Local\Temp\tmpvs4ca520\profiles.json'
    AssertionError: 5 != 0 : Concurrent ProfileManager access generated errors: [(0, AttributeError("'NoneType' object has no attribute 'id'")) ...]
    ```

- **Single Instance & App Key Edge Cases Verification**:
  - **Long App Keys (>5,000 chars)**: `_get_server_name` hashes keys over 60 chars to `PhantomWorkspace_{sha256[:24]}_{user}`. Locks are acquired and released cleanly without Win32 named pipe path overflow.
  - **Empty / Whitespace Keys**: `try_acquire("")` and `try_acquire("   ")` raise `ValueError("Application key must be a non-empty string.")`. `None` key defaults to `DEFAULT_APP_KEY`.
  - **Socket Payload Corruption & Bombardment**: Tested NULL byte streams (`\x00`), high binary bytes (`\xff`), 2 MB binary payloads, non-UTF-8 bytes, and disconnected sockets without payload. `SingleInstanceGuard._on_new_connection` reads raw bytes safely without decoding exceptions, emits `activation_requested`, closes socket connection, and remains 100% responsive for subsequent instances.

---

## 2. Logic Chain

1. **Root Cause Analysis of Profile Manager Concurrency Failure**:
   - In `profile_manager.py:150`, `save_profiles()` constructs the temporary file path as `tmp_path = self.json_path + ".tmp"`.
   - When multiple threads or process instances attempt to save profiles simultaneously, all threads write to and attempt `os.replace()` on the **exact same** `.tmp` file path (`profiles.json.tmp`).
   - On Windows, opening or replacing a file currently held open by another thread/process raises `[WinError 5] Access is denied` or `[WinError 32] The process cannot access the file because it is being used by another process`.
   - As a result, `save_profiles()` fails, leaving the temporary file unreplaced or corrupting concurrent reads, which causes profile lookups to return `None`.

2. **Remediation Plan**:
   - To make atomic JSON writes safe under concurrent execution, each call to `save_profiles()` must use a unique temporary filename (e.g. incorporating `uuid.uuid4().hex`).
   - Specifically, in `profile_manager.py:150`, change:
     ```python
     tmp_path = self.json_path + ".tmp"
     ```
     to:
     ```python
     tmp_path = f"{self.json_path}.{uuid.uuid4().hex}.tmp"
     ```
   - This ensures each atomic write creates an independent temporary file prior to calling `os.replace(tmp_path, self.json_path)`.

3. **Single Instance Architecture Assessment**:
   - `single_instance.py` demonstrates excellent adversarial robustness:
     - Edge inputs (empty/whitespace/long/unicode strings) are handled cleanly.
     - Socket payload corrupted binary bytes or extreme payload sizes (2 MB) do not crash the listening server.
     - `QLocalServer.removeServer` cleans up stale sockets prior to listening.

---

## 3. Caveats

- **Qt Headless Environment**: Unit tests operate under `QT_QPA_PLATFORM=offscreen`. `QLocalServer` / `QLocalSocket` named pipes operate at the Windows OS kernel layer independent of GUI display servers.
- **Cross-Thread QObject Lifetime**: `QLocalServer` objects created inside background worker threads must be released on the thread where they were created before thread termination to prevent orphan pipe handles in Qt's Win32 event subsystem.

---

## 4. Conclusion

- **Overall Assessment**: `single_instance.py` passes all adversarial edge-case stress tests with high robustness. However, `profile_manager.py` contains a reproducible concurrency defect in `save_profiles()` where static `.tmp` filenames cause file lock access denied errors (`WinError 5` / `WinError 32`) on Windows.

- **Verdict**: `Verdict: REQUEST_CHANGES`

- **Required Action**:
  - Update `profile_manager.py:150` to use unique temporary file names per save operation (`f"{self.json_path}.{uuid.uuid4().hex}.tmp"`).

---

## 5. Verification Method

To independently verify this report and reproduce the finding:

1. **Run Full Test Suite**:
   ```powershell
   pytest tests/ -v
   ```
   *Observation*: 115 PASSED, 1 FAILED (`test_concurrent_profile_manager_access`).

2. **Run Milestone 1 Adversarial Test Suite**:
   ```powershell
   pytest tests/test_challenger_m1_2.py -v
   ```
   *Observation*: 13 PASSED in ~6.6s.

3. **Verify Proposed Fix**:
   - Modify `profile_manager.py:150` to use `tmp_path = f"{self.json_path}.{uuid.uuid4().hex}.tmp"`.
   - Re-run `pytest tests/ -v`.
   *Expected Result*: All 116 tests pass 100%.
