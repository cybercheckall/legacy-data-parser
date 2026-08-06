# Milestone 4 Changes Log

## Summary of Changes

### 1. Icon Conversion & Multi-Resolution ICO Assets
- Generated multi-resolution `owl_icon.ico` (16x16, 32x32, 48x48, 64x64, 128x128, 256x256) and `owl_icon.png` from `owl_icon.jpg` using Pillow script in the project root (`C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`).

### 2. Application Rebranding to "Owl"
- **`main.py`**:
  - Application name updated to `"Owl"` (`app.setApplicationName("Owl")`).
  - Set application window icon via `app.setWindowIcon(QIcon("owl_icon.ico"))` (falling back to `owl_icon.jpg`).
  - Updated `SingleInstanceGuard` default key to `"OwlBrowserApp"`.
  - Rebranded start/stop log messages to `"Owl"`.
- **`browser.py`**:
  - Main window class rebranded to `OwlBrowser` with backward compatibility alias `PhantomBrowser = OwlBrowser`.
  - Main window title set to `"Owl"` (`self.setWindowTitle("Owl")`).
  - Main window icon set via `self.setWindowIcon(QIcon("owl_icon.ico"))`.
  - Extended custom navigation scheme handler to support `owl://settings` alongside legacy/chrome aliases.
- **`title_bar.py`**:
  - Changed default TitleBar label to `"🦉 Owl"`.
- **`profile_selector.py`**:
  - Changed startup header label to `"🦉 Owl"`.
  - Updated subtitle to `"Select a profile to launch your private ephemeral workspace"`.
- **`settings_view.py`**:
  - Updated About section title to `"About Owl"`.
  - Updated version label to `"Owl v2.0.0 (Stealth Build)"`.
  - Updated appearance description to `"Owl features an ultra-modern dark glass interface..."`.
  - Fixed `set_search_engine()` method to trigger `self._populate_active_profile_fields()` and `self._sync_sub_pages()` so profile management dropdowns and search engine radio buttons stay synchronized.
- **`single_instance.py`**:
  - Updated `DEFAULT_APP_KEY` to `"OwlBrowser_SingleInstance"`.
  - Updated IPC socket server name generation prefix to `OwlWorkspace_` (`OwlWorkspace_{clean_key}_{user}`).

### 3. Packaging Spec Configuration (`owl.spec` & `phantom_browser.spec`)
- Created `owl.spec` targeting `Owl.exe` output with `icon='owl_icon.ico'` and bundling `owl_icon.jpg`, `owl_icon.ico`, and `owl_icon.png` in `datas`.
- Updated `phantom_browser.spec` to align output name to `'Owl'`, set `icon='owl_icon.ico'`, and include icon files in `datas`.

### 4. Stealth Preservation Verification
- Win32 `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)` display affinity protection verified in `display_affinity.py` and `browser.py`.
- Taskbar & Alt-Tab suppression via `Qt.WindowType.Tool` verified.
- Always-on-top behavior via `Qt.WindowType.WindowStaysOnTopHint` verified.
- System-wide global hotkey listener (`Ctrl+Shift+B`) in `hotkey.py` verified.
- Single-instance IPC socket server locking verified in `single_instance.py`.

### 5. Test Suite Updates & Clearance
- **`tests/test_ui_and_tabs.py`**: Updated title bar assertion from `"Phantom"` to `"Owl"`.
- **`tests/test_challenger_m1_2.py`**: Updated expected IPC server name format assertion to `"OwlWorkspace_"`.
- **`tests/conftest.py`**: Updated fallback test harness mocks (`MockTitleBar`, `SingleInstanceGuard`, default JSON path) to `"🦉 Owl"`, `"owl_workspace_guard"`, and `"owl_test_profiles.json"`.
- **`tests/test_stealth.py`**: Updated PyInstaller spec test to check for `owl.spec` or `phantom_browser.spec`.
- **`tests/test_e2e.py`**: Updated executable and spec checks to verify `Owl.exe` and `owl.spec`.
- **`tests/test_challenger_m3_stress.py`**: Updated settings URL assertion to accept `"owl://settings"`.
- Executed full test suite: **152 / 152 tests passed (100% pass rate)**.
