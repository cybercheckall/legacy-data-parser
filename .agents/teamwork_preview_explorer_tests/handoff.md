# Test Suite Analysis Handoff Report

## Observation
- **Project Structure & Specifications**:
  - `ORIGINAL_REQUEST.md`: Lines 158-196 specify new requirements for Guest Mode startup profile selector (R1/M1), Title Bar transparency slider (R2/M2), Chrome-style adjacent '+' new tab button (R3/M3), clean Google search homepage with standard URL bar (no AI buttons/shortcuts) (R4/M4), and preservation of all 4 stealth features (R5/M5).
  - `PROJECT.md`: Lines 6-23 specify feature inventory across Milestones M1-M5 and interface contracts for `profile_manager`, `title_bar`, `tab_bar`, `nav_bar`, and stealth integration.
  - `pytest --collect-only`: Discovered **159 automated tests** across **20 test modules** in `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\tests`.

- **Existing Test Inventory Across Key Components**:
  - **Profile Manager** (30 tests):
    - `tests/test_profiles.py`: 10 tests (`test_tier1_default_profile_creation`, `test_tier1_profile_persistence`, `test_tier1_active_profile_switch`, `test_tier1_profile_crud_operations`, `test_tier1_otr_web_profile_creation`, `test_tier2_corrupt_json_fallback`, `test_tier2_delete_active_profile`, `test_tier2_delete_last_profile_prevention`, `test_tier2_invalid_search_engine_validation`, `test_tier2_special_char_profile_names`).
    - `tests/test_challenger_m1_2.py`: 5 tests (`test_search_engine_sanitization`, `test_corrupt_json_structure_fallback`, `test_prevent_last_profile_deletion`, `test_delete_active_profile_auto_switches_active`, `test_otr_profile_security_settings`).
    - `tests/test_m1_stress_and_edge.py`: 7 tests (`test_rapid_profile_crud_stress`, `test_json_file_corruption_matrix`, `test_path_traversal_and_adversarial_strings`, `test_concurrent_profile_manager_access`, `test_save_profiles_silent_disk_failure_handling`, `test_otr_profile_zero_disk_storage_guarantee`, `test_otr_profile_page_instantiation_no_disk_leak`).
    - `tests/test_ui_and_tabs.py`: 1 test (`test_tier1_profile_selector_card_ui`).
    - `tests/test_challenger_m2_1.py`: 3 tests (`test_empty_and_none_profiles_list`, `test_set_profiles_multiple_calls_widget_lifecycle`, `test_card_click_signal_emission`).
    - `tests/test_settings.py`: 1 test (`test_tier1_profile_management_view`).
    - `tests/test_challenger_m3_stress.py`: 2 tests (`test_profile_switch_search_engine_sync`, `test_rapid_profile_crud_while_settings_open`).
    - `tests/test_challenger_m4_stress.py`: 1 test (`test_profile_creation_switching_label_sync`).

  - **Title Bar** (7 tests):
    - `tests/test_ui_and_tabs.py`: 2 tests (`test_tier1_frameless_titlebar_controls`, `test_tier2_titlebar_double_click_maximize`).
    - `tests/test_challenger_m2_1.py`: 3 tests (`test_drag_offset_calculation`, `test_maximized_window_drag_immunity`, `test_double_click_toggle_maximize`).
    - `tests/test_challenger_m2_2.py`: 1 test (`test_window_drag_and_double_click_mechanics`).
    - `tests/test_challenger_m4_stress.py`: 1 test (`test_rebranding_window_titles_and_labels`).

  - **Tab Bar** (12 tests):
    - `tests/test_ui_and_tabs.py`: 5 tests (`test_tier1_chrome_style_tabbar_new_tab_button`, `test_tier1_last_tab_close_navigates_home`, `test_tier2_rapid_tab_creation_stress`, `test_tier2_tab_reordering_movable`, `test_tier2_tab_title_truncation`).
    - `tests/test_challenger_m2_1.py`: 3 tests (`test_rapid_tab_creation_and_deletion`, `test_close_tab_invalid_index`, `test_tab_title_truncation_and_whitespace`).
    - `tests/test_challenger_m2_2.py`: 2 tests (`test_corner_widget_placement_on_tabwidget`, `test_last_tab_close_behavior_and_fallback`).
    - `tests/test_challenger_m3_it2_deep_stress.py`: 2 tests (`test_close_settings_when_sole_remaining_tab`, `test_close_settings_in_multitab_environment`).

  - **Nav Bar** (12 tests):
    - `tests/test_ui_and_tabs.py`: 2 tests (`test_tier1_reload_only_navbar`, `test_tier2_url_bar_search_conversion`).
    - `tests/test_challenger_m2_1.py`: 5 tests (`test_url_input_parsing_domain`, `test_url_input_parsing_explicit_scheme`, `test_url_input_parsing_search_queries`, `test_url_input_parsing_empty_and_spaces`, `test_url_input_parsing_localhost_and_files`).
    - `tests/test_challenger_m2_2.py`: 1 test (`test_reload_only_toolbar_compliance`).
    - `tests/test_challenger_m3_stress.py`: 4 tests (`test_settings_url_routing_aliases`, `test_settings_tab_deduplication_stress`, `test_url_vs_search_query_parsing_matrix`, `test_search_query_url_generation_google_vs_duckduckgo`).

  - **Stealth Features** (17 tests):
    - *Display Affinity (`SetWindowDisplayAffinity`, `0x11`)* (9 tests): `test_stealth.py:test_tier1_display_affinity_exclusion`, `test_stealth.py:test_tier2_display_affinity_invalid_hwnd`, `test_stealth.py:test_tier2_wda_constant_hex_value`, `test_stealth.py:test_tier2_stealth_applied_property`, `test_stealth_affinity.py:test_tier1_set_stealth_affinity_win32_function`, `test_stealth_affinity.py:test_tier1_main_window_applies_affinity_on_creation`, `test_stealth_affinity.py:test_tier2_wda_constant_value`, `test_challenger_m4_stress.py:test_stealth_window_flags_and_affinity`, `test_e2e_scenarios.py:test_tier4_scenario_4_stealth_protection_under_offscreen`.
    - *Tool Window Flag (`Qt.WindowType.Tool`)* (3 tests): `test_stealth.py:test_tier1_tool_window_flag`, `test_stealth_affinity.py:test_tier2_window_flags_tool_window`, `test_challenger_m4_stress.py:test_stealth_window_flags_and_affinity`.
    - *Window Stays On Top (`Qt.WindowType.WindowStaysOnTopHint`)* (3 tests): `test_stealth.py:test_tier1_stays_on_top_flag`, `test_stealth_affinity.py:test_tier2_window_flags_stays_on_top`, `test_challenger_m4_stress.py:test_stealth_window_flags_and_affinity`.
    - *Global Hotkey (`Ctrl+Shift+B`)* (7 tests): `test_hotkey.py:test_tier3_global_hotkey_registration`, `test_hotkey.py:test_tier3_hotkey_visibility_toggle_states`, `test_hotkey.py:test_tier3_shortcut_combinations_interaction`, `test_stealth.py:test_tier1_global_hotkey_registered`, `test_stealth.py:test_tier2_hotkey_toggle_repeated`, `test_challenger_m4_stress.py:test_hotkey_listener_rapid_triggering`, `test_e2e_scenarios.py:test_tier3_hotkey_hide_preserves_ai_panel_state`.

- **Existing Test Assertions to Update**:
  - `test_ui_and_tabs.py:58-62` (`test_tier1_chrome_style_tabbar_new_tab_button`):
    `corner_widget = self.tab_widget.cornerWidget(Qt.Corner.TopRightCorner)`
    `self.assertEqual(corner_widget, self.tab_widget.new_tab_btn)`
  - `test_challenger_m2_2.py:27-36` (`test_corner_widget_placement_on_tabwidget`):
    `corner_widget = tabs.cornerWidget(Qt.Corner.TopRightCorner)`
    `assert corner_widget == tabs.new_tab_btn`
  *Reason*: Under M3, the '+' button is repositioned adjacent to the right of the active tab strip (`last_tab_rect.right() + 4`) rather than fixed as the `TopRightCorner` corner widget. These 2 assertions will fail once `new_tab_btn` is removed from `cornerWidget` and must be updated to test adjacent positioning instead.

- **PyTest Execution Verification**:
  - Run command: `pytest`
  - Output: `159 passed in 61.88s` (100% pass rate across all 20 test modules).

## Logic Chain
1. **Observation**: `ORIGINAL_REQUEST.md` (R1-R5) and `PROJECT.md` define 4 functional feature milestones (M1: Guest mode profile selector default, M2: Title Bar transparency slider, M3: Chrome-style adjacent tab bar, M4: Clean Google search homepage) and 1 verification milestone (M5: E2E & stealth regression).
2. **Logic Step 1 (M1 Assessment)**: `test_profiles.py:test_tier1_default_profile_creation` verifies `ProfileManager` default profile is single "Guest mode" (`id="guest"`). However, no test explicitly validates that the startup `ProfileSelector` UI widget initially renders *only* the Guest mode card on launch. A new test targeting `ProfileSelector` startup default card list is required.
3. **Logic Step 2 (M2 Assessment)**: No existing test module in `tests/` references `OpacitySlider`, `opacity_slider`, or window opacity changes via `TitleBar`. Therefore, 3 new tests are required: testing `TitleBar.opacity_slider` creation and range (10..100), window opacity response (`setWindowOpacity(val/100.0)`), and drag event suppression on the slider widget.
4. **Logic Step 3 (M3 Assessment)**: M3 moves `new_tab_btn` from `tab_widget.cornerWidget(TopRightCorner)` to dynamic adjacent positioning next to the last active tab. Existing assertions in `test_ui_and_tabs.py:62` and `test_challenger_m2_2.py:34` explicitly assert `cornerWidget == new_tab_btn`. Moving the button will break these 2 assertions. They must be updated, and a new test added to verify dynamic `new_tab_btn` geometry (`x()` adjacent to `tabBar().tabRect(last_idx).right()`).
5. **Logic Step 4 (M4 Assessment)**: Existing tests cover navigation and search query generation to Google/DDG, but do not assert `HOME_URL == "https://www.google.com"`, clean homepage without quick-link containers, or URL bar without AI Mode button. 3 new tests are required for M4.
6. **Logic Step 5 (Stealth Assessment)**: 17 existing automated tests cover all 4 stealth features (`WDA_EXCLUDEFROMCAPTURE`, `Qt.WindowType.Tool`, `Qt.WindowType.WindowStaysOnTopHint`, `Ctrl+Shift+B` hotkey). All 17 tests remain valid and require zero changes.

## Caveats
- The full test suite execution completed successfully with 159 passed in 61.88s (100% pass rate).
- No code in `tests/` or application source was modified during this read-only investigation.

## Conclusion
- The test suite comprises **159 automated tests** across **20 modules**.
- **Coverage for Stealth Features**: Excellent (17 existing tests across 4 modules).
- **Test Updates Required**:
  - `test_ui_and_tabs.py`: Update `test_tier1_chrome_style_tabbar_new_tab_button` to check adjacent positioning instead of `cornerWidget(TopRightCorner)`.
  - `test_challenger_m2_2.py`: Update `test_corner_widget_placement_on_tabwidget` to remove `cornerWidget` equality assertion.
- **New Tests Required for M1-M4**:
  - **M1**: Test `ProfileSelector` startup UI default showing only Guest mode card (`len(cards) == 1`).
  - **M2**: Test `TitleBar.opacity_slider` creation (range 10..100), `windowOpacity` update signal, and mouse drag event suppression on slider.
  - **M3**: Test dynamic adjacent placement of `new_tab_btn` next to active tab strip (`last_tab_rect.right() + 4`).
  - **M4**: Test `HOME_URL = "https://www.google.com"`, clean homepage layout (no quick-links bar), standard URL bar (no AI Mode button), and floating AI sparkle button preservation.

## Verification Method
- Run full test suite:
  `pytest`
- Collect test list without executing:
  `pytest --collect-only`
- Inspect modified/new test files:
  - `tests/test_ui_and_tabs.py`
  - `tests/test_challenger_m2_2.py`
  - New/updated test methods for M1-M4
- Invalidation conditions: Any test failure in the 159 test suite or failure of stealth flags (`WDA_EXCLUDEFROMCAPTURE`, `Tool`, `WindowStaysOnTopHint`, `Ctrl+Shift+B`).
