## 2026-08-05T08:57:35Z
You are Explorer 1 for Milestone 2 Iteration 3 in Phantom Workspace overhaul.
Your working directory is C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m2_it3_1.

REQUIRED INPUT FILES TO READ:
- C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md
- C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
- C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PAUSE_STATE.md
- Gate status: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\orchestrator\GATE_STATUS.md
- Reviewer 1 Report: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\reviewer_m2_it2_1\handoff.md
- Challenger 1 Report: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\challenger_m2_it2_1\handoff.md
- single_instance.py and tests/test_challenger_m1_2.py / tests/test_m1_stress_and_edge.py.

TASK:
Investigate single-instance IPC socket cleanup and race condition handling in single_instance.py:
1. Fix QLocalServer socket cleanup on Windows (QLocalServer.removeServer(app_key) before listen(), closing and deleting server instance on release()).
2. Fix corrupted socket payload handling so invalid/corrupted bytes on incoming connections fail gracefully without crashing or hanging the server (test_corrupted_payload_bytes_over_socket).
3. Fix concurrent acquisition race condition (test_concurrent_acquisition_race) and duplicate activation check.
4. Verify all tests in tests/test_challenger_m1_2.py, tests/test_m1_stress_and_edge.py, and tests/test_single_instance.py pass cleanly.

Write your exact technical remediation plan to C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m2_it3_1\handoff.md and report completion via message.
