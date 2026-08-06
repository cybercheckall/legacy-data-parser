# DISPATCH — test_writer_1

## 2026-08-05T01:08:03Z

## Task Objective
Implement comprehensive opaque-box E2E and unit test suites in `tests/` covering Tiers 1-4 for all features in Phantom Workspace:
1. Single-Instance Enforcement (`tests/test_single_instance.py`)
2. Profiles Manager & Schema (`tests/test_profiles.py`)
3. Modern Frameless UI & Tab Bar (`tests/test_ui_and_tabs.py`)
4. AI Side Panel (`tests/test_ai_side_panel.py`)
5. Settings Page & Search Engine (`tests/test_settings.py`)
6. Stealth Features Preservation (`tests/test_stealth.py`)
7. Tier 3 Pairwise & Tier 4 Real-World Application Scenarios (`tests/test_e2e_scenarios.py`)

## Documents to Read
- ORIGINAL_REQUEST.md: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md`
- PROJECT.md: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md`
- TEST_INFRA.md: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\TEST_INFRA.md`
- Existing tests: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\tests`

## Requirements
- All tests must pass with `QT_QPA_PLATFORM=offscreen` using pytest (`python -m pytest tests/ -v`).
- Meet or exceed coverage thresholds: Tier 1 (≥5 per feature), Tier 2 (≥5 boundary/corner per feature), Tier 3 (pairwise combinations), Tier 4 (≥5 application scenarios).
- Deliver handoff report to `.agents/test_writer_1/handoff.md`.
