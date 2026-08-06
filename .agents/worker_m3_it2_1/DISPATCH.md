## 2026-08-05T13:07:18Z
You are Worker for Milestone 3 Iteration 2 (Remediation of M3 Defects).
Working Directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m3_it2_1

Your task is to remediate the 7 specific issues identified during Milestone 3 Iteration 1 Reviewer evaluation.

Please read the following context files:
1. GATE_STATUS.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\orchestrator\GATE_STATUS.md
2. Reviewer 2 Handoff: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\reviewer_m3_it1_2\handoff.md
3. ORIGINAL_REQUEST.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md

Detailed Remediation Tasks:
1. `ai_panel.py` (Slide-Out Animation Fix):
   In `AISidePanel.hide_panel()`, connect `self.hide` to `self._anim.finished` (and disconnect when done or use single-shot pattern) so the 250ms slide-out animation visually completes before `self.hide()` is called.
2. `browser.py` (Floating Button Visibility Guard):
   In `PhantomBrowser`, hide `AIFloatingButton` when the startup `ProfileSelector` card view is active. Show `AIFloatingButton` only when the browser workspace view is displayed.
3. `browser.py` (AI Side Panel TitleBar Geometry):
   In `_reposition_ai_components()`, position `AISidePanel` below the frameless `TitleBar` (`y = title_bar_height`, `height = bh - title_bar_height`) so top-right window controls (min/max/close) remain accessible.
4. `tab_bar.py` (Settings Tab Close Fallback):
   In `TabWidget.close_tab()`, when closing the last tab (`count() == 1`), if the tab widget is not a `QWebEngineView` (e.g. `SettingsView`), create and replace it with a new default homepage `WebTab`.
5. `settings_view.py` (Sub-page State Synchronization):
   When profile changes are saved in the "Profiles" sub-page, synchronize the search engine radio buttons on the "Search Engine" sub-page and the homepage editor input on the "General" sub-page.
6. `ai_panel.py` (C++ Method Shadowing Fix):
   Replace native `isVisible` override in `AISidePanel` with custom method `is_expanded()`. Ensure `isVisible()` calls native `QWidget.isVisible()`.
7. Socket Cleanup & Test Suite Verification:
   Fix single-instance IPC test timing flakiness in `test_concurrent_acquisition_race` / `test_m1_stress_and_edge.py` / `test_e2e_scenarios.py`. Ensure `pytest tests/ -v` passes 100% (135+ passed, 0 failed).
