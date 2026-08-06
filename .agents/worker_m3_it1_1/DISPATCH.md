## 2026-08-05T12:50:32Z
You are Worker for Milestone 3 (AI Side Panel & Settings System).
Working Directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m3_it1_1

Your task is to implement Feature 6 (AI Side Panel & Sparkle Button) and Feature 7 (Modern Settings View & Search Engine Switcher) for the Phantom Workspace Overhaul.

Please read the following specification and context files before beginning:
1. ORIGINAL_REQUEST.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md
2. PROJECT.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
3. Explorer 1 Handoff Report: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m3_it1_1\handoff.md
4. Explorer 2 Handoff Report: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m3_it1_2\handoff.md
5. Explorer 3 Handoff Report: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m3_it1_3\handoff.md

Detailed Requirements:
1. Implement `ai_panel.py` in project root:
   - `AIFloatingButton(QPushButton)`: 52x52px circular button (`border-radius: 26px`) with objectName `"AIFloatingButton"`, icon/text `✦`,styled with indigo glass gradient and animated `QGraphicsDropShadowEffect` glow pulse. Positioned bottom-center of browser view (`(width-52)//2, height-52-24`).
   - `AISidePanel(QWidget)`: width 380–420px (e.g. 400px) with objectName `"AISidePanel"`. 42px header bar with `header_label` (`QLabel("ChatGPT")`) and `close_btn` (`QPushButton("✕")`), and embedded `webview` (`QWebEngineView`) loading `https://chatgpt.com`.
   - Toggle animation via `QPropertyAnimation(self, b"geometry")` over 250ms with `QEasingCurve.Type.OutCubic` and boolean `_is_expanded` guard.
   - Methods: `show_panel()`, `hide_panel()`, `toggle_panel()`.

2. Implement `settings_view.py` in project root:
   - `SettingsView(QWidget)`: Two-column layout with left glassmorphic sidebar containing nav buttons (`btn_general`, `btn_profiles`, `btn_search`, `btn_appearance`, `btn_about`) and right `QStackedWidget` (`self.stack`) containing 5 section pages.
   - Radio buttons / controls for Search Engine switcher (`radio_google`, `radio_ddg`), calling `ProfileManager` and emitting `search_engine_changed(str)`.
   - Profile CRUD section for profile view/edit/create/delete, emitting `profile_updated()`.
   - General section for homepage editor (auto-prepending `https://` if scheme missing), emitting `homepage_changed(str)`.
   - Methods: `set_search_engine(engine: str)`, `set_homepage(url: str)`.

3. Integrate in `browser.py`, `nav_bar.py`, and `styles.py`:
   - Wire `AIFloatingButton` and `AISidePanel` into `PhantomBrowser`, handling click triggers, resize events, and z-ordering.
   - Wire gear icon ("⚙") in `nav_bar.py` and URL inputs `chrome://settings` / `phantom://settings` in `browser.py` to open `SettingsView` as a dedicated deduplicated tab.
   - Update `_navigate_from_input()` in `browser.py` to use active profile search engine when input is not a direct URL/scheme.
   - Add QSS rules for `#AIFloatingButton`, `#AISidePanel`, and `#SettingsView` components into `styles.py`.

4. Verification:
   - Run tests: `pytest tests/ -v`
   - Verify all tests pass (including `test_ai_side_panel.py` and `test_settings.py`).
