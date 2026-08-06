## 2026-08-05T03:32:10Z
<USER_REQUEST>
You are Worker 3 for Milestone 2 Iteration 3 in Phantom Workspace overhaul.
Your working directory is C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m2_3.

REQUIRED INPUT FILES TO READ BEFORE STARTING WORK:
- C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md
- C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
- C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PAUSE_STATE.md
- Explorer 1 It3 Handoff Report: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m2_it3_1\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

TASK SCOPE:
Apply single-instance IPC remediation changes to `single_instance.py`:
1. Add class-level `_lock = threading.RLock()` to `SingleInstanceGuard` and synchronize `try_acquire()`, `release()`, `release_all()`, `_on_new_connection()`.
2. Add `QLocalServer.removeServer(server_name)` unconditionally inside the lock BEFORE instantiating `QLocalServer` and calling `listen()`.
3. Add `QCoreApplication.processEvents()` after closing sockets or releasing locks to ensure Windows Named Pipe handles are released immediately in OS kernel.
4. Wrap socket payload reading and client teardown in `_on_new_connection()` in try-except blocks so corrupt bytes fail gracefully.
5. Run full test suite: `pytest tests/ -v` and verify 100% test pass rate across all project tests.

Write your implementation report to C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m2_3\handoff.md including exact test results and command outputs, and report completion via message.
</USER_REQUEST>
