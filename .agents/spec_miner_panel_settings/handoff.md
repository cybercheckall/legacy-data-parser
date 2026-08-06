# Handoff Report — Panel, Settings & Stealth Specification Mining

## 1. Observation
- **Codebase & Environment Inspection**:
  - Source files inspected: `browser.py`, `display_affinity.py`, `hotkey.py`, `main.py`, `phantom_browser.spec`.
  - Test files inspected: `tests/test_stealth_affinity.py`, `tests/test_browser_features.py`, `tests/test_hotkey.py`, `tests/test_e2e.py`.
  - Project specification: `ORIGINAL_REQUEST.md`.
- **Existing Architecture**:
  - `PhantomBrowser` in `browser.py` inherits from `QMainWindow`, uses `QTabWidget` and `QWebEngineView`.
  - `apply_display_affinity` in `display_affinity.py` uses `ctypes` calling `SetWindowDisplayAffinity(hwnd, 0x00000011)`.
  - `GlobalHotkey` in `hotkey.py` uses `pynput.keyboard` to monitor `Ctrl+Shift+B`.
  - Main window flags set in `browser.py`: `Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool`.
  - `pytest` suite running 20 unit/integration tests passes in 0.94s.

## 2. Logic Chain
- **Requirement R4 (AI Side Panel)**:
  - Needs a floating circular button anchored at the bottom-center of the main window viewport.
  - Requires continuous glow/pulse animation to draw user attention.
  - Clicking toggles a right-side slide-in panel (width: 380px–420px, default 400px) containing a `QWebEngineView` loading `https://chatgpt.com`.
  - Must include a header bar with "ChatGPT" title label and a Close ("✕") button.
  - Responsive positioning on window resize (`resizeEvent`) is required so the button stays centered at the bottom and panel stays docked to the right edge.
- **Requirement R5 (Modern Settings Page)**:
  - Accessible via toolbar settings gear icon or internal URL (`chrome://settings` / `phantom://settings`).
  - Layout must feature a modern sidebar navigation (Width: ~220px) with categories: General, Search Engine, Profiles, Appearance, About.
  - Search Engine switcher: Choice between Google (`https://www.google.com/search?q={query}`) and DuckDuckGo (`https://duckduckgo.com/?q={query}`), persisting to active profile configuration and JSON store.
  - Profile Management: Full CRUD UI for profiles (View list, Create with avatar/homepage/engine, Edit, Delete with validation against deleting active/last profile).
  - General: Custom homepage URL input & startup preference.
  - Appearance: Dark theme accent color options & theme indicators.
  - About: Version (v2.0.0 Stealth Edition), tech stack details, stealth status badge.
- **Requirement R6 (Stealth & Core Features Preservation)**:
  - Display affinity: `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)` (0x00000011) must be preserved and re-applied post-window creation.
  - Window flags: `Qt.WindowType.Tool` (no taskbar icon) and `Qt.WindowType.WindowStaysOnTopHint` (always on top).
  - Global hotkey: `Ctrl+Shift+B` toggles window visibility (`show()` + `activateWindow()` + `raise_()` vs `hide()`).
  - Escape key hides browser without quitting app.
  - PyInstaller spec: `phantom_browser.spec` must bundle QtWebEngine resources, pynput binaries/hidden imports, and new profile/settings assets.

## 3. Caveats
- `SetWindowDisplayAffinity` relies on Windows User32 API (`ctypes.windll.user32`). On non-Windows platforms (e.g. Linux/macOS), calling this API will fail or raise `AttributeError`, so fallback checks should be wrapped gracefully.
- `pynput` global keyboard listener requires OS-level input monitoring permissions; headless test environments simulate trigger events via direct callback execution.
- ChatGPT webview requires a standard desktop browser User-Agent header in `QWebEngineProfile` to prevent simplified mobile web fallbacks.

## 4. Conclusion
Exhaustive specification for R4, R5, and R6 has been extracted and documented. All component interfaces, visual layouts, animation parameters, state transitions, edge cases, and acceptance verification rules are fully specified below.

## 5. Verification Method
- Execute pytest: `pytest`
- Verify display affinity constant: `python -c "import display_affinity; print(display_affinity.WDA_EXCLUDEFROMCAPTURE == 0x11)"`
- Verify window flags & hotkey listeners via `tests/test_stealth_affinity.py` and `tests/test_hotkey.py`.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | AI Side Panel | Floating Sparkle AI Button | Bottom-center circular floating trigger button with sparkle icon `✦` and glow/pulse animation. | User mouse click / hover | Toggles slide-in side panel visibility | Ignores clicks if animation is already running; remains pinned on resize | ORIGINAL_REQUEST.md R4 & UI layout |
| 2 | AI Side Panel | Slide-in Side Panel Container | 380px–420px wide right-docked panel with title header ("ChatGPT") and close "✕" button. | Click on AI button or Close button | Smooth horizontal slide animation (In: right->left, Out: left->right) | If window width < 500px, caps panel width to 80% of window | ORIGINAL_REQUEST.md R4 |
| 3 | AI Side Panel | Embedded ChatGPT Webview | Integrated `QWebEngineView` loading `https://chatgpt.com` within side panel. | URL load request (`https://chatgpt.com`) | Rendered live ChatGPT session web interface | Shows reload/retry banner if network connection fails | ORIGINAL_REQUEST.md R4 |
| 4 | Settings Page | Sidebar Navigation Layout | Two-column UI layout with left vertical navigation menu and right stacked settings content area. | Category item clicks (General, Search Engine, Profiles, Appearance, About) | Switches active settings view pane with active item indicator | Defaults to "General" tab if invalid category requested | ORIGINAL_REQUEST.md R5 |
| 5 | Settings Page | Default Search Engine Switcher | Dropdown/Radio option to toggle URL bar search engine between Google and DuckDuckGo. | User selection (Google / DuckDuckGo) | Updates default search URL template and profile JSON config | Reverts to Google if saved setting is invalid | ORIGINAL_REQUEST.md R5 |
| 6 | Settings Page | Profile Management UI | Comprehensive UI inside settings to view, create, edit, and delete browser profiles. | Profile form inputs (Name, Avatar icon, Homepage, Engine) | Updates `profiles.json` and updates profile list state | Prevents deleting current active profile or last remaining profile | ORIGINAL_REQUEST.md R5 |
| 7 | Settings Page | Appearance Settings | Theme toggle & visual customization section (Dark mode default, accent color selection). | Toggle switches / Color accent buttons | Applies CSS QSS palette update across application | Reverts to default dark glassmorphic theme on parse error | ORIGINAL_REQUEST.md R5 |
| 8 | Settings Page | About & Diagnostic Section | Display panel showing browser name, version (v2.0.0), build stack, and stealth affinity status. | Page view | Renders version info and live security status badge | N/A (Static display) | ORIGINAL_REQUEST.md R5 |
| 9 | Stealth Features | Win32 Display Affinity | Protection using `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)` (0x00000011). | Window handle (`HWND`) | Window hidden from OBS, Zoom, Discord, Snipping Tool | Logs warning if ctypes/Win32 call fails | `display_affinity.py` & ORIGINAL_REQUEST.md R6 |
| 10 | Stealth Features | Taskbar Icon Suppression | Window flag `Qt.WindowType.Tool` removes icon from Windows taskbar and Alt+Tab menu. | Window initialization | Window hidden from taskbar | N/A | `browser.py` & ORIGINAL_REQUEST.md R6 |
| 11 | Stealth Features | Always-On-Top Mode | Window flag `Qt.WindowType.WindowStaysOnTopHint` keeps browser floating above all windows. | Window initialization | Browser remains top-most window | N/A | `browser.py` & ORIGINAL_REQUEST.md R6 |
| 12 | Stealth Features | Global Hotkey Toggle | `Ctrl+Shift+B` shortcut toggles application visibility globally from any desktop context. | Physical key combo press `Ctrl+Shift+B` | Toggles window between visible (`show()`) and hidden (`hide()`) | Logs warning if `pynput` is missing | `hotkey.py` & ORIGINAL_REQUEST.md R6 |
| 13 | Stealth Features | Escape Key Quick Hide | Pressing `Esc` key immediately hides main browser window without exiting app process. | KeyPress event `Qt.Key.Key_Escape` | Window calls `hide()` | N/A | `tests/test_stealth_affinity.py` & ORIGINAL_REQUEST.md R6 |
| 14 | Build & Packaging | PyInstaller Build Spec | Updated `phantom_browser.spec` to bundle QtWebEngine assets, pynput modules, JSON profiles, and UI assets. | Build command `pyinstaller phantom_browser.spec` | Standalone `dist/phantom_browser.exe` executable | Packaging fails if required binaries are missing | `phantom_browser.spec` & ORIGINAL_REQUEST.md R6 |

---

## Edge Cases

| # | Feature | Input | Observed / Required Behavior |
|---|---------|-------|------------------------------|
| 1 | AI Side Panel | Rapid clicking of floating AI button while panel animation is running | Animation engine must cancel/stop current transition smoothly and start reverse animation without jitter or UI lockup. |
| 2 | AI Side Panel | Main window resized to small width (e.g. 500px) while side panel is open | Side panel automatically adjusts max width to 80% of window or auto-collapses to preserve main web content readability. |
| 3 | AI Side Panel | Network disconnect while loading ChatGPT | Webview displays custom offline/error placeholder inside side panel with a "Retry" button without crashing main app. |
| 4 | Settings Page | User attempts to delete active currently-in-use profile from settings | Delete button is disabled for active profile; hover tooltip displays "Cannot delete active profile". |
| 5 | Settings Page | User attempts to delete the last remaining profile | System blocks action and shows error dialog: "At least one profile must exist". |
| 6 | Settings Page | Searching special characters or empty string in URL bar with DuckDuckGo engine | URL bar URL-encodes special characters (`https://duckduckgo.com/?q=%23python`) cleanly. |
| 7 | Stealth Features | Screen recording app (e.g. OBS/Zoom) started while browser is open | Window display affinity immediately renders window area pitch black / invisible in capture stream. |
| 8 | Stealth Features | `pynput` library unavailable in Python environment | Application gracefully catches `ImportError`, logs warning to desktop log file, and fallback allows in-app shortcuts. |
| 9 | Stealth Features | Global hotkey triggered when window is minimized or behind other windows | Brings window to front, calls `show()`, `raise_()`, and `activateWindow()` to gain input focus. |
| 10 | Packaging | Executable executed on machine without Python installed | Standalone PyInstaller bundle contains all C++ DLLs and QtWebEngineProcess sub-executables to run independently. |

---

## Technical Component Architecture & Layout Specifications

### 1. R4 — AI Side Panel (ChatGPT Integration) Layout Specification

```
+-------------------------------------------------------------------------------+
| Main Browser Window (QMainWindow)                                             |
| +---------------------------------------------------------------------------+ |
| | Custom Title Bar (Frameless, Window Drag, Min/Max/Close)                   | |
| +---------------------------------------------------------------------------+ |
| | Chrome-Style Tab Bar (+ New Tab Button)                                   | |
| +---------------------------------------------------------------------------+ |
| | Navigation Bar (Reload, URL Search Bar, Profile Switcher, Gear Settings)  | |
| +---------------------------------------------------+-----------------------+ |
| | Active Web View / Content View                    | AI Side Panel (400px) | |
| | (QWebEngineView)                                  | +-------------------+ | |
| |                                                   | | Header: ✦ ChatGPT  X| | |
| |                                                   | +-------------------+ | |
| |                                                   | | QWebEngineView    | | |
| |                                                   | | (https://chatgpt) | | |
| |                                                   | |                   | | |
| |                     +------------------+          | |                   | | |
| |                     | Floating AI Button|         | |                   | | |
| |                     |  (✦ Sparkle Pulse) |        | |                   | | |
| |                     +------------------+          | +-------------------+ | |
| +---------------------------------------------------+-----------------------+ |
+-------------------------------------------------------------------------------+
```

#### Detailed Element Parameters for R4:
1. **Floating AI Button**:
   - Class name: `AIFloatingButton` (inherits `QPushButton` or `QToolButton`).
   - Geometry: Fixed size `52px x 52px`. Border radius `26px`.
   - Palette & Style: Dark glassmorphic background `rgba(20, 20, 35, 0.85)` with `1px solid rgba(124, 58, 237, 0.5)`. Text color `#00FFFF`, font size `22px`.
   - Animation: `QGraphicsDropShadowEffect` with `QPropertyAnimation` targeting blur radius (8px -> 20px -> 8px) over 2000ms loop.
   - Dynamic Placement: Position updated in `parentWidget.resizeEvent` to `x = (parent_width - 52) / 2`, `y = parent_height - 72`.
2. **Slide-in Side Panel**:
   - Class name: `AISidePanel` (inherits `QWidget`).
   - Fixed Width: `400px`. Height: Fills vertical space between nav bar and bottom edge.
   - Animation: `QPropertyAnimation(panel, b"geometry")` or `b"maximumWidth"` over `300ms` using `QEasingCurve.Type.OutCubic`.
   - Header: `QHBoxLayout` containing `QLabel("✦ ChatGPT")` (Segoe UI, bold, 14px, `#E0E0FF`) and `QToolButton("✕")` (`28x28px`, hover effect `#C0392B`).
   - Embedded Webview: `WebTab(profile=chat_profile)` pre-loaded with `https://chatgpt.com`.

---

### 2. R5 — Modern Settings Page Specification

```
+-------------------------------------------------------------------------------+
| In-Browser Settings Tab (phantom://settings or chrome://settings)            |
+--------------------------+----------------------------------------------------+
| Sidebar Menu (220px)     | Right Settings Content Pane (Scrollable Stack)     |
| +----------------------+ | +------------------------------------------------+ |
| | ⚙️ General            | | | 🔍 Search Engine                             | |
| | 🔍 Search Engine      | | | Default search engine used in address bar:   | |
| | 👤 Profile Management| | |  (o) Google    ( ) DuckDuckGo                  | |
| | 🎨 Appearance         | | +------------------------------------------------+ |
| | ℹ️ About Browser       | | | 👤 Profile Management                        | |
| +----------------------+ | | [ + Create New Profile ]                        | |
|                          | | +----------------------------------------------+ | |
|                          | | | Profile List:                                | | |
|                          | | |  - Default Profile [Active] (Google, Home)   | | |
|                          | | |  - Work Profile (DuckDuckGo, Custom Home)    | | |
|                          | | +----------------------------------------------+ | |
|                          | | | ℹ️ About Phantom Workspace                   | | |
|                          | | | Version: 2.0.0 Stealth Edition               | | |
|                          | | | Stealth Protection: Active (0x11)             | | |
|                          | +------------------------------------------------+ |
+--------------------------+----------------------------------------------------+
```

#### Detailed Options for R5:
1. **Search Engine Switcher**:
   - Options: `Google` (`https://www.google.com/search?q={query}`), `DuckDuckGo` (`https://duckduckgo.com/?q={query}`).
   - Behavior: Immediate signal `search_engine_changed(str)` fired upon radio/combo selection; saves choice in current profile's dictionary in `profiles.json`.
2. **Profile Management**:
   - Actions: Create Profile (opens dialog for Name, Icon, Homepage URL, Engine), Edit Profile, Delete Profile (with safeguard preventing active/last deletion).
3. **Appearance**:
   - Options: Toggle Dark Mode (Default: True), Accent Color Picker (Purple `#7C3AED`, Cyan `#06B6D4`, Emerald `#10B981`). Firing palette recalculation.
4. **General**:
   - Homepage URL: Editable line text input (default `https://www.google.com`). Firing profile update.
   - Startup Option: Radio buttons ("Open Homepage", "Open Blank Page").
5. **About**:
   - Software metadata display card: Version info, PyQt6 / QtWebEngine details, live security indicator badge showing "Display Affinity Active".

---

### 3. R6 — Stealth & Core Features Preservation Specification

| Stealth Component | Target API / Mechanism | Configuration Value | Expected Result |
|-------------------|------------------------|---------------------|-----------------|
| Display Affinity | Win32 `SetWindowDisplayAffinity` | `WDA_EXCLUDEFROMCAPTURE` (`0x00000011`) | Window excluded from all screen captures, OBS, Zoom, Teams, Snipping Tool |
| Taskbar Exemption | Qt Window Flags | `Qt.WindowType.Tool` | App icon suppressed from Windows Taskbar and Alt+Tab task switcher |
| Always-On-Top | Qt Window Flags | `Qt.WindowType.WindowStaysOnTopHint` | Window remains visible above all other running desktop applications |
| Global Hotkey | `pynput.keyboard.Listener` | `Ctrl + Shift + B` | System-wide hotkey toggles main window between hidden and shown state |
| Quick Hide | Qt Event Handler | `Qt.Key.Key_Escape` | Pressing `Esc` key hides window immediately without terminating app |
| Frameless Drag | Mouse Press/Move Events | Tracking `drag_pos` on Title Bar | Enables custom smooth window movement across multi-monitor setup |
| Packaging Spec | PyInstaller Spec | `phantom_browser.spec` | Bundles QtWebEngine binaries, pynput modules, profile JSON, and assets |

---

## Acceptance Criteria Mapping Matrix

| ID | Requirement | Feature | Verification Criteria | Test Method / Command |
|---|-------------|---------|-----------------------|-----------------------|
| AC-R4-1 | R4 | Floating AI Button Visuals | Floating button visible at bottom-center with sparkle `✦` icon and pulse animation. | Inspection & UI layout unit test checking button position and animation property |
| AC-R4-2 | R4 | AI Panel Slide-In | Clicking floating button slides side panel in from right (380-420px wide) containing `https://chatgpt.com`. | Trigger click signal; assert panel geometry position changes from x=`width` to x=`width-400` |
| AC-R4-3 | R4 | AI Panel Header & Close | Header shows "ChatGPT" title and Close "✕" button. Clicking Close slides panel out. | Trigger Close button click; assert panel returns to hidden position |
| AC-R5-1 | R5 | Settings Access | Gear icon in navigation bar or `chrome://settings` opens Modern Settings Page tab. | Click gear icon; assert active tab displays Settings Page view |
| AC-R5-2 | R5 | Search Engine Switcher | User can switch default search engine between Google and DuckDuckGo in settings. | Select DuckDuckGo; navigate `test search`; assert URL is `https://duckduckgo.com/?q=test+search` |
| AC-R5-3 | R5 | Profile CRUD from Settings | Create, edit, and delete profiles from Settings page UI; changes persist to JSON file. | Create new profile via settings dialog; verify `profiles.json` contains new profile entry |
| AC-R5-4 | R5 | Appearance & About Sections | Settings page has dark theme styling, appearance controls, and About info section. | Inspect Settings tab components for dark CSS theme, version text, and status badge |
| AC-R6-1 | R6 | Display Affinity | `SetWindowDisplayAffinity` (0x00000011) applied on window HWND handle. | `python -c "from display_affinity import apply_display_affinity; assert apply_display_affinity(hwnd)"` |
| AC-R6-2 | R6 | Stealth Window Flags | Window flags include `Qt.WindowType.Tool` and `Qt.WindowType.WindowStaysOnTopHint`. | Run `pytest tests/test_stealth_affinity.py` (Assert flags set) |
| AC-R6-3 | R6 | Global Hotkey Toggle | `Ctrl+Shift+B` shortcut toggles window visibility globally. | Run `pytest tests/test_hotkey.py` (Assert window toggles state) |
| AC-R6-4 | R6 | Quick Hide Shortcut | Pressing `Esc` key hides window without exiting app. | Run `pytest tests/test_stealth_affinity.py::test_tier2_esc_key_hides_window` |
| AC-R6-5 | R6 | PyInstaller Spec Update | `phantom_browser.spec` includes all required dependencies, QtWebEngine resources, and modules. | Run `pytest tests/test_e2e.py::test_tier4_standalone_executable_verification` |
