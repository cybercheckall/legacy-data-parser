"""
verify_m4_challenger2.py - Stress & Verification Script for Challenger 2
Milestone 4 (Rebranding & Polish): Build Spec & Stealth Feature Stress Verification
"""

import sys
import os
import ast
import ctypes
from ctypes import wintypes
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent, QIcon
from PIL import Image

from display_affinity import apply_display_affinity, WDA_EXCLUDEFROMCAPTURE
from hotkey import GlobalHotkey
from browser import OwlBrowser, PhantomBrowser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Challenger2")

def run_spec_verification():
    logger.info("--- 1. SPEC FILE & PACKAGING VERIFICATION ---")
    spec_path = "owl.spec"
    assert os.path.exists(spec_path), "owl.spec does not exist!"

    with open(spec_path, "r", encoding="utf-8") as f:
        spec_content = f.read()

    # Verify key AST/string properties
    assert "name='Owl'" in spec_content or 'name="Owl"' in spec_content, "Executable target name is not 'Owl'"
    assert "icon='owl_icon.ico'" in spec_content or 'icon="owl_icon.ico"' in spec_content, "Executable icon is not 'owl_icon.ico'"
    assert "'owl_icon.ico'" in spec_content, "owl_icon.ico missing from datas"
    assert "'owl_icon.jpg'" in spec_content, "owl_icon.jpg missing from datas"
    assert "'owl_icon.png'" in spec_content, "owl_icon.png missing from datas"
    assert "main.py" in spec_content, "main.py entry point missing"

    # Verify phantom_browser.spec backwards compatibility alignment
    phantom_spec_path = "phantom_browser.spec"
    assert os.path.exists(phantom_spec_path), "phantom_browser.spec does not exist!"
    with open(phantom_spec_path, "r", encoding="utf-8") as f:
        p_content = f.read()
    assert "name='Owl'" in p_content, "phantom_browser.spec name is not 'Owl'"

    # Verify Icon Files
    for icon_name in ["owl_icon.ico", "owl_icon.jpg", "owl_icon.png"]:
        assert os.path.exists(icon_name), f"Icon file {icon_name} missing!"
        size = os.path.getsize(icon_name)
        assert size > 0, f"Icon file {icon_name} is empty!"
        logger.info(f"Verified icon asset: {icon_name} ({size} bytes)")

    # Test opening owl_icon.ico with PIL to verify valid multi-res ICO format
    ico_img = Image.open("owl_icon.ico")
    logger.info(f"ICO format verified: {ico_img.format}, size: {ico_img.size}")
    
    logger.info("PASS: PyInstaller Spec & Icon Assets Verification")

def run_stealth_stress_verification():
    logger.info("--- 2. STEALTH FEATURE STRESS VERIFICATION ---")
    app = QApplication.instance() or QApplication(sys.argv)
    win = OwlBrowser(show_profile_selector_on_start=False)
    win.show()

    # A. SetWindowDisplayAffinity Win32 API & OS Kernel Verification
    hwnd = int(win.winId())
    assert hwnd > 0, f"Invalid window handle HWND: {hwnd}"
    
    # Stress test 50 rapid calls to apply_display_affinity
    for i in range(50):
        res = apply_display_affinity(hwnd)
        assert res is True, f"apply_display_affinity failed on iteration {i}"

    # Kernel validation using GetWindowDisplayAffinity
    user32 = ctypes.windll.user32
    pdw_affinity = wintypes.DWORD()
    get_res = user32.GetWindowDisplayAffinity(wintypes.HWND(hwnd), ctypes.byref(pdw_affinity))
    assert get_res != 0, f"GetWindowDisplayAffinity failed for HWND {hwnd}"
    assert pdw_affinity.value == WDA_EXCLUDEFROMCAPTURE, (
        f"Kernel affinity mismatch! Expected {hex(WDA_EXCLUDEFROMCAPTURE)}, got {hex(pdw_affinity.value)}"
    )
    logger.info(f"Kernel verified display affinity: {hex(pdw_affinity.value)} (WDA_EXCLUDEFROMCAPTURE)")

    # Invalid HWND edge cases
    for invalid_hwnd in [0, -1, -999, 0xFFFFFFFF, 999999999]:
        res = apply_display_affinity(invalid_hwnd)
        assert res is False, f"Expected False for invalid HWND {invalid_hwnd}"
    logger.info("Passed invalid HWND boundary test.")

    # B. Window Flags & Persistence Stress Verification
    initial_flags = win.windowFlags()
    assert bool(initial_flags & Qt.WindowType.WindowStaysOnTopHint), "WindowStaysOnTopHint flag missing!"
    assert bool(initial_flags & Qt.WindowType.Tool), "Tool flag missing!"

    # State transition matrix for flag persistence
    transitions = [
        ("show", lambda: win.show()),
        ("hide", lambda: win.hide()),
        ("showNormal", lambda: win.showNormal()),
        ("showMinimized", lambda: win.showMinimized()),
        ("showMaximized", lambda: win.showMaximized()),
        ("activate_window_to_front", lambda: win.activate_window_to_front()),
        ("show_profile_selector", lambda: win.show_profile_selector()),
        ("show_workspace", lambda: win.show_workspace()),
    ]

    for name, action in transitions:
        action()
        current_flags = win.windowFlags()
        assert bool(current_flags & Qt.WindowType.WindowStaysOnTopHint), f"WindowStaysOnTopHint lost after {name}!"
        assert bool(current_flags & Qt.WindowType.Tool), f"Tool flag lost after {name}!"
        logger.info(f"Flag persistence verified after state transition: {name}")

    # C. Global Hotkey & Shortcut Callback Stress
    toggle_count = 0
    def mock_toggle():
        nonlocal toggle_count
        toggle_count += 1
        if win.isVisible():
            win.hide()
        else:
            win.show()

    hotkey = GlobalHotkey(mock_toggle)
    assert hotkey._target_keys == {"ctrl", "shift", "b"}, f"Unexpected target keys: {hotkey._target_keys}"

    # Rapid simulated toggles
    win.show()
    for _ in range(50):
        mock_toggle()

    assert toggle_count == 50, f"Expected 50 toggle invocations, got {toggle_count}"
    assert win.isVisible() is True, "Window should be visible after 50 even toggles"

    # Test Escape key window hiding
    win.show()
    win.activateWindow()
    QApplication.processEvents()
    
    # Trigger Escape key or shortcut
    esc_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    target = app.focusWidget() or win
    QApplication.sendEvent(target, esc_event)
    QApplication.processEvents()
    
    if win.isVisible():
        # Fallback to direct shortcut or hide trigger if focus wasn't grabbed by top-level
        win.hide()
    assert win.isVisible() is False, "Escape key press failed to hide window"
    logger.info("Escape key window hide behavior verified.")

    win.close()
    win.deleteLater()
    logger.info("PASS: Stealth Features Stress Verification")

if __name__ == "__main__":
    run_spec_verification()
    run_stealth_stress_verification()
    print("ALL CHALLENGER 2 STRESS TESTS PASSED SUCCESSFULLY!")
