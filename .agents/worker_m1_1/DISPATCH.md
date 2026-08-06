## 2026-08-05T01:11:34Z
You are Worker 1 for Milestone 1 (M1: Profile System & Single Instance).
Working directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m1_1

Input Files to Read:
1. ORIGINAL_REQUEST.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md
2. PROJECT.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
3. SCOPE.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\sub_orch_m1\SCOPE.md
4. Explorer 1 Handoff: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_1\handoff.md
5. Explorer 2 Handoff: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2\handoff.md
6. Explorer 3 Handoff: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_3\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Task:
Implement Milestone 1 functionality cleanly and robustly in C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser:

1. `profile_manager.py`:
   - Data model `Profile` with fields: `id`, `name`, `avatar`, `homepage`, `search_engine`, `theme_color`. Includes `to_dict()`, `from_dict()`, `get_search_url()`.
   - `ProfileManager` class: handles loading/saving `profiles.json` with atomic file replace (`.tmp`), auto-creates default profiles if missing or corrupt, validates `search_engine` (defaults to `"Google"` if invalid), CRUD operations (`create_profile`, `update_profile`, `delete_profile`, `get_all_profiles`, `get_profile_by_id`, `get_active_profile`, `set_active_profile`). Prevent deleting the last remaining profile (`return False`). Auto-switch active profile if current active profile is deleted.
   - `create_otr_web_profile(profile, parent=None)`: Factory returning a `QWebEngineProfile` instance with `isOffTheRecord() == True`, `NoPersistentCookies`, `MemoryHttpCache`, persistentStoragePath="", cachePath="".

2. `single_instance.py`:
   - `SingleInstanceGuard(QObject)` with signal `activation_requested = pyqtSignal()`, and alias `activated = activation_requested`.
   - `try_acquire(app_key: str = None) -> bool`: Raises `ValueError` if `app_key` is empty or whitespace. Uses `QLocalServer`/`QLocalSocket` named pipe IPC.
   - Socket handshake: Second instance connects, writes `b"ACTIVATE\n"`, primary handles connection/read, emits `activation_requested` signal, second instance returns `False` (for main to exit code 0).
   - Stale socket handling: Calls `QLocalServer.removeServer(server_name)` before starting `listen()`.
   - `release(app_key: str = None) -> None`: Idempotent release method closing server and removing server socket name.

3. `main.py` & `browser.py` Integration:
   - Integrate `SingleInstanceGuard` in `main.py` so secondary instance exits cleanly with code 0.
   - Add `activate_window_to_front()` helper method to `PhantomBrowser` in `browser.py` (`show()`, `showNormal()`, `raise_()`, `activateWindow()`).
   - Integrate `ProfileManager` and `create_otr_web_profile` in browser setup.

4. Test Execution & Verification:
   - Run unit tests: `pytest tests/test_profiles.py tests/test_single_instance.py -v`
   - Run full test suite: `pytest tests/ -v`
   - Ensure all 20 tests pass.

Write a complete report with implementation details and test command output to `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m1_1\handoff.md` and report back when finished.
