# Dispatch to Worker M1 — Guest Mode Profile Selector

## Identity
- Role: Implementation Worker
- Working Directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m1
- Scope Document: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\PROJECT.md
- Original Request File: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\ORIGINAL_REQUEST.md

## Task Description
Implement Milestone M1: Default startup profile selector to show ONLY Guest mode initially.

### File Write Ownership
- `profile_manager.py`
- `browser.py`
- `tests/test_profiles.py` (if test assertions need updating for Guest mode default)

### Implementation Requirements
1. In `profile_manager.py`: Modify `_create_defaults()` so that the initial profile list contains ONLY one profile — "Guest mode":
   ```python
   guest_prof = Profile(
       id="guest",
       name="Guest mode",
       avatar="👤",
       homepage="https://www.google.com",
       search_engine="Google",
       theme_color="#533483",
   )
   self.profiles = [guest_prof]
   self.active_profile_id = guest_prof.id
   self.save_profiles()
   return self.profiles
   ```
2. In `browser.py`: Ensure that when `show_profile_selector_on_start` is True, `self.show_profile_selector()` is triggered on launch so the user sees the Guest mode profile selector.
3. Run `pytest` to execute all tests. If any profile unit test expects the old "Default Profile" or "Work Profile" names or count of 2 defaults, update those test assertions to match the new "Guest mode" default.
4. All tests must pass (100% pass rate).

### Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Output Requirements
Write your handoff report to `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\worker_m1\handoff.md` including build/test execution commands and results, and notify the orchestrator via send_message.
