# Handoff Report — Feature 7 (Modern Settings Page) Strategy

**Agent**: Explorer 2  
**Milestone**: Milestone 3 (AI Side Panel & Settings System), Iteration 1  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m3_it1_2`  
**Target Module**: `settings_view.py` & `browser.py` / `nav_bar.py` / `styles.py`

---

## 1. Observation

- **Existing Files & Infrastructure**:
  - `profile_manager.py:26`: `VALID_SEARCH_ENGINES = ("Google", "DuckDuckGo")` and `SEARCH_ENGINE_URLS` (`Google`: `https://www.google.com/search?q={}`, `DuckDuckGo`: `https://duckduckgo.com/?q={}`).
  - `profile_manager.py:41-70`: `Profile` dataclass has `search_engine`, `homepage`, and method `get_search_url(query: str) -> str`.
  - `profile_manager.py:72-271`: `ProfileManager` provides `get_all_profiles()`, `get_active_profile()`, `set_active_profile()`, `create_profile()`, `update_profile()`, `delete_profile()`.
  - `nav_bar.py:60-66`: `self.settings_btn` ("⚙") emits `settings_requested` signal.
  - `browser.py:325-328`: `_open_settings()` is currently a placeholder log stub: `logger.info("Settings requested.")`.
  - `tests/test_settings.py`: Contains 10 unit tests specifying the exact attributes, signals, and methods expected on `SettingsView`:
    - Nav button attributes: `btn_general`, `btn_profiles`, `btn_search`, `btn_appearance`, `btn_about`.
    - Stack attribute: `stack` (`QStackedWidget`).
    - Signals: `search_engine_changed(str)`, `profile_updated()`, `homepage_changed(str)`.
    - Methods: `set_search_engine(engine: str)`, `set_homepage(url: str)`.

- **Test Suite Status**: All 142+ existing tests across the project pass cleanly (`pytest tests/ -v`).

---

## 2. Logic Chain

1. **Contract Requirements**: `test_settings.py` tests `SettingsView` by directly inspecting attributes (`btn_general`, `btn_profiles`, `btn_search`, `btn_appearance`, `btn_about`, `stack`, `profile_manager`) and connecting to signals (`search_engine_changed`, `profile_updated`, `homepage_changed`). Therefore, `SettingsView` must define these exact attribute names and signals.
2. **Profile Manager Integration**: `Profile` models already encapsulate `search_engine` ("Google" | "DuckDuckGo") and `homepage`. Calling `ProfileManager.update_profile()` handles atomic JSON persistence to `profiles.json`. Thus, `SettingsView` can delegate persistence directly to `ProfileManager`.
3. **Search Engine URL Formulation**: `Profile.get_search_url(query)` formats queries according to `search_engine`. In `browser.py`, `_navigate_from_input(text)` delegates query formatting to `self._active_profile.get_search_url(cleaned)`. Switching `search_engine` in settings automatically updates query formatting for all subsequent address bar searches.
4. **In-Browser Settings Page Triggering**: Modern Chromium browsers open settings in a tab when clicking the gear icon or navigating to `chrome://settings` / `phantom://settings`. Connecting `nav_bar.settings_requested` to `browser._open_settings()` and adding tab deduplication ensures seamless user experience while satisfying Requirement R5.

---

## 3. Caveats

- **Tab vs Overlay View**: `test_settings.py` instantiates `SettingsView` directly as a standalone `QWidget`. The design ensures `SettingsView` operates as a standalone `QWidget` that can be added into `TabWidget` or viewed independently without coupling bugs.
- **Profile Deletion Safety**: Deleting the last profile in `ProfileManager` is blocked by `ProfileManager.delete_profile()`. The UI in `SettingsView` must gracefully display a warning message if a user attempts to delete the last profile.

---

## 4. Conclusion

Implement `settings_view.py` containing `SettingsView(QWidget)`:
1. **Layout**: Two-column layout with left glassmorphic sidebar containing `btn_general`, `btn_profiles`, `btn_search`, `btn_appearance`, `btn_about`, and right `QStackedWidget` (`self.stack`) containing 5 section pages.
2. **Search Engine**: Selection controls for Google vs DuckDuckGo; `set_search_engine(engine)` updates active profile in `ProfileManager` and emits `search_engine_changed(str)`.
3. **Profile CRUD**: Full active profile view/edit, profile switcher, profile creation, and safe profile deletion. Emits `profile_updated()`.
4. **General & Scheme Handling**: Homepage editor with `set_homepage(url)` auto-prepending `https://` when scheme is missing. Emits `homepage_changed(str)`.
5. **Appearance & About**: Dark mode toggle, accent highlight selector, browser version info, and stealth capabilities summary (`SetWindowDisplayAffinity`, zero-cookie OTR storage, IPC single instance, `Ctrl+Shift+B` hotkey).
6. **Browser Integration**: Wire gear icon in `nav_bar.py` and `phantom://settings` / `chrome://settings` in `browser.py` to open `SettingsView` as a dedicated browser tab with deduplication.

---

## 5. Verification Method

### 5.1 Independent Test Command
Run the dedicated settings test suite:
```powershell
pytest tests/test_settings.py -v
```

### 5.2 Specific Files to Inspect
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\settings_view.py` (New module to create)
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\browser.py` (Update `_open_settings` & `_navigate_from_input`)
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\styles.py` (Add settings QSS rules)

### 5.3 Invalidation Conditions
- Missing any required attribute name on `SettingsView` (`btn_general`, `btn_profiles`, `btn_search`, `btn_appearance`, `btn_about`, `stack`).
- Failing to auto-prepend `https://` to homepages missing a URL scheme.
- Search queries using Google when active search engine preference is set to DuckDuckGo (or vice versa).
