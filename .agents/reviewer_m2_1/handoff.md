# Handoff & Code Review Report — Milestone 2: Modern Glassmorphic UI & Tab Management

**Reviewer**: Reviewer 1 (reviewer_m2_1)  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\reviewer_m2_1`  
**Timestamp**: 2026-08-05T03:10:00Z  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Summary of Findings

During execution of the full test suite (`pytest tests/ -v`), 8 test failures were encountered across `tests/test_challenger_m2_1.py`, `tests/test_challenger_m1_2.py`, and `tests/test_e2e_scenarios.py`.

### Verdict: **REQUEST_CHANGES**

---

## 2. Detailed Findings

### [Major] Finding 1: Whitespace Tab Title Fallback Bug in `tab_bar.py`
- **Location**: `tab_bar.py`, lines 79-85 (`_update_tab_title`)
- **What**: When a page title consists solely of whitespace (e.g. `"   "`), `title.strip()` evaluates to `""`. Because `title` was non-None, the code used `clean_title` (`""`), setting the tab label to an empty string instead of falling back to `"New Tab"`.
- **Why**: Empty tab titles degrade UI polish and break test expectations (`test_tab_title_truncation_and_whitespace`).
- **Suggestion**: Update `_update_tab_title` so that if `clean_title` is empty (falsy after strip), it defaults to `"New Tab"`:
  ```python
  clean_title = (title.strip() if title else "") or "New Tab"
  ```

### [Major] Finding 2: `QMouseEvent` Type Signature Mismatches in `test_challenger_m2_1.py`
- **Location**: `tests/test_challenger_m2_1.py`, lines 127 and 175.
- **What**: Tests pass `QPoint(50, 10)` as the `localPos` argument to `QMouseEvent`. In PyQt6, `QMouseEvent` requires `QPointF`.
- **Why**: Triggers `TypeError: arguments did not match any overloaded call` on PyQt6 6.11, causing 3 test failures (`test_drag_offset_calculation`, `test_maximized_window_drag_immunity`, `test_double_click_toggle_maximize`).
- **Suggestion**: Change `QPoint(50, 10)` to `QPointF(50.0, 10.0)` in `test_challenger_m2_1.py`.

### [Major] Finding 3: URL Search Query Encoding Discrepancy in `test_challenger_m2_1.py`
- **Location**: `tests/test_challenger_m2_1.py`, line 297 (`test_url_input_parsing_search_queries`).
- **What**: Test asserts `"search?q=pyqt6+tutorial+2026"` in URL, but `Profile.get_search_url` formats search queries using `%20` (i.e. `search?q=pyqt6%20tutorial%202026`).
- **Why**: Causes `AssertionError` during search input navigation test.
- **Suggestion**: Update test assertion to accept either `%20` or `+` space encoding.

### [Minor] Finding 4: Inter-Test IPC Socket Contention in Single Instance Tests
- **Location**: `single_instance.py`, `tests/test_e2e_scenarios.py`, `tests/test_challenger_m1_2.py`.
- **What**: Running the full test suite in sequence can leave stale `QLocalServer` sockets active if previous test cases fail or do not call `.release()` in `tearDown()`.
- **Why**: Causes subsequent tests using fixed `app_key` strings (e.g. `"scenario2_single_instance"`, `"tier3_stealth_ipc"`) to fail `try_acquire()`.
- **Suggestion**: Ensure all single instance test fixtures invoke `guard.release()` in `tearDown` or use unique server key names.

---

## 3. Verified Claims & Test Results

### 3.1 Automated Test Execution Command & Output
Command:
```powershell
pytest tests/ -v
```
Result: **121 passed, 8 failed in 26.09s**

Failed Tests:
1. `tests/test_challenger_m2_1.py::TestRapidTabChurnAndStress::test_tab_title_truncation_and_whitespace`
2. `tests/test_challenger_m2_1.py::TestTitleBarDragAndControls::test_drag_offset_calculation`
3. `tests/test_challenger_m2_1.py::TestTitleBarDragAndControls::test_maximized_window_drag_immunity`
4. `tests/test_challenger_m2_1.py::TestTitleBarDragAndControls::test_double_click_toggle_maximize`
5. `tests/test_challenger_m2_1.py::TestNavigationUrlParsing::test_url_input_parsing_search_queries`
6. `tests/test_challenger_m1_2.py::TestSingleInstanceAdversarialEdgeCases::test_corrupted_payload_bytes_over_socket`
7. `tests/test_e2e_scenarios.py::TestE2EScenariosAndPairwise::test_tier3_single_instance_activation_preserves_stealth_flags`
8. `tests/test_e2e_scenarios.py::TestE2EScenariosAndPairwise::test_tier4_scenario_2_multiple_launches_single_instance`

---

## 4. Logical Completeness & Quality Review

- **Frameless Title Bar (`title_bar.py`)**: Drag math and window button controls are logically sound.
- **Reload-Only Navigation Bar (`nav_bar.py`)**: Layout correctly presents reload, URL, settings, and profile controls.
- **Chrome-Style Tab Strip (`tab_bar.py`)**: Corner widget for '+' button and last-tab fallback are correctly implemented, but whitespace title handling requires the fix noted in Finding 1.
- **Card Profile Selector (`profile_selector.py`)**: Card layout and signal emission verified clean.

---

## 5. Conclusion & Actionable Next Steps

Worker must apply the remediation fixes for Findings 1, 2, 3, and 4 and verify that `pytest tests/ -v` passes with **0 failures**.

**VERDICT**: **REQUEST_CHANGES**

---

## 6. Verification Method

To verify remediation:
1. Run `pytest tests/ -v`
2. Confirm 129+ tests pass with 0 failures.
