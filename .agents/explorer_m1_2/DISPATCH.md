## 2026-08-05T01:07:43Z

You are Explorer 2 for Milestone 1 (M1: Profile System & Single Instance).
Working directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2

Input Files to Read:
1. ORIGINAL_REQUEST.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md
2. PROJECT.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
3. SCOPE.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\sub_orch_m1\SCOPE.md

Task:
Investigate the codebase at C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser.
Specifically:
- Check existing application entry point and Qt window structure.
- Detail exact specifications for `single_instance.py`:
  - `SingleInstanceGuard` using `QLocalServer`/`QLocalSocket` IPC.
  - Server socket name convention.
  - Protocol for detecting running instance and sending activation signal.
  - Window foreground activation methods (`showNormal()`, `show()`, `raise_()`, `activateWindow()`).
  - Graceful exit with code 0 for second instance.
  - Server cleanup / stale socket handling on Windows.
- Recommend implementation strategy for `single_instance.py`.

Write your detailed findings and implementation plan to C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2\handoff.md and report back when finished.
