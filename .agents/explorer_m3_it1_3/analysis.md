# Milestone 3 Test Suite & Infrastructure Analysis

**Agent**: Explorer 3 (Milestone 3 Iteration 1)  
**Date**: 2026-08-05  
**Target Module**: Milestone 3 — AI Side Panel (ChatGPT Integration) & Settings System  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m3_it1_3`  

---

## 1. Executive Summary

Milestone 3 introduces two major modern browser subsystems to **Phantom Workspace**:
1. **AI Assistant Side Panel (`ai_panel.py`)**: A floating circular sparkle button (52x52px, `✦`, glowing pulse animation) at bottom-center and a 380-420px sliding container with embedded ChatGPT webview (`https://chatgpt.com`).
2. **Modern In-Browser Settings Page (`settings_view.py`)**: A sidebar navigation interface (General, Profiles, Search Engine, Appearance, About) supporting search engine switching (Google vs DuckDuckGo), profile CRUD, and homepage configuration.

This analysis evaluates the existing 142-test suite baseline, verifies test environment readiness, formulates detailed test specifications for all Milestone 3 features, details integration points in `browser.py`, and maps potential regression risks against passing tests.

---

## 2. Existing Baseline Test Suite Analysis

### 2.1 Baseline Execution Status
- **Total Tests**: 142 test cases across 16 test files.
- **Pass Rate**: 100% (142 passed in 10.36 seconds under `QT_QPA_PLATFORM=offscreen`).
- **Execution Command**: `pytest tests/ -v`

### 2.2 Test Suite Architecture & File Inventory
| Test File | Test Count | Scope Covered | Key Features Verified |
|-----------|------------|---------------|-----------------------|
| `test_ai_side_panel.py` | 10 | AI Floating Button & Side Panel | 52x52px size, sparkle icon ✦, 380-420px width, `https://chatgpt.com` load, slide toggle, close btn, rapid toggle |
| `test_settings.py` | 10 | Settings View & Search Engine | Sidebar nav, Google vs DuckDuckGo switch, active profile update, homepage normalization, URL format |
| `test_profiles.py` | 12 | Profile Manager & Data Models | JSON storage, OTR WebEngine profiles, zero-cookie policy, CRUD operations |
| `test_m1_stress_and_edge.py` | 24 | Profile Stress & Edge Cases | Corrupted profiles.json handling, atomic write, concurrent access, invalid schema fallbacks |
| `test_single_instance.py` | 10 | Single Instance IPC Guard | `QLocalServer`/`QLocalSocket` IPC, primary lock acquisition, secondary activation signal |
| `test_ui_and_tabs.py` | 12 | UI Layout & Tab Operations | Reload-only NavBar, Chrome-style TabBar, '+' new tab button, tab title truncation |
| `test_browser_features.py` | 10 | Browser Features & Navigation | WebEngine settings (JS enabled), tab open/close, address bar navigate, bookmarks bar |
| `test_challenger_m1_2.py` | 15 | M1 Challenger Stress | IPC socket cleanup under abnormal exit, profile data integrity |
| `test_challenger_m2_1.py` | 15 | M2 Challenger Stress | 50-tab rapid churn, title bar drag math, ProfileSelector card rendering, URL search query parsing |
| `test_challenger_m2_2.py` | 5 | M2 Iteration 2 Compliance | Corner widget '+' placement, reload-only toolbar compliance, last-tab home fallback, dark glass QSS |
| `test_stealth.py` | 6 | Stealth Protection | `SetWindowDisplayAffinity` (WDA_EXCLUDEFROMCAPTURE), `Tool` window flag, `WindowStaysOnTopHint` |
| `test_stealth_affinity.py` | 4 | Win32 Affinity Binding | HWND extraction, display affinity API return codes |
| `test_hotkey.py` | 4 | Global Hotkey Listener | `Ctrl+Shift+B` pynput hotkey registration, hide/show toggle signal |
| `test_e2e.py` | 5 | Basic End-to-End Scenarios | Window creation, tab flow, title bar interaction |
| `test_e2e_scenarios.py` | 10 | Pairwise & Tier 4 Scenarios | Profiles x Settings, SingleInstance x Stealth, AI Panel x Tabs, 5 Real-World Workflows |
| `test_pyinstaller_sample.py` | 0 | PyInstaller Build Config | Spec file validation fixture |

### 2.3 `conftest.py` Fallback Architecture Discovery
`conftest.py` provides fallback mock implementations for `ai_panel`, `settings_view`, `profile_manager`, `single_instance`, `nav_bar`, `tab_bar`, `title_bar`, `profile_selector`, and `stealth_browser.*`.  
**Critical Finding**: The test suite currently passes because `conftest.py` supplies fallback contracts when files don't exist. When real `ai_panel.py` and `settings_view.py` modules are created in the project root, `pytest` will import the real project modules. All implementation classes must strictly adhere to the exact attribute names, signal names, and signatures defined in `PROJECT.md` and verified in `conftest.py`.

---

## 3. Milestone 3 Feature Test Specifications

### 3.1 AI Floating Button (`AIFloatingButton`) Specifications
- **Spec A1: Dimensions & Shape**: Button must be instantiated with fixed size of `52x52` pixels (`setFixedSize(52, 52)`), with circular QSS border-radius (`border-radius: 26px`).
- **Spec A2: Sparkle Icon**: Button text/icon must contain the sparkle character `✦` or modern AI icon.
- **Spec A3: Glow / Pulse Animation**: Visual glow or pulse effect (`QGraphicsDropShadowEffect` or CSS animation) active on hover/idle to draw user attention.
- **Spec A4: Bottom-Center Viewport Positioning**: Positioned dynamically at bottom-center of `PhantomBrowser` main window (`x = (win_width - 52) // 2`, `y = win_height - 52 - 20`). Must re-center automatically during main window resize events (`resizeEvent`).
- **Spec A5: Z-Order Elevation**: Must call `raise_()` to ensure floating button stays on top of embedded web views and tab content.
- **Spec A6: Click Action**: Clicking `AIFloatingButton` calls `AISidePanel.toggle_panel()`.

### 3.2 AI Side Panel Container (`AISidePanel`) Specifications
- **Spec B1: Container Width**: Fixed or constrained panel width strictly within `380px` to `420px` range (default `400px`).
- **Spec B2: Embedded ChatGPT Webview**: Contains embedded `QWebEngineView` loading URL `https://chatgpt.com`.
- **Spec B3: Header Layout**: Top header bar containing title label `"ChatGPT"` and close button (`close_btn`) with text `"✕"`.
- **Spec B4: Visibility & State Transitions**:
  - Initial state: Hidden (`isVisible() == False`).
  - `show_panel()`: Transitions state to visible (`_visible_state = True`), triggers slide-in animation, calls `show()` and `raise_()`.
  - `hide_panel()`: Transitions state to hidden (`_visible_state = False`), triggers slide-out animation, calls `hide()`.
  - `toggle_panel()`: Invokes `hide_panel()` if visible; invokes `show_panel()` if hidden.
- **Spec B5: Slide-In / Slide-Out Animations**: `QPropertyAnimation` targeting position or geometry, sliding in from `x = win_width` to `x = win_width - panel_width`.
- **Spec B6: Header Close Button**: Clicking `close_btn` executes `hide_panel()`.
- **Spec B7: Rapid Toggle Idempotency & Stability**: Executing 10+ rapid `toggle_panel()` calls in sequence must preserve state consistency and not crash the Qt event loop or animation instance.

### 3.3 Settings View (`SettingsView`) Specifications
- **Spec C1: Sidebar Navigation Layout**:
  - Horizontal main layout featuring a left sidebar (`sidebar`) with navigation buttons:
    - `btn_general` ("General")
    - `btn_profiles` ("Profiles")
    - `btn_search` ("Search Engine")
    - `btn_appearance` ("Appearance")
    - `btn_about` ("About")
  - Paired with a `QStackedWidget` (`stack`) containing page views for each category.
- **Spec C2: Search Engine Selection & Persistence**:
  - Radio buttons `radio_google` ("Google") and `radio_ddg` ("DuckDuckGo").
  - Selecting DuckDuckGo updates active profile's `search_engine` property to `"DuckDuckGo"` and persists changes to `profiles.json`.
  - Selecting Google updates active profile's `search_engine` property to `"Google"` and persists changes to `profiles.json`.
  - Emits `search_engine_changed(str)` signal with updated engine name.
- **Spec C3: Search Query URL Generation**:
  - `Google`: search query URL formatted as `https://www.google.com/search?q={query_encoded}`
  - `DuckDuckGo`: search query URL formatted as `https://duckduckgo.com/?q={query_encoded}`
  - Query formatting handles spaces (replaced with `+` or `%20`) and special characters cleanly.
- **Spec C4: Profile CRUD in Settings**:
  - Displays existing profiles list.
  - Form/inputs to create new profile (name, avatar, homepage, search engine).
  - Ability to edit active profile attributes.
  - Ability to delete non-active profile (protecting against deleting the last remaining profile).
  - Emits `profile_updated()` signal when profiles are modified.
- **Spec C5: Preferred Homepage Configuration**:
  - Line edit input for homepage URL.
  - Normalizes URLs lacking schemes (e.g. `example.com` -> `https://example.com`).
  - Persists homepage to active profile in `profiles.json`.
  - Emits `homepage_changed(str)` signal.
- **Spec C6: In-Browser Navigation (`chrome://settings`)**:
  - Navigating URL bar to `chrome://settings` or `about:settings` opens `SettingsView` in active browser window tab or central stack view.

### 3.4 Integration Specifications in `browser.py`
- **Spec D1: Toolbar Gear Button Click**: Clicking `nav_bar.settings_btn` ("⚙") opens/displays `SettingsView` in `PhantomBrowser`.
- **Spec D2: Floating Sparkle Button Click**: Clicking `ai_button` ("✦") toggles `ai_panel` visibility.
- **Spec D3: URL Search Routing Sync**: When user submits a search query in `nav_bar.url_bar`, `PhantomBrowser._navigate_from_input()` checks the active profile's search engine preference and routes to Google or DuckDuckGo accordingly.
- **Spec D4: Profile Selector to Settings Sync**: Switching profile via `ProfileSelector` updates `SettingsView` radio buttons and homepage inputs to match the newly selected profile.
- **Spec D5: Z-Order & Resize Coordination**: Resizing `PhantomBrowser` repositions `ai_button` at bottom-center and aligns `ai_panel` to the right edge.

---

## 4. Required Interface Contract Alignment

To prevent breaking existing test suites (`test_ai_side_panel.py`, `test_settings.py`, `test_e2e_scenarios.py`), real implementations MUST match these attribute contracts:

### 4.1 `ai_panel.py` Class Contracts
```python
class AIFloatingButton(QPushButton):
    # Fixed size 52x52, text features "✦"

class AISidePanel(QWidget):
    # Attributes required:
    # - self.header_label (QLabel: text == "ChatGPT")
    # - self.close_btn (QPushButton: text == "✕")
    # - self.webview (QWebEngineView: loads "https://chatgpt.com")
    # Methods required:
    # - toggle_panel()
    # - show_panel()
    # - hide_panel()
    # - isVisible() -> bool
```

### 4.2 `settings_view.py` Class Contracts
```python
class SettingsView(QWidget):
    # Signals required:
    # - search_engine_changed = pyqtSignal(str)
    # - profile_updated = pyqtSignal()
    # - homepage_changed = pyqtSignal(str)
    # Attributes required:
    # - self.profile_manager (ProfileManager instance)
    # - self.btn_general, self.btn_profiles, self.btn_search, self.btn_appearance, self.btn_about (QPushButton)
    # - self.stack (QStackedWidget)
    # - self.radio_google, self.radio_ddg (QRadioButton)
    # Methods required:
    # - set_search_engine(engine: str)
    # - set_homepage(url: str)
```

---

## 5. Potential Regression Risks & Mitigation Matrix

| # | Risk Area | Potential Failure Impact | Affected Test Files | Mitigation Strategy |
|---|-----------|--------------------------|---------------------|---------------------|
| 1 | **Search Query Routing** | Breaking direct URL parsing (e.g. `github.com`, `localhost`, `file://`) when integrating DuckDuckGo/Google search engine routing in `_navigate_from_input()`. | `test_challenger_m2_1.py`, `test_browser_features.py` | Keep URL scheme detection (`http://`, `https://`, `file://`, `localhost`, domain dot checks without spaces) BEFORE applying profile search engine URL generator. |
| 2 | **Attribute Name Mismatch in Real Modules** | If real `ai_panel.py` or `settings_view.py` drop attributes expected by tests (`close_btn`, `header_label`, `webview`, `btn_search`, etc.), unit tests will raise `AttributeError`. | `test_ai_side_panel.py`, `test_settings.py`, `test_e2e_scenarios.py` | Strictly verify real module class definitions against Section 4 contracts before completing implementation. |
| 3 | **`PhantomBrowser` Central Widget Layout Breakage** | Parent-child layout changes in `browser.py` for `AISidePanel` overlay positioning might break window controls or tab bar corner placement. | `test_challenger_m2_2.py`, `test_ui_and_tabs.py` | Use absolute overlay positioning or parent overlay container for `AIFloatingButton` and `AISidePanel` on `PhantomBrowser`, preserving `workspace_widget` layout. |
| 4 | **Asynchronous WebEngine Load Crashes** | Offscreen execution of ChatGPT webview (`https://chatgpt.com`) causing Qt network thread leaks or segmentation faults on window close. | All headless GUI tests in `tests/` | Use `deleteLater()` in widget teardown and process pending events via `QApplication.processEvents()`. |
| 5 | **Profile Persistence Desynchronization** | Settings engine change not persisting to `profiles.json` or corrupting JSON structure. | `test_profiles.py`, `test_m1_stress_and_edge.py` | Ensure `ProfileManager.update_profile()` uses atomic JSON file writing and updates in-memory profile model. |

---

## 6. Recommended Milestone 3 Test Strategy

1. **Step 1 — Baseline Retention Verification**:
   - Run `pytest tests/ -v` after initial implementation to verify all 142 baseline tests pass.
2. **Step 2 — Feature Unit Test Validation**:
   - Run targeted test commands:
     - `pytest tests/test_ai_side_panel.py -v`
     - `pytest tests/test_settings.py -v`
3. **Step 3 — Integration & Challenger Test Execution**:
   - Run integration suites:
     - `pytest tests/test_e2e_scenarios.py -v`
     - `pytest tests/test_challenger_m2_1.py tests/test_challenger_m2_2.py -v`
4. **Step 4 — Full Regression & Coverage Sweep**:
   - Execute full test suite `pytest tests/ -v` to ensure zero regressions across all 142+ tests.
