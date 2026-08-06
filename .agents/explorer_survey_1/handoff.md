# Handoff Report: Explorer Survey 1 — Owl Stealth Browser Architecture & UI Survey

## 1. Observation

### 1.1 Architecture & Module Inventory
The codebase is a PyQt6-based Chromium stealth workspace browser named **Owl**. Key system entry points and modules:

| Module / File | Primary Class / Functions | Description & Responsibilities | Line Reference |
|---|---|---|---|
| `main.py` | `main()` | Application entry point, logging configuration, `SingleInstanceGuard` acquire, QSS stylesheet application, `OwlBrowser` window creation, `GlobalHotkey` listener start. | `main.py:27-94` |
| `browser.py` | `OwlBrowser`, `WebTab` | Main `QMainWindow` assembling `TitleBar`, `NavBar`, `bookmarks_bar`, `TabWidget` (`tab_widget`), `ProfileSelector` (in `_central_stack`), `AIFloatingButton`, `AISidePanel`. | `browser.py:64-440` |
| `profile_manager.py` | `ProfileManager`, `Profile`, `create_otr_web_profile` | Dataclass `Profile`, atomic JSON persistence (`profiles.json`), off-the-record ephemeral `QWebEngineProfile` generator (`NoPersistentCookies`, `MemoryHttpCache`). | `profile_manager.py:40-284` |
| `profile_selector.py` | `ProfileSelector` | Startup overlay and profile picker screen rendering clickable profile cards with avatars and badges. | `profile_selector.py:18-114` |
| `title_bar.py` | `TitleBar` | Custom 34px dark glass title bar with `title_label` ("🦉 Owl"), `min_btn`, `max_btn`, `close_btn`, frameless window mouse drag & double-click maximize logic. | `title_bar.py:13-119` |
| `tab_bar.py` | `TabWidget` | Document-mode closable/movable `QTabWidget` with '+' new tab button (`new_tab_btn`), dynamic title truncation, and last-tab homepage fallback. | `tab_bar.py:14-98` |
| `nav_bar.py` | `NavBar` | 40px reload-only navigation bar with `reload_btn` ("⟳"), prominent `url_bar` (`QLineEdit`), `settings_btn` ("⚙"), `profile_btn` ("👤"), and hidden `back_btn`/`fwd_btn`. | `nav_bar.py:12-90` |
| `styles.py` | `DARK_GLASS_STYLE` | Application-wide QSS stylesheet defining dark glass visual theme, color tokens, rounded borders, and button hover states. | `styles.py:9-305` |
| `ai_panel.py` | `AIFloatingButton`, `AISidePanel` | 52x52px circular floating button with pulse glow and 400px wide slide-in side panel containing embedded `QWebEngineView("https://chatgpt.com")`. | `ai_panel.py:20-182` |
| `settings_view.py` | `SettingsView` | In-browser `owl://settings` page with sidebar navigation for General, Profiles, Search Engine, Appearance, About. | `settings_view.py:24-542` |
| `display_affinity.py` | `apply_display_affinity(hwnd)` | Applies Win32 `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE = 0x11)` for screen capture invisibility. | `display_affinity.py:14-41` |
| `hotkey.py` | `GlobalHotkey` | Background `pynput` listener monitoring `Ctrl+Shift+B` to toggle window visibility. | `hotkey.py:12-74` |
| `single_instance.py` | `SingleInstanceGuard` | Enforces single-instance app execution via `QLocalServer`/`QLocalSocket` IPC. | `single_instance.py:15-110` |

### 1.2 Automated Test Suite Status
The test suite consists of 159 tests located under `tests/` (`test_ui_and_tabs.py`, `test_challenger_m2_1.py`, `test_challenger_m2_2.py`, `test_ai_side_panel.py`, `test_profiles.py`, `test_stealth.py`, etc.). Execution via `pytest` passes with 100% pass rate.

---

## 2. Logic Chain & Proposed Implementation Blueprint

### 2.1 Requirement R1: Profile Selector — Guest Mode Initial Option
- **Direct Observation**:
  - `profile_manager.py:91-111` (`_create_defaults()`): Currently auto-creates two initial profiles: "Default Profile" and "Work Profile".
  - `profile_selector.py:61-68`: Renders card buttons for every profile present in `self.profiles`.
  - `browser.py:110-113`: Checks `if show_profile_selector_on_start and len(self._profile_manager.load_profiles()) > 1:` before launching selector view.
- **Logic & Proposed Change**:
  1. Modify `_create_defaults()` in `profile_manager.py` to create a single **Guest mode** profile as the initial default:
     ```python
     guest_prof = Profile(
         id="guest",
         name="Guest mode",
         avatar="👤",
         homepage="https://www.google.com",
         search_engine="Google",
         theme_color="#533483",
     )
     self.profiles = [guest_prof]
     self.active_profile_id = guest_prof.id
     self.save_profiles()
     return self.profiles
     ```
  2. Update `browser.py:110` so that `show_profile_selector()` is invoked whenever `show_profile_selector_on_start` is enabled (even with 1 profile), ensuring users see the Guest mode selector on launch.

---

### 2.2 Requirement R2: Title Bar Transparency Slider
- **Direct Observation**:
  - `title_bar.py:23-60`: `TitleBar` builds layout: `title_label` -> `addStretch()` -> `min_btn` -> `max_btn` -> `close_btn`.
  - PyQt6 `QMainWindow` supports dynamic opacity via `setWindowOpacity(float_val)` (0.0 to 1.0).
- **Logic & Proposed Change**:
  1. In `title_bar.py`: Add a horizontal `QSlider` (`self.opacity_slider` / `self.transparency_slider`):
     ```python
     self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
     self.opacity_slider.setObjectName("OpacitySlider")
     self.opacity_slider.setRange(20, 100)  # 20% to 100% opacity
     self.opacity_slider.setValue(100)
     self.opacity_slider.setFixedWidth(110)
     self.opacity_slider.setToolTip("Window Opacity / Transparency")
     self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
     ```
  2. Connect value changes to update parent window opacity:
     ```python
     def _on_opacity_changed(self, value: int):
         opacity = value / 100.0
         win = self.window()
         if win and hasattr(win, "setWindowOpacity"):
             win.setWindowOpacity(opacity)
     ```
  3. Layout placement: Place `self.opacity_slider` inside `TitleBar`'s layout between `title_label` (after stretch) and window controls (`min_btn`, `max_btn`, `close_btn`).
  4. In `styles.py`: Add styling rules for `#OpacitySlider::groove:horizontal` and `#OpacitySlider::handle:horizontal` matching the dark glass design.

---

### 2.3 Requirement R3: Chrome-Style Tabs & Adjacent '+' Button
- **Direct Observation**:
  - `tab_bar.py:28-32`: Currently sets `self.setCornerWidget(self.new_tab_btn, Qt.Corner.TopRightCorner)`, fixing the '+' button at the far right of the widget.
  - `styles.py:126-150`: Defines `QTabBar::tab` QSS styling with rounded top corners (`border-top-left-radius: 10px; border-top-right-radius: 10px;`).
- **Logic & Proposed Change**:
  1. Redesign `tab_bar.py` so that `new_tab_btn` is positioned **immediately to the right of the last active tab**.
  2. Implementation approach:
     - Keep `self.new_tab_btn` attribute on `TabWidget` (and retain `cornerWidget` fallback setter for unit test contract compatibility in `test_ui_and_tabs.py:61-62`).
     - Subclass or handle `QTabBar` / layout updates: after tabs are added, removed, or resized, calculate the geometry of the rightmost tab (`last_rect = self.tabBar().tabRect(self.count() - 1)`), and dynamically position `self.new_tab_btn` at `last_rect.right() + 4`.
  3. Enhance QSS in `styles.py` for Chrome-style tab visual accuracy: rounded top corners, subtle active indicator line, and smooth hover state.

---

### 2.4 Requirement R4: Custom Homepage & Navigation Bar AI Mode Button
- **Direct Observation**:
  - `browser.py:35-44` (`BOOKMARKS` array): Defines quick-links to ChatGPT, Claude, Google, Stack Overflow, GitHub, LeetCode, which are rendered in `bookmarks_bar` (`browser.py:189-205`).
  - `nav_bar.py:43-76`: Layout contains `reload_btn`, `url_bar`, `settings_btn`, `profile_btn`.
- **Logic & Proposed Change**:
  1. **Default Homepage**: Set `HOME_URL = "https://www.google.com"` in `browser.py:44` and set default profile homepage to `"https://www.google.com"`.
  2. **Remove Quick-Links**: Remove or hide `self.bookmarks_bar` from `browser.py:189-205` so quick-links / shortcuts to ChatGPT, Claude, Google, Stack Overflow, GitHub, and LeetCode are completely removed.
  3. **"AI Mode" Button in Nav Bar**:
     - In `nav_bar.py`: Add `self.ai_mode_btn = QPushButton("✦ AI Mode", self)` with object name `#AIModeBtn`.
     - Position `self.ai_mode_btn` inside `NavBar` layout (e.g. between `url_bar` and `settings_btn`).
     - Add signal `ai_mode_requested = pyqtSignal()`.
     - In `browser.py`: Connect `nav_bar.ai_mode_requested` to `self.ai_panel.toggle_panel`.

---

### 2.5 Requirement R5: Stealth Features Preservation
- **Direct Observation**:
  - Display Affinity: `display_affinity.py:14-41` (`SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)`).
  - Window Flags: `browser.py:78-82` (`Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool`).
  - Global Hotkey: `hotkey.py:12-74` (`Ctrl+Shift+B` toggle).
- **Logic & Proposed Change**:
  - Retain all window flags, timer-based display affinity setup, and `GlobalHotkey` listener without alteration. All 159 automated tests verify these stealth features continuously.

---

## 3. Caveats

1. **Test Suite Contract Compatibility**:
   - `tests/test_ui_and_tabs.py:61-62` asserts `self.assertEqual(corner_widget, self.tab_widget.new_tab_btn)`. When positioning `new_tab_btn` dynamically adjacent to tabs, ensure `self.new_tab_btn` attribute and `cornerWidget` compatibility remain functional so test assertions pass without regression.
2. **Network Dependency for WebEngine**:
   - Real page rendering of `https://www.google.com` and `https://chatgpt.com` requires network connectivity in manual runtime testing, whereas unit tests mock WebEngine pages.
3. **Display Affinity Platform Guard**:
   - Win32 `SetWindowDisplayAffinity` requires native HWND on Windows 10/11. On non-Windows platforms or virtual displays, `display_affinity.py` logs warnings without causing application failure.

---

## 4. Conclusion

The codebase architecture of Owl is highly modular, well-encapsulated, and ready for implementation. The proposed architectural plan for Requirements R1 through R4 provides explicit file paths, precise code modifications, and exact QSS styling details while ensuring 100% backward compatibility and stealth feature preservation (R5).

---

## 5. Verification Method

### 5.1 Automated Test Verification
Run the complete automated test suite from project root:
```powershell
pytest
```
*Expected Result*: 159 passed tests with 0 failures.

### 5.2 Manual UI Verification Steps
1. **Launch Application**: Execute `python main.py`.
2. **Profile Selector (R1)**: Verify that application startup opens the Profile Selector UI showing "Guest mode" option.
3. **Transparency Slider (R2)**: Move slider in the custom TitleBar left and right to verify dynamic window opacity adjustment.
4. **Chrome-Style Tabs (R3)**: Confirm tabs have rounded top corners and '+' new tab button sits directly to the right of the active tab.
5. **Homepage & AI Mode Button (R4)**:
   - Confirm new tabs open to a clean Google search page (`https://www.google.com`).
   - Confirm quick-link shortcuts (ChatGPT, Claude, Google, Stack Overflow, GitHub, LeetCode) are removed.
   - Click "✦ AI Mode" button in the navigation bar to verify smooth slide-in of ChatGPT side panel.
6. **Stealth Verification (R5)**:
   - Press `Ctrl+Shift+B` to verify global window hide/show toggle.
   - Test screen share / screen capture software to confirm window invisibility via display affinity.
