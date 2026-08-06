# Handoff Report: Milestone 2 — Modern Glassmorphic UI & Tab Management Strategy

## 1. Observation

### 1.1 Existing Codebase & Component State
- **`browser.py`** (lines 105–271): Currently contains an inline monolithic UI build method (`_build_ui`).
  - Title bar is a basic `QWidget` (lines 106–144) hardcoded inside `browser.py` with static inline QSS (`background-color: #1a1a2e`).
  - Navigation bar (lines 145–203) includes legacy back (`_back_btn`) and forward (`_fwd_btn`) arrow buttons alongside refresh (`_refresh_btn`) and `_url_bar`.
  - Tab widget (lines 238–271) is a standard `QTabWidget` without a dedicated right-aligned '+' new tab corner widget or custom Chrome-style tab styling.
- **`main.py`** (lines 51–66): Directly instantiates `PhantomBrowser()` and applies basic inline QSS (`background-color: #0a0a1a`). Does not yet show a profile selector screen/overlay on startup.
- **`profile_manager.py`** (lines 41–70, 72–233): Robust Profile data model and JSON persistence (`profiles.json`) already implemented and verified in Milestone 1. Provides `Profile` model with `id`, `name`, `avatar`, `homepage`, `search_engine`, `theme_color`, and `ProfileManager` with full CRUD operations.
- **Missing UI Modules**: Dedicated standalone modules `title_bar.py`, `nav_bar.py`, `tab_bar.py`, `profile_selector.py`, and `styles.py` do not yet exist as separate source files in the project root.

### 1.2 Test Suite State (`tests/`)
- **`tests/test_ui_and_tabs.py`**:
  - Requires imports: `from title_bar import TitleBar`, `from nav_bar import NavBar`, `from tab_bar import TabWidget`, `from profile_selector import ProfileSelector`, `from profile_manager import Profile`.
  - Attributes expected on `TitleBar`: `min_btn`, `max_btn`, `close_btn`, `title_label` (line 45–48). Expects double-click window maximize toggle support (line 90–108).
  - Attributes expected on `NavBar`: `reload_btn`, `url_bar`, `settings_btn`, `profile_btn` (line 52–55). Expects `navigate_requested` signal (emitting typed URL or search query) (line 111–119).
  - Attributes expected on `TabWidget`: `new_tab_btn` positioned at `TopRightCorner` (`cornerWidget(Qt.Corner.TopRightCorner)`), label="+", `add_new_tab(url, label)`, `close_tab(index)`, `count()`, `isMovable()` set to `True` (line 57–63, 80–87, 120–136).
  - Attributes expected on `ProfileSelector`: `ProfileSelector(profiles=profiles)`, `cards` list attribute, emits `profile_selected` signal passing `Profile` object on card click (line 64–78).
- **`tests/test_browser_features.py`**: Asserts tab creation/closing, URL bar signal emission, bookmark bar links, and navigation button events.
- **`tests/conftest.py`** (lines 302–430): Currently provides mock stub implementations for `title_bar`, `nav_bar`, `tab_bar`, `profile_selector`, `ai_panel`, `settings_view` in `sys.modules` when standalone files are absent.
- **Automated Test Run**: Ran `pytest tests/ -v` and verified **116/116 standard tests passed** in 27.58 seconds.

---

## 2. Logic Chain

### 2.1 Component Architecture & Refactoring Strategy
To fulfill Requirement R1, R2, R7 and pass the test contracts, the monolithic `browser.py` must be decomposed into modular components:

```
stealth_browser/
├── styles.py           # Glassmorphism QSS theme, color tokens & micro-animations
├── title_bar.py        # Frameless dark glass TitleBar with min/max/close, drag & double-click toggle
├── nav_bar.py          # Reload-only NavBar with prominent URL bar, settings & profile triggers
├── tab_bar.py          # Chrome-style TabWidget with right-aligned '+' corner widget & dynamic tabs
├── profile_selector.py # Card-based ProfileSelector view/overlay for startup & switching
├── browser.py          # PhantomBrowser QMainWindow assembling all M2 components
└── main.py             # App entry point with IPC guard, profile selector launch flow & global hotkey
```

### 2.2 Detailed Technical Strategy per Sub-Task

#### 1. Custom Frameless Title Bar (`title_bar.py`)
- **Visual Design**: Dark glass backdrop (`background-color: rgba(15, 23, 42, 0.85)` / `#0f172a`), 32px height, subtle bottom border (`1px solid rgba(255, 255, 255, 0.08)`).
- **Control Buttons**:
  - `min_btn`: Minimizes parent window (`showMinimized()`).
  - `max_btn`: Toggles maximize/restore (`showMaximized()` / `showNormal()`), updates button glyph (`□` vs `❐`).
  - `close_btn`: Closes parent window (`close()`), with red hover highlight (`#ef4444`).
  - `title_label`: Displays app title (`👻 Phantom Workspace` or `Phantom Browser`).
- **Drag & Interaction Handling**:
  - Mouse press (`mousePressEvent`) records offset relative to window top-left when clicking empty title bar space.
  - Mouse move (`mouseMoveEvent`) updates window position (`self.window().move(...)`).
  - Double-click (`mouseDoubleClickEvent`) toggles window maximize state via `window()._toggle_maximize()` or internal handler.

#### 2. Navigation Bar (`nav_bar.py`)
- **Layout & Controls**:
  - Remove back (`◀`) and forward (`▶`) buttons from main toolbar view per R1 specification.
  - Retain `reload_btn` (`⟳`) on the far left.
  - Centered prominent `url_bar` (`QLineEdit`) with rounded pill shape (`border-radius: 14px`), dark glass background, glowing focus ring (`#6366f1`), and placeholder `"Search with Google or enter URL..."`.
  - Right-side triggers: `settings_btn` (`⚙`) and `profile_btn` (`👤` / avatar display).
- **Signals**:
  - `navigate_requested(str)`: Emitted on `url_bar.returnPressed`. Formats search queries automatically using the active profile's default search engine (`Google` or `DuckDuckGo`).
  - `refresh_requested`: Emitted when `reload_btn` is clicked.
  - `settings_requested`: Emitted when `settings_btn` is clicked.
  - `profile_requested`: Emitted when `profile_btn` is clicked.

#### 3. Chrome-Style Tab Bar & Management (`tab_bar.py`)
- **Tab Bar Styling**:
  - Slanted/rounded tab style with active tab background matching webview viewport (`#0f172a`), inactive tabs dark semi-transparent (`rgba(255, 255, 255, 0.05)`).
  - Active indicator bar (indigo border-bottom `#6366f1` or top accent).
  - Hover transitions on inactive tabs.
- **New Tab Button (`+`)**:
  - `new_tab_btn`: `QPushButton("+")`, fixed size 28x28px, rounded (`border-radius: 14px`).
  - Positioned via `self.setCornerWidget(self.new_tab_btn, Qt.Corner.TopRightCorner)`.
  - Emits `new_tab_requested` signal on click.
- **Tab Behavior**:
  - `setMovable(True)` and `setTabsClosable(True)`.
  - `add_new_tab(url=None, label="New Tab")`: Creates `WebTab` instance, connects `titleChanged` and `urlChanged` signals, handles dynamic title truncation (max 25 chars + `...`), sets tab icon / favicon if available.
  - `close_tab(index)`: If tab count > 1, removes and deletes tab widget. If tab count == 1 (last tab), navigates current tab to user's active profile homepage instead of closing window (satisfying R7 and `test_tier1_last_tab_close_navigates_home`).

#### 4. Modern Profile Selector Screen (`profile_selector.py`)
- **Card-Based UI**:
  - Grid or horizontal card layout with dark glass cards (`rgba(30, 41, 59, 0.7)`), subtle borders (`1px solid rgba(255, 255, 255, 0.1)`), hover elevation scale/glow.
  - Each card displays avatar (emoji / icon), profile name, homepage URL badge, search engine indicator, and theme color accent.
  - Exposes `cards` list attribute containing clickable card widgets/buttons for test contract compatibility.
- **Signals & Actions**:
  - Emits `profile_selected(Profile)` on card click.
  - Includes a "+ Create New Profile" card trigger opening a profile creation dialog.

#### 5. Dark Glassmorphism Stylesheet (`styles.py`)
- Centralized QSS stylesheet module defining `DARK_GLASS_STYLE` with CSS variables / color palette:
  - Background dark glass: `rgba(15, 23, 42, 0.95)` / `#0f172a`.
  - Panel glass: `rgba(30, 41, 59, 0.85)` / `#1e293b`.
  - Accent primary: `#6366f1` (Indigo) / `#818cf8`.
  - Text primary: `#f8fafc`, text secondary: `#94a3b8`.
  - Border glass: `1px solid rgba(255, 255, 255, 0.1)`.
  - Micro-animation states for `:hover`, `:focus`, and `:pressed`.

#### 6. Integration in `browser.py` & `main.py`
- Refactor `PhantomBrowser` in `browser.py` to instantiate and lay out `TitleBar`, `NavBar`, and `TabWidget` vertically inside a central container layout.
- In `main.py`, show the `ProfileSelector` overlay/view on application startup before loading `PhantomBrowser`, or present `ProfileSelector` inside `PhantomBrowser` when no active profile is set.

---

## 3. Caveats

1. **Test Module Fallbacks in `conftest.py`**:
   - `conftest.py` dynamically injects mock modules if `title_bar.py`, `nav_bar.py`, `tab_bar.py`, `profile_selector.py` are not importable. Once real modules are created, python will import the real files. We must ensure the real module interfaces match or extend all expected attributes (`min_btn`, `max_btn`, `close_btn`, `title_label`, `reload_btn`, `url_bar`, `settings_btn`, `profile_btn`, `new_tab_btn`, `cards`, `profile_selected`, `navigate_requested`, `add_new_tab`, `close_tab`, etc.) to prevent test regressions.
2. **Back/Forward Navigation in NavBar**:
   - Requirement R1 specifies removing back/forward buttons from the navigation bar. However, keyboard shortcuts (`Alt+Left`, `Alt+Right`) should remain functional in `PhantomBrowser` so users can still navigate history without cluttering the modern toolbar.
3. **PyQt6 Offscreen Platform Support**:
   - All custom widgets (especially mouse drag, double click, and tab corner widgets) must run cleanly under `QT_QPA_PLATFORM=offscreen` during headless automated test execution.

---

## 4. Conclusion

The existing codebase is well-structured and Milestone 1 components (`profile_manager.py`, `single_instance.py`) are fully verified.
Milestone 2 implementation requires creating 5 new modular files (`styles.py`, `title_bar.py`, `nav_bar.py`, `tab_bar.py`, `profile_selector.py`) and refactoring `browser.py` and `main.py`.

### Actionable Implementation Plan

| Step | Action | Files to Create / Modify | Key Deliverables |
|------|--------|--------------------------|------------------|
| **Step 1** | Create Glassmorphic Stylesheet | `styles.py` | Modern dark glass QSS theme, color tokens, button/tab micro-animations |
| **Step 2** | Implement TitleBar Component | `title_bar.py` | Frameless title bar, `min_btn`, `max_btn`, `close_btn`, `title_label`, drag & double-click maximize toggle |
| **Step 3** | Implement NavBar Component | `nav_bar.py` | Reload-only nav bar, centered pill `url_bar`, `settings_btn`, `profile_btn`, `navigate_requested` signal |
| **Step 4** | Implement TabWidget Component | `tab_bar.py` | Chrome-style tabs, top-right `+` `new_tab_btn`, reorderable (`isMovable`), closable, homepage fallback on last tab close |
| **Step 5** | Implement ProfileSelector View | `profile_selector.py` | Card-based profile selection screen, `cards` list, `profile_selected` signal, modern card UI |
| **Step 6** | Overhaul Main Window & Launch Flow | `browser.py`, `main.py` | Assemble modular UI in `PhantomBrowser`, integrate startup profile selector overlay, apply glass theme |
| **Step 7** | Verify Test Suite | `tests/` | Run `pytest tests/ -v`, verify all 141 tests pass without breaking any contract |

---

## 5. Verification Method

### 5.1 Automated Test Execution
Run the complete automated test suite in headless offscreen mode:
```powershell
pytest tests/ -v
```
Expected output: **141/141 passed** across all test files:
- `tests/test_ui_and_tabs.py` (TitleBar, NavBar, TabWidget, ProfileSelector unit & integration tests)
- `tests/test_browser_features.py` (Tab navigation, bookmarks, WebEngine settings)
- `tests/test_profiles.py` (Profile persistence and CRUD)
- `tests/test_single_instance.py` (IPC single instance lock)
- `tests/test_stealth.py` & `tests/test_stealth_affinity.py` (Display affinity WDA protection)
- `tests/test_e2e_scenarios.py` & `tests/test_challenger_m1_2.py` (Stress and edge case suites)

### 5.2 Manual UI Verification Commands
Run the application locally to inspect visual elements:
```powershell
python main.py
```
Checklist for visual inspection:
- [ ] Card-based Profile Selector overlay appears on launch.
- [ ] Choosing a profile launches the main frameless window with dark glass title bar.
- [ ] Title bar minimize, maximize/restore (□/❐), and close buttons respond correctly.
- [ ] Dragging the title bar moves the window; double-clicking toggles maximize.
- [ ] Nav bar features centered URL bar and reload button only (no back/forward buttons).
- [ ] Tab bar displays Chrome-style tabs with '+' button on the far right.
- [ ] Closing the last tab navigates to profile homepage instead of closing window.
