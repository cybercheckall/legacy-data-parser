# Handoff Report — Codebase Survey & Analysis for Phantom Workspace Overhaul

## 1. Observation

Direct observations from codebase inspection at `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`:

### A. Root Directory Files & Sizes
- `main.py` (84 lines, 2013 bytes): Main application entry point.
- `browser.py` (471 lines, 15658 bytes): Main window, tabs, navigation bar, bookmarks, and event handlers.
- `display_affinity.py` (41 lines, 1197 bytes): Win32 `SetWindowDisplayAffinity` wrapper.
- `hotkey.py` (75 lines, 2766 bytes): Global keyboard listener using `pynput`.
- `phantom_browser.spec` (86 lines, 2313 bytes): PyInstaller executable build spec file.
- `test_sample.spec` (728 bytes): Sample spec file.
- `ORIGINAL_REQUEST.md` (114 lines, 6674 bytes): Specifications for Phantom Workspace overhaul.
- `README.md` (1742 bytes): Project summary and user quickstart.
- `TEST_INFRA.md` (2111 bytes): Opaque-box E2E test runner documentation.
- `TEST_READY.md` (2998 bytes): Test suite status report (20/20 tests passing).
- `tests/`: Directory containing 6 test files (`conftest.py`, `test_browser_features.py`, `test_stealth_affinity.py`, `test_hotkey.py`, `test_e2e.py`, `test_pyinstaller_sample.py`).

### B. Stealth Implementation Key Locations
1. **Win32 Display Affinity (`WDA_EXCLUDEFROMCAPTURE`)**:
   - `display_affinity.py`, lines 11 & 22-24: `WDA_EXCLUDEFROMCAPTURE = 0x00000011`. Calls `ctypes.windll.user32.SetWindowDisplayAffinity(wintypes.HWND(hwnd), 0x00000011)`.
   - `browser.py`, lines 86 & 285-293: Invoked via `QTimer.singleShot(100, self._apply_stealth)` in `PhantomBrowser.__init__`.
2. **Window Flags (Tool & Always-On-Top)**:
   - `browser.py`, lines 63-67:
     ```python
     self.setWindowFlags(
         Qt.WindowType.Window
         | Qt.WindowType.WindowStaysOnTopHint
         | Qt.WindowType.Tool  # Suppresses taskbar icon
     )
     ```
3. **Global Hotkey (`Ctrl+Shift+B`)**:
   - `hotkey.py`, lines 12-74: `GlobalHotkey` class monitors system key events in a daemon thread using `pynput.keyboard.Listener`.
   - `main.py`, lines 58-69: Instantiates `GlobalHotkey(on_toggle=toggle_browser)`. Toggles visibility with `browser.hide()` vs `browser.show()` + `browser.activateWindow()` + `browser.raise_()`.
4. **Custom Frameless Title Bar & Drag Handling**:
   - `browser.py`, lines 97-134: `_title_bar` widget (height 30px, `#1a1a2e` bg) with minimize, maximize/restore (`_toggle_maximize`), and close buttons.
   - `browser.py`, lines 412-430: `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`, `mouseDoubleClickEvent` calculate window position relative to mouse drag within `_title_bar.geometry()`.
5. **Escape Key Hide Shortcut**:
   - `browser.py`, line 283: `QShortcut(QKeySequence("Escape"), self, self.hide)` hides window on `Esc` key press.

### C. Main Window, Tab & Web View Architecture
1. **Main Window (`PhantomBrowser`)**: Subclasses `QMainWindow`. Fixed size initialization `1100x750`.
2. **Web View Tab (`WebTab`)**: Subclasses `QWebEngineView`.
   - `browser.py`, lines 38-53: Uses `QWebEnginePage(profile, self)` and overrides `createWindow(window_type)` to open `target="_blank"` links in a new tab via `main_window.add_new_tab()`.
3. **Tab Widget**: Uses `QTabWidget` (`self._tabs`).
   - `add_new_tab(url=None)` creates a `WebTab` with shared `QWebEngineProfile.defaultProfile()` (persistent cookies policy enabled).
   - Tab close behavior (`_close_tab`): If tab count > 1, closes and deletes tab widget. If tab count == 1, navigates active tab to `HOME_URL` ("https://www.google.com") instead of closing.
4. **Navigation & Controls**:
   - Back (`◀`), Forward (`▶`), Refresh (`⟳`), Address Bar (`QLineEdit`), New Tab (`+`).
   - `_navigate_to_url()`: Navigates to direct URL if containing `.` without spaces (adds `https://` if missing), otherwise searches Google (`https://www.google.com/search?q=...`).

### D. Build & Test Infrastructure
1. **PyInstaller Spec (`phantom_browser.spec`)**:
   - Dynamically locates `PyQt6` resources (`Qt6/resources`), `QtWebEngineProcess.exe` (`Qt6/bin`), and translation files (`Qt6/translations`).
   - Includes hidden imports: `PyQt6.QtWebEngineWidgets`, `PyQt6.QtWebEngineCore`, `PyQt6.QtWebChannel`, `PyQt6.QtNetwork`, `PyQt6.QtPositioning`, `pynput.keyboard._win32`, `pynput._util.win32`.
   - Bundles output to `phantom_browser.exe` (`console=False`).
2. **Test Suite Verification**:
   - Command `$env:QT_QPA_PLATFORM="offscreen"; pytest tests/ -v` executes 20 test cases.
   - Result verified: **20 passed in 2.54s**.

---

## 2. Logic Chain

1. **Baseline Soundness**: All 20 existing unit/E2E tests pass cleanly under offscreen Qt mode. The existing codebase relies on standard PyQt6 + QtWebEngineWidgets + ctypes Win32 API + pynput.
2. **Preservation Requirements**: Overhauling into **Phantom Workspace** requires maintaining full functional compatibility for:
   - `SetWindowDisplayAffinity(hwnd, 0x00000011)` in `display_affinity.py` / main window startup.
   - `Qt.WindowType.Tool` & `Qt.WindowType.WindowStaysOnTopHint` window flags.
   - `GlobalHotkey` (`Ctrl+Shift+B`) in `hotkey.py`.
   - `Esc` key press hiding behavior.
   - Preserving last-tab navigation to default homepage instead of exiting application.
3. **Overhaul Integration & Component Map**:
   - **R1 UI Overhaul**: Update navigation bar layout (remove Back and Forward buttons, keep Reload button, center URL bar). Replace standard QTabWidget style with Chrome-style tabs and a "+" button on the right side of the tab bar. Upgrade dark theme with glassmorphism CSS, rounded corners, modern SVG/Unicode icons, custom frameless title bar.
   - **R2 Profiles System**: Implement a JSON-backed profile manager (`profiles.json`). Store profile fields: name, avatar, homepage URL, default search engine (Google or DuckDuckGo). Do NOT store cookies, history, or cache. Present a card-based launch profile selection dialog before main window display.
   - **R3 Single-Instance Enforcement**: Integrate a named Win32 mutex or local socket server (`QLocalServer`/`QLocalSocket` or `QSystemSemaphore`/`QSharedMemory`) during application startup in `main.py`. On secondary launch, send a signal to activate the primary instance (`show()`, `raise_()`, `activateWindow()`) and terminate the secondary instance immediately.
   - **R4 AI Side Panel (ChatGPT)**: Add a floating circular action button (with glow animation/sparkle icon) centered at the bottom of the main window. Integrate a sliding side panel widget (380-420px wide) containing a secondary `QWebEngineView` loading `https://chatgpt.com`.
   - **R5 Modern Settings Page**: Create a dedicated settings view/page accessible via a gear toolbar icon. Provide tabbed/sidebar navigation for Search Engine preference, Profile management, Appearance, About, and General options.
   - **R6 & R7 Build & Tab Integration**: Ensure new modules (e.g. profiles manager, single instance lock, AI panel widget, settings view) are cleanly imported and bundled into `phantom_browser.spec`. Ensure test suite remains green.

---

## 3. Caveats

1. **Win32 Display Affinity in Offscreen/Headless Mode**: Under `QT_QPA_PLATFORM=offscreen`, `winId()` returns a mock or virtual HWND, so `SetWindowDisplayAffinity` returns `0` (False) from Win32 API. Test suite handles this gracefully by checking HWND validity or fallback logic. Real execution on Windows desktop applies `SetWindowDisplayAffinity` successfully.
2. **`conftest.py` Dynamic Fallback Package**: `tests/conftest.py` defines a mock fallback package for `stealth_browser.*` if modular package imports are attempted. The main codebase currently uses top-level modules (`main.py`, `browser.py`, `display_affinity.py`, `hotkey.py`). Maintain compatibility with both entry points or structure updates cleanly.
3. **pynput Dependency**: If `pynput` is missing or lacks OS hook permissions, `GlobalHotkey` gracefully logs a warning without crashing the app.

---

## 4. Conclusion

The stealth browser codebase is compact, modular, and fully functional with 100% test pass rate (20/20). The existing stealth components (display affinity protection, taskbar suppression via `Tool` flag, always-on-top hint, global `Ctrl+Shift+B` hotkey, custom drag mechanics) are isolated in clear modules and methods (`display_affinity.py`, `hotkey.py`, `browser.py`).

The overhaul to **Phantom Workspace** can be achieved by:
1. Creating specialized modules for Profile Management, Single-Instance Lock, AI Side Panel Widget, Settings View, and UI Styling.
2. Redesigning `browser.py` to incorporate Chrome-style tab bar, single-reload nav bar, floating AI button, ChatGPT drawer panel, settings view trigger, and profile preferences.
3. Updating `main.py` with profile selection flow and single-instance mutex enforcement.
4. Updating `phantom_browser.spec` to bundle all new source files, JSON defaults, and resources.

---

## 5. Verification Method

To independently verify the baseline codebase and exploration findings:

1. **Run Unit & E2E Test Suite**:
   ```powershell
   $env:QT_QPA_PLATFORM="offscreen"
   pytest tests/ -v
   ```
   Verify 20 tests pass without failures.

2. **Inspect Main Source Files**:
   - `main.py`: Entry point and hotkey binding.
   - `browser.py`: `PhantomBrowser` UI layout, `WebTab` web engine setup, custom title bar drag handling.
   - `display_affinity.py`: `WDA_EXCLUDEFROMCAPTURE = 0x00000011` Win32 call.
   - `hotkey.py`: `pynput` global keyboard listener for `Ctrl+Shift+B`.
   - `phantom_browser.spec`: PyInstaller data bundling and hidden imports.
