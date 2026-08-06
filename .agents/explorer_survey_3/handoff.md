# Stealth Features & Regression Risk Survey Report

## Executive Summary
This survey report details the architecture, file locations, exact Win32 API / Qt flag implementations, and regression risks for the four stealth features of **Owl Browser** (`SetWindowDisplayAffinity` / `WDA_EXCLUDEFROMCAPTURE`, `WS_EX_TOOLWINDOW`, `WindowStaysOnTopHint`, and `Ctrl+Shift+B` global hotkey). Additionally, it identifies specific collision vectors and mitigation strategies for upcoming requirements **R1** (Guest Mode Profile Selector), **R2** (Title Bar Transparency Slider), **R3** (Chrome-style Adjacent Tab Button), and **R4** (Google Homepage & AI Mode Button in Navigation Bar).

---

## 1. Observation

### A. Core Stealth Features Architecture & Code References

#### 1. Display Affinity Protection (`WDA_EXCLUDEFROMCAPTURE`)
* **Location**: `display_affinity.py` (lines 11–40) & `browser.py` (lines 22, 116, 273–280).
* **Exact Constant**: `WDA_EXCLUDEFROMCAPTURE = 0x00000011` (decimal `17`).
* **Implementation snippet** (`display_affinity.py`):
  ```python
  WDA_EXCLUDEFROMCAPTURE = 0x00000011

  def apply_display_affinity(hwnd: int) -> bool:
      if not hwnd or hwnd < 0:
          logger.warning("Invalid HWND: %s", hwnd)
          return False
      try:
          user32 = ctypes.windll.user32
          result = user32.SetWindowDisplayAffinity(
              wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE
          )
          return bool(result)
      except Exception as e:
          logger.error("Exception applying display affinity: %s", e)
          return False
  ```
* **Call Site in `browser.py`**:
  ```python
  # Initialized during OwlBrowser setup via 100ms single-shot timer to ensure valid native HWND:
  QTimer.singleShot(100, self._apply_stealth)

  def _apply_stealth(self):
      hwnd = int(self.winId())
      success = apply_display_affinity(hwnd)
  ```
* **Test Suite Files**: `tests/test_stealth.py` (lines 40–44, 96–105), `tests/test_stealth_affinity.py` (lines 36–54, 87–89), `tests/conftest.py` (lines 58–88).

#### 2. Taskbar Icon Suppression (`WS_EX_TOOLWINDOW` / `Qt.WindowType.Tool`)
* **Location**: `browser.py` (lines 78–82).
* **Implementation snippet** (`browser.py`):
  ```python
  self.setWindowFlags(
      Qt.WindowType.Window
      | Qt.WindowType.WindowStaysOnTopHint
      | Qt.WindowType.Tool
  )
  ```
* **Behavior**: Applying `Qt.WindowType.Tool` maps to Win32 extended window style `WS_EX_TOOLWINDOW` (`0x00000080`), suppressing the window button from the Windows Taskbar and Alt+Tab application switcher.
* **Test Suite Files**: `tests/test_stealth.py` (lines 46–52), `tests/test_stealth_affinity.py` (lines 55–61), `tests/conftest.py` (line 567).

#### 3. Always On Top (`WindowStaysOnTopHint`)
* **Location**: `browser.py` (lines 78–82).
* **Behavior**: Maps to Win32 `HWND_TOPMOST` z-order positioning. Keeps the browser window floating above all non-topmost desktop applications.
* **Test Suite Files**: `tests/test_stealth.py` (lines 54–60), `tests/test_stealth_affinity.py` (lines 63–69).

#### 4. Global Hotkey (`Ctrl+Shift+B`) & Visibility Toggle
* **Location**: `hotkey.py` (lines 12–74), `main.py` (lines 70–81), `browser.py` (line 271).
* **Implementation snippet** (`hotkey.py`):
  ```python
  class GlobalHotkey:
      def __init__(self, on_toggle: Callable):
          self._on_toggle = on_toggle
          self._target_keys = {"ctrl", "shift", "b"}
  ```
* **Toggle logic in `main.py`**:
  ```python
  def toggle_browser():
      if browser.isVisible():
          browser.hide()
          logger.info("Browser hidden via global hotkey")
      else:
          browser.show()
          browser.activateWindow()
          browser.raise_()
          logger.info("Browser shown via global hotkey")
  ```
* **Escape Key Backup**: `QShortcut(QKeySequence("Escape"), self, self.hide)` in `browser.py` line 271.
* **Test Suite Files**: `tests/test_hotkey.py` (lines 35–60), `tests/test_stealth.py` (lines 62–70, 84–94).

### B. Current Baseline Test Suite Execution
* **Execution Command**: `pytest`
* **Result**: `159 passed in 76.01s (0:01:16)`
* **Status**: 100% pass rate across all 159 tests (unit, challenger, e2e, stealth, hotkey, profiles, settings, single instance).

---

## 2. Logic Chain

From the direct observations above, the step-by-step reasoning maps stealth feature mechanics to potential collision vectors when implementing requirements **R1** through **R4**:

### Step 1: Display Affinity (`WDA_EXCLUDEFROMCAPTURE`) & Transparency Slider (R2)
* **Observation**: `apply_display_affinity` binds `WDA_EXCLUDEFROMCAPTURE` (`0x11`) to a specific native Windows `HWND` via `ctypes.windll.user32.SetWindowDisplayAffinity`.
* **Reasoning**: In PyQt6 / Win32, modifying window opacity via `self.setWindowOpacity(val)` uses Win32 layered window attributes (`SetLayeredWindowAttributes`). Directly calling `setWindowOpacity()` retains the existing HWND. However, if code dynamically modifies window flags (e.g. `self.setWindowFlags(...)`), Qt destroys and recreates the underlying Win32 HWND. Any display affinity set on the old HWND is lost upon HWND recreation.
* **Collision Vector**: If the transparency slider implementation triggers window flag changes or HWND recreation, `WDA_EXCLUDEFROMCAPTURE` will silently stop working.
* **Mitigation Strategy**: Opacity adjustments must call `self.setWindowOpacity(float_val)` directly without modifying `windowFlags()`. If window flags are ever re-evaluated, `_apply_stealth()` must be re-invoked immediately on the new HWND.

### Step 2: Taskbar Suppression (`WS_EX_TOOLWINDOW`) & Profile Selector UI (R1)
* **Observation**: `OwlBrowser` currently sets `Qt.WindowType.Tool` on `self` during `__init__`, and `ProfileSelector` is hosted inside `OwlBrowser._central_stack` (a `QStackedWidget`).
* **Reasoning**: `ProfileSelector` inside `_central_stack` shares `OwlBrowser`'s single HWND and inherits `Qt.WindowType.Tool` and `Qt.WindowType.WindowStaysOnTopHint`.
* **Collision Vector**: If `ProfileSelector` is refactored into a separate standalone `QDialog` or `QMainWindow` prior to creating `OwlBrowser`, that secondary window will lack `Qt.WindowType.Tool` and will pop up in the Windows Taskbar, violating stealth requirements (R6/R5).
* **Mitigation Strategy**: Keep `ProfileSelector` integrated inside `_central_stack` of `OwlBrowser` (or explicitly set `Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint` on any dialog window created).

### Step 3: Frameless Window Dragging & TitleBar Slider (R2)
* **Observation**: `TitleBar` in `title_bar.py` overrides `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent` to drag `OwlBrowser` across the screen.
* **Reasoning**: Unhandled mouse events on child widgets inside `TitleBar` propagate upward to `TitleBar` handlers.
* **Collision Vector**: Adding a `QSlider` into `TitleBar` without consuming mouse drag events will cause clicking/dragging the slider handle to drag the entire browser window instead of adjusting opacity. Also, allowing opacity to slide down to `0.0` (0%) will make the window completely invisible and un-clickable.
* **Mitigation Strategy**: 
  1. The opacity slider must accept mouse press and move events (`event.accept()`).
  2. `TitleBar.mousePressEvent` should check `if self.opacity_slider.geometry().contains(event.pos())` and bypass window movement when interacting with the slider.
  3. Clamp the slider range to `0.10`–`1.00` (10% to 100%) so the window remains subtly visible even at minimum slider setting.

### Step 4: Chrome-Style Tab Bar (R3) & Test Contract Compatibility
* **Observation**: `tab_bar.py` defines `TabWidget` with a public attribute `self.new_tab_btn = QPushButton("+", self)` positioned via `self.setCornerWidget(self.new_tab_btn, Qt.Corner.TopRightCorner)`. Existing test files (`test_ui_and_tabs.py`, `test_challenger_m2_1.py`, `conftest.py`) directly reference `tab_widget.new_tab_btn`.
* **Reasoning**: R3 requires placing the `+` button immediately adjacent to the right side of the active tab rather than fixed at the far right corner of the window.
* **Collision Vector**: Renaming or removing `self.new_tab_btn` will break test contract assertions in `test_ui_and_tabs.py` and cause test failures.
* **Mitigation Strategy**: Retain `self.new_tab_btn` as a public `QPushButton` instance emitting `new_tab_requested`, but position it dynamically adjacent to tabs (e.g. inside a custom tab bar layout or `QTabBar` button container).

### Step 5: Custom Google Homepage & AI Button (R4)
* **Observation**: `browser.py` sets `HOME_URL = "https://www.google.com"`, and `NavBar` in `nav_bar.py` holds URL bar controls. `bookmarks_bar` displays quick-link buttons.
* **Reasoning**: R4 requires defaulting homepage to clean Google search, removing quick-links shortcuts, and embedding an "AI Mode" button in the navigation bar.
* **Collision Vector**: Test files (e.g. `test_browser_features.py`) or mock setups in `conftest.py` may reference `bookmarks_bar` or `BOOKMARKS`.
* **Mitigation Strategy**: Hide `bookmarks_bar` or preserve the attribute while removing quick-link buttons from the UI layout. Wire the new `ai_mode_btn` in `NavBar` to call `self.ai_panel.toggle_panel()`.

---

## 3. Caveats

* **OS Platform Constraint**: `SetWindowDisplayAffinity` (`WDA_EXCLUDEFROMCAPTURE = 0x11`) is a Windows 10+ (Version 2004 or higher) native Win32 API. In non-Windows OS or offscreen test environments (`QT_QPA_PLATFORM=offscreen`), `conftest.py` provides a mock fallback wrapper (`safe_apply`) to ensure unit test passability without Win32 DLLs.
* **Global Hotkey Threading**: `pynput.keyboard.Listener` executes callback functions on a background thread. Calling Qt UI methods directly from non-GUI threads can occasionally cause cross-thread UI warnings. The existing architecture calls `browser.hide()` / `show()` directly, which is tested and working, but implementations should avoid heavy blocking operations inside hotkey callbacks.
* **DWM Hardware Acceleration**: In virtual machine environments lacking DWM hardware acceleration, window opacity (`setWindowOpacity`) and display affinity rendering may exhibit slight visual artifacts, though API calls succeed.

---

## 4. Conclusion

All 4 stealth features are robustly integrated and passing 100% of automated tests:
1. **`WDA_EXCLUDEFROMCAPTURE`**: Functioning in `display_affinity.py` & `browser.py` (`_apply_stealth`).
2. **`WS_EX_TOOLWINDOW`**: Applied via `Qt.WindowType.Tool` on `OwlBrowser`.
3. **`WindowStaysOnTopHint`**: Applied via `Qt.WindowType.WindowStaysOnTopHint` on `OwlBrowser`.
4. **`Ctrl+Shift+B` Hotkey**: Running via `GlobalHotkey` daemon listener in `hotkey.py` / `main.py`.

### Actionable Implementation Guidance for Next Phase:
* **R1 (Guest Mode Profile Selector)**: Embed Profile Selector inside `OwlBrowser._central_stack` so it inherits taskbar suppression (`WS_EX_TOOLWINDOW`), stay-on-top, and display affinity without creating secondary HWNDs.
* **R2 (Transparency Slider)**: Place `QSlider` in `TitleBar`, consume mouse events to prevent window dragging, clamp range to 10%–100%, and apply opacity via `setWindowOpacity()` without re-creating window flags.
* **R3 (Chrome Tabs)**: Reposition `+` button adjacent to active tab while preserving `tab_widget.new_tab_btn` attribute and `new_tab_requested` signal contract.
* **R4 (Homepage & AI Button)**: Default homepage to `https://www.google.com`, remove homepage quick-link shortcut UI, and connect navigation bar "AI Mode" button to `ai_panel.toggle_panel()`.

---

## 5. Verification Method

### 1. Automated Test Suite Verification
Run the complete pytest suite to confirm 100% pass rate:
```bash
pytest
```
*Expected Output*: `159 passed in ~76s`.

### 2. Specific Stealth Test Suite Verification
Run dedicated stealth test modules:
```bash
pytest tests/test_stealth.py
pytest tests/test_stealth_affinity.py
pytest tests/test_hotkey.py
```
*Expected Output*: All stealth tests pass cleanly without errors.

### 3. Manual Feature Inspection Checklist
1. **Launch App**: Execute `python main.py`.
2. **Taskbar Check**: Verify no icon appears in the Windows Taskbar or Alt+Tab switcher (`WS_EX_TOOLWINDOW`).
3. **Always On Top Check**: Open another application (e.g. Notepad) and click it — verify `OwlBrowser` remains on top (`WindowStaysOnTopHint`).
4. **Display Affinity Check**: Open Windows Snipping Tool / OBS / Zoom screen share and capture the browser window — verify the captured region is solid black (`WDA_EXCLUDEFROMCAPTURE = 0x11`).
5. **Hotkey Check**: Press `Ctrl+Shift+B` globally from any application — verify `OwlBrowser` toggles hidden -> visible -> hidden.
6. **Opacity Slider Check**: Slide transparency control in `TitleBar` — verify browser opacity dims smoothly while window movement and display affinity protection remain active.
