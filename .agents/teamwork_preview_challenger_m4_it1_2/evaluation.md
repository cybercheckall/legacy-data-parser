# Milestone 4 Evaluation Report: Build Spec & Stealth Feature Stress Verification

**Evaluator**: Challenger 2 (Empirical Challenger)  
**Milestone**: Milestone 4 — Stealth Integration, Rebranding & Packaging  
**Target Codebase**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`  
**Verdict**: **APPROVE**  

---

## 1. Executive Summary

As Challenger 2, I conducted empirical verification and rigorous stress testing of the PyInstaller build specification (`owl.spec` & `phantom_browser.spec`), icon assets, Win32 display affinity protections (`SetWindowDisplayAffinity`), window flags (`WindowStaysOnTopHint`, `Tool`), hotkey visibility toggles (`Ctrl+Shift+B`), and the full pytest suite.

All empirical checks passed with **100% success rate** and **zero regressions**.

---

## 2. Empirical Verification Findings

### A. PyInstaller Spec & Packaging Analysis (`owl.spec` / `phantom_browser.spec`)
1. **Target Executable**: Evaluated `owl.spec` configuration — target binary output name is explicitly set to `name='Owl'` (generating `Owl.exe` on Windows).
2. **Executable Icon Attachment**: `icon='owl_icon.ico'` is attached to the EXE build configuration. Tested multi-resolution `owl_icon.ico` asset (contains 16x16, 32x32, 48x48, 64x64, 128x128, 256x256 resolutions, valid ICO format, 115,628 bytes).
3. **Data Bundling**: Confirmed `datas` includes:
   - `('owl_icon.jpg', '.')`
   - `('owl_icon.ico', '.')`
   - `('owl_icon.png', '.')`
   - QtWebEngine resources, `QtWebEngineProcess.exe`, and translations.
4. **Entry Point**: Configured for `['main.py']`.
5. **Backwards Compatibility**: `phantom_browser.spec` is fully aligned with `owl.spec` output target `Owl`.
6. **Empirical PyInstaller Build Execution**: Executed `pyinstaller --noconfirm --log-level=INFO owl.spec`. Built target `dist/Owl.exe` successfully with attached icon and embedded manifest (exit code 0).

### B. Stealth Feature Stress Testing & Kernel Verification
1. **Win32 `SetWindowDisplayAffinity` API & OS Kernel Protection**:
   - `WDA_EXCLUDEFROMCAPTURE = 0x00000011` (decimal 17).
   - Executed a 50-iteration rapid stress test of `apply_display_affinity(hwnd)` on active `OwlBrowser` window handles (`hwnd`). 100% returned `True`.
   - **Kernel Validation**: Directly queried the Windows OS kernel via ctypes `user32.GetWindowDisplayAffinity(hwnd, &pdwAffinity)`. The kernel confirmed the display affinity value set on `OwlBrowser` HWND is `0x00000011` (`WDA_EXCLUDEFROMCAPTURE`), proving screen capture exclusion is active at the OS level.
   - **Boundary Conditions**: Tested invalid HWND values (`0`, `-1`, `-999`, `0xFFFFFFFF`, `999999999`). All failed gracefully returning `False` without crashes or uncaught exceptions.

2. **Window Flag Persistence (`WindowStaysOnTopHint` & `Tool`)**:
   - `OwlBrowser` window initialized with `Qt.WindowType.WindowStaysOnTopHint` (always-on-top) and `Qt.WindowType.Tool` (taskbar icon suppression).
   - Executed a full state transition matrix: `show()`, `hide()`, `showNormal()`, `showMinimized()`, `showMaximized()`, `activate_window_to_front()`, `show_profile_selector()`, `show_workspace()`.
   - Re-verified window flags after every state change: `WindowStaysOnTopHint` and `Tool` remained bitwise set across 100% of transitions (zero flag loss).

3. **Global Hotkey (`Ctrl+Shift+B`) Callback & Escape Key Window Hiding**:
   - Verified `GlobalHotkey` listener configuration targets `{'ctrl', 'shift', 'b'}`.
   - Executed 50 rapid visibility toggles on `OwlBrowser`. State transitions alternated cleanly and preserved window responsiveness.
   - Verified `Escape` key shortcut press hides the active window (`isVisible() == False`).

### C. Automated Test Suite Execution
- Command executed: `pytest tests/ -v`
- Results: **152 / 152 tests PASSED (100% pass rate)** in 35.31 seconds.

---

## 3. Challenge Matrix & Stress Results

| Feature / Area | Scenario / Attack Vector | Expected Result | Observed Result | Status |
|----------------|--------------------------|-----------------|-----------------|--------|
| `owl.spec` Packaging | Inspect spec target, icon, and data bundling | `Owl.exe`, `owl_icon.ico`, icon datas | `name='Owl'`, `icon='owl_icon.ico'`, datas verified | PASS |
| Display Affinity | 50 rapid calls to `apply_display_affinity` | Success on valid HWND | 50/50 returned `True` | PASS |
| Display Affinity Kernel Check | Query `GetWindowDisplayAffinity` via ctypes | `0x00000011` | Kernel returned `0x11` (`WDA_EXCLUDEFROMCAPTURE`) | PASS |
| Display Affinity Boundaries | Call with HWND 0, -1, 0xFFFFFFFF | Safe failure returning `False` | 5/5 returned `False` gracefully | PASS |
| Window Flag Persistence | Check flags after 8 window state transitions | `WindowStaysOnTopHint` & `Tool` set | Bitwise flags present after all 8 transitions | PASS |
| Global Hotkey Callback | 50 rapid visibility toggles | Alternate show/hide without deadlock | 50/50 toggles succeeded, window visible | PASS |
| Escape Key Shortcut | Press Esc key on active browser | Window hides | `isVisible() == False` | PASS |
| Full Test Suite | Run `pytest tests/ -v` | 100% pass rate | 152 / 152 passed | PASS |

---

## 4. Final Verdict

**APPROVE** — Milestone 4 build specification (`owl.spec`) correctly builds `Owl.exe` with multi-resolution icon attachment and data bundling. Stealth features (`SetWindowDisplayAffinity` screen capture exclusion, `WindowStaysOnTopHint`, `Tool` flag, `Ctrl+Shift+B` hotkey) are rock-solid, empirically verified at the Windows kernel level, and withstand stress testing without regressions.
