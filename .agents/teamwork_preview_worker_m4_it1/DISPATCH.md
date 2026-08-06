## 2026-08-06T00:06:20Z

You are the Implementation Worker for Milestone 4 (Rebranding to "Owl", Iconography, Spec File, Stealth Verification & Test Suite Clearance) of the Owl browser project located at C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser.
Your working directory is C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_worker_m4_it1.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY ASSIGNMENT & READINGS:
Read the following authoritative files first before modifying any code:
- ORIGINAL_REQUEST.md at C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md
- PROJECT.md at C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
- PAUSE_STATE.md at C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PAUSE_STATE.md
- Explorer 1 Analysis: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_explorer_m4_it1_1\analysis.md
- Explorer 2 Analysis: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_explorer_m4_it1_2\analysis.md
- Explorer 3 Analysis: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_explorer_m4_it1_3\analysis.md

Task Objectives:
1. **Icon Conversion**: Convert `owl_icon.jpg` to `owl_icon.ico` (multi-resolution 16x16, 32x32, 48x48, 64x64, 128x128, 256x256 via Pillow) and `owl_icon.png` in project root.
2. **Rebranding to "Owl"**:
   - `main.py`: Set application name to `"Owl"`, set window icon `app.setWindowIcon(QIcon("owl_icon.ico"))`.
   - `browser.py`: Set window title to `"Owl"`, set window icon `self.setWindowIcon(QIcon("owl_icon.ico"))`. Support `owl://settings` URL scheme. Maintain alias `PhantomBrowser = OwlBrowser` (or keep `PhantomBrowser` class name while setting title to `"Owl"`).
   - `title_bar.py`: Change default title label to `"🦉 Owl"`.
   - `profile_selector.py`: Change title to `"🦉 Owl"`, subtitle to `"Select a profile to launch your private ephemeral workspace"`.
   - `settings_view.py`: Change About titles to `"About Owl"` and `"Owl v2.0.0 (Stealth Build)"`. Fix `set_search_engine()` to sync subpages so all settings controls update properly.
   - `single_instance.py`: Update app key / socket naming to `"OwlBrowser_SingleInstance"` / `"OwlWorkspace_..."`.
3. **Build Spec**: Update `phantom_browser.spec` (and create `owl.spec`) to output `Owl.exe`, set `icon='owl_icon.ico'`, and include `owl_icon.jpg`, `owl_icon.ico`, and `owl_icon.png` in `datas`.
4. **Stealth Verification**: Ensure all stealth features (`SetWindowDisplayAffinity` in `display_affinity.py`, `Tool` window flag, `WindowStaysOnTopHint`, `Ctrl+Shift+B` hotkey in `hotkey.py`, single instance socket lock) remain fully active and functional.
5. **Test Suite Clearance**: Update test files (`tests/test_ui_and_tabs.py`, `tests/test_single_instance.py`, `tests/test_challenger_m1_2.py`, `tests/test_stealth.py`, `tests/test_e2e.py`, `tests/conftest.py`, etc.) to match `"Owl"`, `"🦉 Owl"`, `"OwlWorkspace_"`, `owl.spec`, and `Owl.exe`. Run the full pytest suite (`pytest tests/ -v`) and verify 100% pass rate (152/152 passed).

Document all modified files and test execution results in C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\teamwork_preview_worker_m4_it1\changes.md and handoff.md.
