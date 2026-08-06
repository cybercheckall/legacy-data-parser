## 2026-08-06T05:29:15Z
You are a teamwork_preview_worker agent.
Your working directory is `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_worker_m1_m4`.

Read `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md`, `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md`, and the Explorer handoff reports at:
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_explorer_m1_m2\handoff.md`
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_explorer_m3_m4\handoff.md`
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_explorer_tests\handoff.md`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Task:
Implement all code modifications for Milestones M1, M2, M3, and M4, and verify non-regression:

1. **M1 (Guest Mode Profile Selector)**:
   - Update root `profiles.json` and `profile_manager.py` so Guest mode (`id="guest"`, `name="Guest mode"`, `avatar="👤"`, `homepage="https://www.google.com"`, `search_engine="Google"`, `theme_color="#533483"`) is the single default active profile.

2. **M2 (Window Transparency Slider)**:
   - In `title_bar.py`:
     - Import `QSlider` from `PyQt6.QtWidgets`.
     - In `TitleBar.__init__`: create `self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)`, `setObjectName("OpacitySlider")`, `setRange(10, 100)`, `setValue(100)`, tooltip `"Window Opacity (10% - 100%)"`.
     - Insert `opacity_slider` into title bar layout between title label and window control buttons (minimize/maximize/close).
     - Connect `valueChanged` to `_on_opacity_changed(self, value: int)` calling `win.setWindowOpacity(value / 100.0)`.
     - In `TitleBar.mousePressEvent`, add guard: `if hasattr(self, "opacity_slider") and self.opacity_slider.geometry().contains(event.position().toPoint()): event.ignore(); return` to prevent window dragging when interacting with slider.
   - In `styles.py`: Append QSS styling rules for `QSlider#OpacitySlider` (groove, sub-page, handle, handle hover).

3. **M3 (Chrome-style Tab Bar with Adjacent '+' Button)**:
   - In `tab_bar.py`:
     - Parent `self.new_tab_btn` to `self` or `self.tabBar()` instead of calling `setCornerWidget`.
     - Implement override `cornerWidget(self, corner=Qt.Corner.TopRightCorner)` returning `self.new_tab_btn` for test backward compatibility.
     - Add `_update_new_tab_btn_pos(self)` calculating `last_rect = self.tabBar().tabRect(self.count() - 1)` and positioning `self.new_tab_btn` at `last_rect.right() + 4` (y-centered).
     - Connect `_update_new_tab_btn_pos()` to tab additions/removals/changes and `resizeEvent`.

4. **M4 (Clean Google Search Homepage & Standard Nav Bar)**:
   - In `browser.py`:
     - Set default `HOME_URL = "https://www.google.com"`.
     - In `_build_workspace_ui()`, do not add `self.bookmarks_bar` to `ws_layout` (or call `self.bookmarks_bar.hide()`), removing the quick-links shortcuts bar from the UI while keeping `self.bookmarks_bar` attribute intact.
     - Keep `NavBar`, `AIFloatingButton` (sparkle icon button at bottom center), and `AISidePanel` 100% intact and functional.

5. **Test Updates & Verification**:
   - Update tests in `tests/` if needed for M1-M4 features.
   - Run `pytest` from `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`.
   - Verify all 159 automated tests pass with 100% success rate.

When finished, write your report to `handoff.md` in your working directory, document build/test commands and output, and send a message back to the orchestrator.
