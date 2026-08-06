## 2026-08-05T01:32:26Z
You are Worker 3 for Milestone 1 (M1: Profile System & Single Instance Socket Isolation Remediation).
Working directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m1_3

Input Files to Read:
1. ORIGINAL_REQUEST.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md
2. PROJECT.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
3. SCOPE.md: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\sub_orch_m1\SCOPE.md
4. Challenger 2 Handoff: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\challenger_m1_2_2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Remediation Tasks:
1. Fix `single_instance.py` Inter-Test Socket Pollution:
   - When running `pytest tests/ -v` (full suite of 116 tests), lingering named pipes or socket handles across consecutive test classes cause `try_acquire()` to falsely connect to old servers or emit duplicate activation signals (`5 failed out of 116`).
   - In `try_acquire(app_key)`:
     - Validate empty/whitespace key -> raise `ValueError`.
     - When probing connection with `QLocalSocket`, ensure `socket.disconnectFromServer()`, `socket.close()`, and `socket.deleteLater()` are called on the socket before returning `False`.
     - Force call `QLocalServer.removeServer(server_name)` before calling `self._server.listen(server_name)`.
   - In `_on_new_connection()`:
     - Ensure incoming client socket is closed (`client.close()`, `client.deleteLater()`) after reading bytes and emitting `activation_requested` / `activated`.
   - In `release(app_key)`:
     - Ensure `self._server.close()`, `self._server.deleteLater()`, `self._server = None`, and `QLocalServer.removeServer(server_name)` cleanly clean up the server instance.

2. Test Verification:
   - Run `pytest tests/ -v` -> MUST PASS 100% (ALL 116 tests passed in ONE single test runner execution!).
   - Run `pytest tests/test_m1_stress_and_edge.py tests/test_challenger_m1_2.py -v` -> MUST PASS 100%.

Write your handoff report to `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m1_3\handoff.md` and report back when finished.
