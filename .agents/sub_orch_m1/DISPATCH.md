## 2026-08-05T01:06:42+05:30

<USER_REQUEST>
You are the Sub-Orchestrator for Milestone 1 (M1: Profile System & Single Instance) of Phantom Workspace overhaul.
Your working directory is C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\sub_orch_m1.
Read ORIGINAL_REQUEST.md at C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md.
Read PROJECT.md at C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md.

Task:
Execute Milestone 1 (M1: Profile System & Single Instance):
1. Create SCOPE.md in your working directory C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\sub_orch_m1\SCOPE.md defining M1 scope:
   - `profile_manager.py`: Profile data model (`id`, `name`, `avatar`, `homepage`, `search_engine`, `theme_color`), persistent `profiles.json` storage, CRUD operations, ephemeral OTR `QWebEngineProfile` generator (no cookies, history, or disk cache).
   - `single_instance.py`: `SingleInstanceGuard` using `QLocalServer`/`QLocalSocket` IPC to detect existing instance, send activation signal, bring window to foreground (`showNormal()`, `show()`, `raise_()`, `activateWindow()`), and terminate second instance with exit code 0.
2. Apply the Iteration Loop procedure (Assess -> Iteration Loop: Explorers -> Worker -> Reviewers -> Challengers -> Forensic Auditor -> Gate).
   - MUST pass path to ORIGINAL_REQUEST.md to all subagents.
   - MUST enforce zero tolerance for cheating/hardcoding test results.
3. Once M1 passes all gate criteria cleanly (build/tests pass, reviewers approve, challengers verify, auditor clean), update PROJECT.md milestone status for M1 to `DONE`.
4. Write handoff.md in your working directory and send a completion message to the Project Orchestrator.
</USER_REQUEST>
