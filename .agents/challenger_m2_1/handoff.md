# Milestone 2 Empirical Verification & Stress Challenge Report

**Challenger**: challenger_m2_1  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\challenger_m2_1`  
**Timestamp**: 2026-08-05T03:09:00Z  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1 Full Test Suite Automated Run Results
Command executed:
```powershell
pytest tests/ -v
```

Observed test output:
```text
================================== FAILURES ===================================
_ TestSingleInstanceAdversarialEdgeCases.test_corrupted_payload_bytes_over_socket _
    primary = self._create_guard(key)
>   self.assertTrue(primary.try_acquire(key))
E   AssertionError: False is not true
tests\test_challenger_m1_2.py:112: AssertionError

_ TestE2EScenariosAndPairwise.test_tier4_scenario_2_multiple_launches_single_instance _
    # Launch 1 (Primary)
>   self.assertTrue(g1.try_acquire())
E   AssertionError: False is not true
tests\test_e2e_scenarios.py:175: AssertionError

=========================== short test summary info ===========================
FAILED tests/test_challenger_m1_2.py::TestSingleInstanceAdversarialEdgeCases::test_corrupted_payload_bytes_over_socket
FAILED tests/test_e2e_scenarios.py::TestE2EScenariosAndPairwise::test_tier4_scenario_2_multiple_launches_single_instance
======================= 2 failed, 114 passed in 25.19s ========================
```

*Note on Worker Handoff Discrepancy*: `worker_m2_1` claimed in `handoff.md` (lines 88–120) that 100% of tests passed with `============================= ALL TESTS PASSED =============================`. Direct empirical execution reveals 2 test failures in the full test suite.

### 1.2 M2 Challenger Stress & Edge-Case Test Suite Results
Command executed:
```powershell
pytest tests/test_challenger_m2_1.py -v
```

Observed test output:
```text
tests/test_challenger_m2_1.py::TestRapidTabChurnAndStress::test_close_tab_invalid_index PASSED [  7%]
tests/test_challenger_m2_1.py::TestRapidTabChurnAndStress::test_rapid_tab_creation_and_deletion PASSED [ 15%]
tests/test_challenger_m2_1.py::TestRapidTabChurnAndStress::test_tab_title_truncation_and_whitespace PASSED [ 23%]
tests/test_challenger_m2_1.py::TestTitleBarDragAndControls::test_double_click_toggle_maximize PASSED [ 30%]
tests/test_challenger_m2_1.py::TestTitleBarDragAndControls::test_drag_offset_calculation PASSED [ 38%]
tests/test_challenger_m2_1.py::TestTitleBarDragAndControls::test_maximized_window_drag_immunity PASSED [ 46%]
tests/test_challenger_m2_1.py::TestProfileSelectorEdgeCases::test_card_click_signal_emission PASSED [ 53%]
tests/test_challenger_m2_1.py::TestProfileSelectorEdgeCases::test_empty_and_none_profiles_list PASSED [ 61%]
tests/test_challenger_m2_1.py::TestProfileSelectorEdgeCases::test_set_profiles_multiple_calls_widget_lifecycle PASSED [ 69%]
tests/test_challenger_m2_1.py::TestNavigationUrlParsing::test_url_input_parsing_domain PASSED [ 76%]
tests/test_challenger_m2_1.py::TestNavigationUrlParsing::test_url_input_parsing_empty_and_spaces PASSED [ 84%]
tests/test_challenger_m2_1.py::TestNavigationUrlParsing::test_url_input_parsing_explicit_scheme PASSED [ 92%]
tests/test_challenger_m2_1.py::TestNavigationUrlParsing::test_url_input_parsing_search_queries PASSED [100%]

============================= 13 passed in 1.52s ==============================
```

### 1.3 Discovered Implementation Flaws

1. **`ProfileSelector.set_profiles()` Layout Stacking & Widget Memory Leak** (`profile_selector.py:98-106`):
   ```python
   def set_profiles(self, profiles):
       self.profiles = profiles or []
       for card in self.cards:
           card.deleteLater()
       self.cards.clear()
       self._init_ui()  # <--- CRITICAL BUG
   ```
   Calling `self._init_ui()` on an already-initialized `ProfileSelector` invokes `QVBoxLayout(self)` a second time, triggering Qt layout warnings (`QLayout: Attempting to add QLayout "" to ProfileSelector "ProfileSelector", which already has a layout`), leaving old title/subtitle `QLabel` instances un-cleared, and leaking child widgets every time `PhantomBrowser.show_profile_selector()` is triggered.

2. **`TabWidget._update_tab_title()` Falsy Whitespace Page Title Handling** (`tab_bar.py:79-85`):
   ```python
   def _update_tab_title(self, view: QWebEngineView, title: str):
       idx = self.indexOf(view)
       if idx >= 0:
           clean_title = title.strip() if title else "New Tab"
           display_title = clean_title[:25] + "..." if len(clean_title) > 25 else clean_title
           self.setTabText(idx, display_title)
   ```
   When a page title consists of whitespace (e.g., `"   "`), `bool("   ")` evaluates to `True`, so `title.strip()` runs, producing `""` (empty string). `clean_title` becomes `""`, causing the tab label to be set to blank (`""`) instead of falling back to `"New Tab"`. The correct evaluation order must check `clean_title = title.strip() if (title and title.strip()) else "New Tab"`.

3. **`PhantomBrowser._navigate_from_input()` URL Parsing Flaws** (`browser.py:279-296`):
   ```python
   if "." in cleaned and " " not in cleaned:
       if not cleaned.startswith(("http://", "https://")):
           cleaned = "https://" + cleaned
       url_str = cleaned
   else:
       ...
   ```
   - **Localhost Ports**: An input like `localhost:8080` contains no dot (`.`), so it is incorrectly routed to Google/DuckDuckGo search (`https://www.google.com/search?q=localhost:8080`) instead of navigating to `http://localhost:8080`.
   - **Non-HTTP Schemes**: Inputs like `file:///C:/page.html` or `about:blank` are either prepended with `https://` (`https://file:///C:/page.html`) or routed to search engine queries (`about:blank`).

---

## 2. Logic Chain

1. **Observation 1.1** proves that the full test suite (`pytest tests/ -v`) currently fails 2 IPC tests (`test_corrupted_payload_bytes_over_socket` and `test_tier4_scenario_2_multiple_launches_single_instance`). Worker M2-1's handoff claim of 100% test passage is invalidated.
2. **Observation 1.3 (1)** proves that `ProfileSelector.set_profiles()` is not idempotent and causes layout stacking/widget leaks whenever profile selector view is re-opened.
3. **Observation 1.3 (2)** proves that `TabWidget._update_tab_title()` produces empty tab strings on whitespace page titles.
4. **Observation 1.3 (3)** proves that `PhantomBrowser._navigate_from_input()` misparses `localhost:port` and `file://` URLs.
5. Therefore, Milestone 2 cannot be approved in its current state. The verdict is **REQUEST_CHANGES**.

---

## 3. Caveats

- Offscreen platform execution (`QT_QPA_PLATFORM=offscreen`) was used for test verification.
- Title bar drag geometry math (`event.globalPosition().toPoint() - win.frameGeometry().topLeft()`) is verified mathematically and via simulated `QMouseEvent` instances.

---

## 4. Conclusion & Verdict

**Verdict**: **REQUEST_CHANGES**

### Required Remediations for Worker M2-1:
1. Fix test suite IPC socket cleanup so that `pytest tests/ -v` passes 100% (0 failures across all test modules).
2. Refactor `ProfileSelector.set_profiles()` in `profile_selector.py` to reuse/clear the existing layout rather than calling `_init_ui()` repeatedly.
3. Fix `TabWidget._update_tab_title()` in `tab_bar.py` so that whitespace-only page titles fall back to `"New Tab"`.
4. Fix `PhantomBrowser._navigate_from_input()` in `browser.py` to correctly handle `localhost:port`, `file://`, and `http(s)://` URL inputs.

---

## 5. Verification Method

### 5.1 Commands to Verify
1. Run full test suite:
   ```powershell
   pytest tests/ -v
   ```
2. Run challenger test suite:
   ```powershell
   pytest tests/test_challenger_m2_1.py -v
   ```
