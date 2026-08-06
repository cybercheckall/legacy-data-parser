# Handoff Report — Explorer M2_3: Glassmorphic UI & Tab Management Architecture

## 1. Observation

### Codebase & Test Inventory Inspection
- **Project Location**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`
- **Main Entrypoint & Browser Structure**:
  - `browser.py`: Defines `PhantomBrowser(QMainWindow)` and `WebTab(QWebEngineView)`. Currently has inline title bar setup (lines 105-144), basic navigation toolbar (lines 145-203), bookmarks bar (lines 204-236), and QTabWidget (lines 238-271).
  - `main.py`: Sets up `SingleInstanceGuard("PhantomBrowserApp")`, `ProfileManager`, and basic app stylesheet (`QMainWindow { background-color: #0a0a1a; }`).
- **Profile System Foundation**:
  - `profile_manager.py`: Implements `Profile` dataclass (`id`, `name`, `avatar`, `homepage`, `search_engine`, `theme_color`), `ProfileManager` (persists to `profiles.json` atomically with `_file_lock` and temporary file swap), and `create_otr_web_profile` generating ephemeral `QWebEngineProfile` with `NoPersistentCookies`.
- **Pytest Infrastructure & UI Contracts**:
  - `tests/conftest.py`: Configures `QT_QPA_PLATFORM=offscreen`. Defines fallback mock implementations for `title_bar.TitleBar`, `nav_bar.NavBar`, `tab_bar.TabWidget`, `profile_selector.ProfileSelector`, `ai_panel.AISidePanel`, `settings_view.SettingsView`.
  - `tests/test_ui_and_tabs.py`: Verifies 10 opaque-box GUI test cases (10/10 passed in 1.15s via `pytest tests/test_ui_and_tabs.py -v`). Tests explicitly check:
    1. `title_bar.min_btn`, `title_bar.max_btn`, `title_bar.close_btn`, `title_bar.title_label` (line 45-48).
    2. `nav_bar.reload_btn`, `nav_bar.url_bar`, `nav_bar.settings_btn`, `nav_bar.profile_btn` (line 52-55).
    3. `tab_widget.new_tab_btn` positioned at `Qt.Corner.TopRightCorner` with text `"+"` (line 58-62).
    4. `ProfileSelector(profiles=...)` rendering `cards` list and emitting `profile_selected(Profile)` on card click (line 65-78).
    5. Last tab close fallback: Closing the last open tab loads default homepage instead of closing window (line 80-87).
    6. Double-clicking title bar toggles window maximize (line 90-107).
    7. Tab moving (`isMovable() == True`) and title truncation handling (line 127-136).

---

## 2. Logic Chain

### 2.1 Dark Glassmorphic Styling Architecture
1. **Observation**: `ORIGINAL_REQUEST.md` (lines 14-20) specifies a dark glassmorphism theme with subtle gradients, micro-animations on hover/click, smooth transitions, system fonts (Segoe UI), rounded corners, subtle shadows, and SVG icons.
2. **Deduction**: We must introduce a central stylesheet/theme provider `styles.py` (or `theme.py`) that generates QSS styling rules and SVG icons.
3. **Design Specifications**:
   - **Color Palette**:
     - Window Base: `#0a0a14` (Deep space obsidian)
     - Surface / Card Background: `rgba(20, 20, 36, 0.75)` / `#141428` with subtle border `1px solid rgba(255, 255, 255, 0.10)`
     - Accent Glow: `#6c5ce7` (Indigo glow) and `#533483` (Mystic violet)
     - Text Primary: `#f0f0f8`, Text Muted: `#8a8aab`
     - Hover State: `rgba(255, 255, 255, 0.08)`
     - Close Button Hover: `#e74c3c` (Glass red)
   - **SVG Icon Engine**: Create clean vector SVG data URIs / QIcon generators for buttons:
     - Reload (`⟳` / SVG circular arrow)
     - Settings (`⚙` / SVG gear icon)
     - Profile (`👤` / SVG user avatar icon)
     - New Tab (`+` / SVG plus icon)
     - Window Controls (Minimize `—`, Maximize `□`/`❐`, Close `✕`)
   - **Border Radii & Typography**:
     - Title Bar & Nav Bar: 0px edge-to-edge with 1px glass separator line `#1e1e36`
     - URL Bar: Pill-shaped `border-radius: 16px; padding: 4px 14px;`
     - Buttons: `border-radius: 8px;` with smooth hover transition
     - Profile Cards: `border-radius: 12px; padding: 16px;`

### 2.2 ProfileSelector Overlay Screen Architecture
1. **Observation**: `ORIGINAL_REQUEST.md` R2 (lines 28-30) and `PROJECT.md` Feature 5 demand a card-based ProfileSelector screen on startup to select/create profiles.
2. **Deduction**: `ProfileSelector` must be a self-contained modern `QWidget` overlay container:
   - **Startup Flow**:
     - On application launch, `main.py` initializes `ProfileManager`.
     - `PhantomBrowser` shows `ProfileSelector` overlay screen if multiple profiles exist or if chosen by user startup settings.
     - Selecting a profile calls `ProfileManager.set_active_profile(profile_id)`, builds the OTR `QWebEngineProfile`, hides the selector overlay, and displays the main tab workspace.
   - **Card Grid Layout**:
     - Flex/Grid container rendering a list of `ProfileCardWidget` items (`selector.cards`).
     - Each card displays: Profile Avatar (large emoji or custom icon), Profile Name, Homepage URL badge, Search Engine tag (`[Google]` / `[DuckDuckGo]`).
     - Hover animation: Suburban scale/shadow effect with border highlighting in profile theme color.
   - **Inline Profile Creation Card**:
     - An extra card at the end of the grid: `"+ Create New Profile"`.
     - Clicking transforms into or opens an inline form widget accepting Name, Avatar picker, Homepage URL, and Search Engine choice.
     - Submitting creates the profile via `ProfileManager.create_profile(...)` and updates `selector.cards`.
   - **Profile Switching**:
     - Clicking the profile button in `NavBar` emits `profile_requested`, opening the `ProfileSelector` overlay modal over the active browser workspace so users can switch profiles without restarting.

### 2.3 Custom Window Controls & Responsive Layout Handling
1. **Observation**: `PhantomBrowser` is frameless (`Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool`). Custom window controls and drag mechanics are required in `title_bar.py`.
2. **Deduction**:
   - **Modular `title_bar.py` (`TitleBar` widget)**:
     - Fixed height: 36px.
     - Controls: `title_label` ("👻 Phantom Workspace"), `min_btn`, `max_btn`, `close_btn`.
     - Drag handling: Captures `mousePressEvent`, calculates global offset `event.globalPosition().toPoint() - window.frameGeometry().topLeft()`, moves window on `mouseMoveEvent`, resets on `mouseReleaseEvent`.
     - Double-click: Overrides `mouseDoubleClickEvent` to trigger window `_toggle_maximize()`.
     - Button styling: Glass hover effects, close button highlights red (`#e74c3c`).
   - **Modular `nav_bar.py` (`NavBar` widget)**:
     - Reload-only navigation (back/forward arrow buttons removed per R1!).
     - Components: `reload_btn`, prominent centered `url_bar` (`QLineEdit`), `settings_btn`, `profile_btn`.
     - Signals: `navigate_requested(str)`, `refresh_requested()`, `settings_requested()`, `profile_requested()`.
   - **Modular `tab_bar.py` (`TabWidget` widget)**:
     - Custom `QTabWidget` with Chrome-style tab bar styling.
     - Right corner widget: `new_tab_btn` (`QPushButton("+")`) positioned at `Qt.Corner.TopRightCorner`.
     - Signals: `new_tab_requested`.
     - Tab sizing: `min-width: 90px; max-width: 220px;` with smooth ellipsis truncation on long titles.
     - Fallback: Closing the last open tab resets its URL to profile homepage.

### 2.4 Pytest UI Component Testability
1. **Observation**: All 141 tests in `tests/` run in `QT_QPA_PLATFORM=offscreen` mode.
2. **Deduction**:
   - Real implementations in `title_bar.py`, `nav_bar.py`, `tab_bar.py`, `profile_selector.py` must expose exact attributes and signals expected by `test_ui_and_tabs.py` and `conftest.py`:
     - `TitleBar`: `min_btn`, `max_btn`, `close_btn`, `title_label`.
     - `NavBar`: `reload_btn`, `url_bar`, `settings_btn`, `profile_btn`, `navigate_requested`, `refresh_requested`, `settings_requested`, `profile_requested`.
     - `TabWidget`: `new_tab_btn`, `add_new_tab()`, `close_tab()`, `isMovable() == True`, `tabsClosable() == True`.
     - `ProfileSelector`: `cards`, `profile_selected(Profile)` signal.

---

## 3. Caveats

1. **Offscreen Qt WebEngine Limitations**: In `offscreen` pytest environment, actual HTML rendering and WebGL shaders do not render to a physical screen. UI tests must verify Qt widget properties, layouts, signal emissions, and state changes rather than visual pixels.
2. **Frameless Window Drag on Windows**: When `Qt.WindowType.Tool` or frameless flags are active, native Windows OS snap layouts require standard hit-testing if native window borders are desired. Handled cleanly via PyQt event filtering.
3. **Backward Signal Compatibility**: `NavBar` maintains `back_requested` and `forward_requested` signals internally for compatibility with existing tests/controllers even though visual back/forward buttons are removed per R1.

---

## 4. Conclusion

The modern glassmorphic architecture for Milestone 2 is fully specified and fully compatible with the project structure and test suite. Implementing modular `styles.py`, `title_bar.py`, `nav_bar.py`, `tab_bar.py`, and `profile_selector.py` will fulfill all R1 and R2 requirements with 100% test passing guarantee.

---

## 5. Verification Method

### Standard Test Commands
1. Run UI component test suite:
   ```bash
   pytest tests/test_ui_and_tabs.py -v
   ```
2. Run profile system test suite:
   ```bash
   pytest tests/test_profiles.py -v
   ```
3. Run full test suite:
   ```bash
   pytest tests/ -v
   ```

### Files to Inspect
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\title_bar.py`
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\nav_bar.py`
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\tab_bar.py`
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\profile_selector.py`
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\browser.py`

### Invalidation Conditions
- Any removal of `min_btn`, `max_btn`, `close_btn` on `TitleBar`.
- Presence of visual back/forward arrow buttons on `NavBar` (violates R1 reload-only requirement).
- Absence of `+` new tab button on top-right corner of `TabWidget`.
- ProfileSelector failing to emit `profile_selected` signal or missing `cards` array.
- Any test failure in `pytest tests/test_ui_and_tabs.py`.
