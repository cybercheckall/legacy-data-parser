# PAUSE STATE UI — Owl Stealth Browser Overhaul

**Paused At**: 2026-08-06T01:05:00Z (Local) / 2026-08-05T19:35:00Z (UTC)  
**Project Path**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`  
**Current Phase**: Phase 2 — Milestone Execution (M1 Guest Mode Profile Selector in progress)

---

## 1. Resume Instructions
To resume execution from this exact point:
1. Re-read `ORIGINAL_REQUEST.md` for full verbatim history of requirements.
2. Read `PROJECT.md` to restore architectural contracts and milestone breakdown (M1 through M5).
3. Check `.agents/orchestrator/progress.md` for current task status.
4. Spawn `teamwork_preview_orchestrator` and instruct it to resume Phase 2 Milestone Execution starting with Milestone M1 (`profile_manager.py` & `browser.py`).

---

## 2. Requirement Status & Feature Inventory

| Requirement | Description | Status | Target Module |
|---|---|---|---|
| **R1** | Profile Selector defaults to "Guest mode" only on app launch | `IN_PROGRESS` | `profile_manager.py`, `profile_selector.py`, `browser.py` |
| **R2** | Window Transparency Slider in TitleBar between title and controls | `PLANNED` | `title_bar.py`, `styles.py`, `browser.py` |
| **R3** | Chrome-style TabBar with '+' button adjacent to right of active tab | `PLANNED` | `tab_bar.py`, `styles.py` |
| **R4** | Clean Google search homepage (no shortcuts), standard URL bar without "AI Mode" button, keep floating AI sparkle button & side panel 100% intact | `PLANNED` | `nav_bar.py`, `browser.py`, `ai_panel.py` |
| **R5** | 100% stealth feature preservation (`WDA_EXCLUDEFROMCAPTURE`, `WS_EX_TOOLWINDOW`, `WindowStaysOnTopHint`, `Ctrl+Shift+B` hotkey) & pass 159 tests | `PLANNED` | `display_affinity.py`, `hotkey.py`, `tests/` |

---

## 3. Test Suite Baseline
- **Total Automated Tests**: 159
- **Passing Tests**: 159 (100% pass rate baseline prior to Phase 2 changes)
- **Test Command**: `pytest`

---

## 4. Pending Deliverables & Next Steps
- [ ] Complete Milestone M1: Update default profile in `profile_manager.py` to single Guest mode profile (`id="guest"`, `name="Guest mode"`, `avatar="👤"`, `homepage="https://www.google.com"`).
- [ ] Complete Milestone M2: Add `QSlider` (range 10..100) to `TitleBar` connected to `setWindowOpacity`.
- [ ] Complete Milestone M3: Position `new_tab_btn` dynamically adjacent to last tab rect in `TabWidget`.
- [ ] Complete Milestone M4: Set default `HOME_URL = "https://www.google.com"`, remove shortcuts bar, preserve floating AI button.
- [ ] Complete Milestone M5: Run full pytest suite (159 tests) and trigger mandatory Victory Audit.
