# Milestone 4 Stealth Implementation & Test Suite Audit Report

**Author**: Explorer 3  
**Date**: 2026-08-06  
**Target Project**: Owl Browser (`C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`)  

---

## 1. Stealth Implementations Inspection

### 1.1 Win32 Display Affinity Exclusion (`display_affinity.py`)
- **API Mechanism**: Employs `ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)` where constant `WDA_EXCLUDEFROMCAPTURE = 0x00000011` (decimal 17).
- **Security Impact**: Renders the application window completely black / invisible to screen capture APIs, screen recording software (OBS, Camtasia), and video conferencing screen shares (Zoom, Microsoft Teams, Discord).
- **Robustness & Error Handling**:
  - Validates `hwnd` handle (returns `False` if `hwnd <= 0`).
  - Traps `ctypes` errors via `ctypes.GetLastError()` and handles exceptions gracefully without raising uncaught errors.
  - Deferred execution in `PhantomBrowser.__init__` via `QTimer.singleShot(100, self._apply_stealth)` ensures native Win32 window handles (`winId()`) are fully realized before invoking Win32 API calls.
- **Headless Test Compatibility**: `conftest.py` installs a safe execution wrapper during headless `QT_QPA_PLATFORM=offscreen` pytest runs, preventing Win32 error code 1400 (Invalid Window Handle) from breaking automated test suites.

### 1.2 Window Flags & Taskbar Suppression (`browser.py` / `main.py`)
- **API Mechanism**: In `PhantomBrowser.__init__`, the central window flags are configured as:
  ```python
  self.setWindowFlags(
      Qt.WindowType.Window
      | Qt.WindowType.WindowStaysOnTopHint
      | Qt.WindowType.Tool
  )
  ```
- **Stealth Impact**:
  - `Qt.WindowType.Tool`: Suppresses application window representation in the Windows Taskbar and Alt+Tab application switcher.
  - `Qt.WindowType.WindowStaysOnTopHint`: Pins the window above standard desktop application windows for rapid stealth access.
- **Frameless Drag & Close Mechanics**: Frameless title bar (`TitleBar`) handles left-click mouse movement dragging (`mouseMoveEvent`) and double-click maximize toggling (`mouseDoubleClickEvent`), while `Escape` key press in `_setup_shortcuts()` hides the window immediately (`self.hide()`).

### 1.3 System-Wide Global Hotkey Listener (`hotkey.py`)
- **API Mechanism**: Implements `GlobalHotkey` using `pynput.keyboard.Listener` running in a dedicated background daemon thread.
- **Shortcut Key Target**: Listens system-wide for `Ctrl + Shift + B` key combinations regardless of whether the browser window currently has focus.
- **Visibility Toggle Logic**:
  - Calls `browser.hide()` when window is currently visible.
  - Calls `browser.show()`, `browser.activateWindow()`, and `browser.raise_()` when hidden.
- **Fallback Guard**: Includes `try...except ImportError` block so if `pynput` is absent, application startup proceeds safely without crash.

### 1.4 Single-Instance IPC Enforcement (`single_instance.py`)
- **API Mechanism**: Uses Qt's `QLocalServer` and `QLocalSocket` local IPC sockets for cross-process single-instance locking.
- **Key & Naming Strategy**:
  - Default key: `DEFAULT_APP_KEY = "PhantomBrowser_SingleInstance"`.
  - Generates deterministic OS-safe socket name: `f"PhantomWorkspace_{clean_key}_{user}"` (or `sha256` hash slice if key > 60 chars).
- **IPC Activation Protocol**:
  1. Primary process binds `QLocalServer` to socket name.
  2. Secondary process attempts `QLocalSocket.connectToServer(server_name)`.
  3. If connection succeeds, secondary sends `b"ACTIVATE\n"`, primary receives connection and emits `activation_requested` / `activated` pyqtSignal, triggering `browser.activate_window_to_front()`. Secondary exits cleanly (`sys.exit(0)`).
  4. If connection fails, primary removes stale socket server files (`QLocalServer.removeServer(server_name)`) and begins listening.

---

## 2. Rebranding Impacts ("Phantom Workspace" → "Owl")

Rebranding the application to **"Owl"** requires coordinated updates across code labels, title bar components, single-instance socket names, window icons, and PyInstaller build specifications.

### 2.1 Code & UI Label Updates
| File Path | Current Code / Label | Proposed Rebranded Code / Label |
|---|---|---|
| `main.py:30` | `logger.info("=== Phantom Workspace starting ===")` | `logger.info("=== Owl starting ===")` |
| `main.py:41` | `app.setApplicationName("Phantom Workspace")` | `app.setApplicationName("Owl")` |
| `main.py:45` | `SingleInstanceGuard("PhantomBrowserApp")` | `SingleInstanceGuard("OwlBrowserApp")` |
| `browser.py:69` | `self.setWindowTitle("Phantom Workspace")` | `self.setWindowTitle("Owl")` |
| `title_bar.py:16` | `title: str = "👻 Phantom Workspace"` | `title: str = "🦉 Owl"` |
| `settings_view.py:464` | `QLabel("About Phantom Workspace", page)` | `QLabel("About Owl", page)` |
| `settings_view.py:476` | `QLabel("Phantom Workspace v2.0.0...", card)` | `QLabel("Owl v2.0.0 (Stealth Build)", card)` |

### 2.2 Iconography Integration
- Root icon asset: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\owl_icon.jpg`.
- **PyQt6 Window Icon**:
  - In `browser.py` or `main.py`, apply:
    ```python
    from PyQt6.QtGui import QIcon
    app.setWindowIcon(QIcon("owl_icon.jpg"))
    ```
- **PyInstaller Executable Icon**:
  - Convert `owl_icon.jpg` to `owl_icon.ico` using PIL / `Pillow` or configure PyInstaller spec to package `owl_icon.jpg` / `owl_icon.ico`.

### 2.3 Single Instance IPC Socket Naming
- `single_instance.py`:
  - Change default key: `DEFAULT_APP_KEY = "owl_browser_single_instance_lock"`.
  - Update `_get_server_name` prefix: `return f"Owl_{clean_key}_{user}"` or `return f"OwlWorkspace_{clean_key}_{user}"`.

### 2.4 PyInstaller Build Spec (`owl.spec`)
- Create/rename `owl.spec` targeting `Owl.exe`:
  - `name='Owl'` in `EXE(...)` block.
  - Include `owl_icon.jpg` and `owl_icon.ico` in `datas`.
  - Target entrypoint: `main.py`.

---

## 3. Test Suite Audit (`tests/`)

### 3.1 Current Test Execution Baseline
- Total test cases across suite: **152 tests**.
- Current status: **151 PASSED, 1 FAILED**.

### 3.2 Existing Test Failure Analysis
- **Failing Test**: `tests/test_challenger_m3_it2_deep_stress.py::TestSubPageUISynchronization::test_settings_subpage_sync_between_general_profiles_search`.
- **Root Cause**: In `settings_view.py`, `set_search_engine(engine)` updates the active profile and emits `search_engine_changed`, but fails to call `self._populate_active_profile_fields()` or `self._sync_sub_pages()`. As a result, changing the Search Engine radio button on Page 2 leaves the `prof_engine_combo` on Page 1 out of sync (`'DuckDuckGo' != 'Google'`).
- **Required Fix**: In `settings_view.py`, inside `set_search_engine(engine)`, call `self._sync_sub_pages()` and update `self.prof_engine_combo`.

### 3.3 Test Suite Audit Matrix for "Owl" Rebranding
| Test File | Current Assertion / Reference | Required Update for Rebranding | Impact |
|---|---|---|---|
| `tests/test_ui_and_tabs.py:48` | `self.assertIn("Phantom", self.title_bar.title_label.text())` | Change to `self.assertIn("Owl", self.title_bar.title_label.text())` | Prevents test failure when default title becomes `"🦉 Owl"` |
| `tests/test_challenger_m1_2.py:83` | `expected_name = f"PhantomWorkspace_{expected_hash}_{user}"` | Update to match rebranded `_get_server_name` (e.g. `f"OwlWorkspace_{expected_hash}_{user}"`) | Prevents IPC server name test mismatch |
| `tests/test_stealth.py:110` | Checks `phantom_browser.spec` existence | Update to check `owl.spec` (or accept `owl.spec` / `phantom_browser.spec`) | Validates rebranded spec file |
| `tests/test_e2e.py:93-94` | Checks `dist/stealth_browser.exe` & `stealth_browser.spec` | Update to check `dist/Owl.exe` & `owl.spec` | Validates rebranded build executable |
| `tests/conftest.py:318` | Mock `TitleBar` default label `"👻 Phantom Workspace"` | Update mock default to `"🦉 Owl"` | Maintains mock fidelity |
| `tests/conftest.py:136` | Mock `SingleInstanceGuard` default key `"phantom_workspace_guard"` | Update mock default key to `"owl_workspace_guard"` | Aligns IPC mock defaults |

---

## 4. Concrete Implementation Recommendations for Implementer

1. **Fix `settings_view.py` Sub-Page Sync**:
   Add `self._populate_active_profile_fields()` inside `set_search_engine` in `settings_view.py` so search engine radio toggle syncs profile dropdown menu, resolving the 1 failing test.
2. **Execute Rebranding Changes**:
   - Update string constants in `main.py`, `browser.py`, `title_bar.py`, `settings_view.py`, `single_instance.py`.
   - Wire `setWindowIcon(QIcon("owl_icon.jpg"))` in `browser.py` / `main.py`.
   - Update `phantom_browser.spec` / `owl.spec` to output `Owl.exe` with icon.
3. **Update Test Suite Assertions**:
   - Update `test_ui_and_tabs.py`, `test_challenger_m1_2.py`, `test_stealth.py`, `test_e2e.py`, and `conftest.py` per matrix above.
4. **Final Verification**:
   - Re-run `pytest tests/ -v` to ensure 152/152 tests (100%) pass.
