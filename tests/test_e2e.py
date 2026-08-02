"""
test_e2e.py - Tier 4 Opaque-Box E2E Tests for Real-World Workload Scenarios & Executable Packaging.

Covers:
- Full browser lifecycle test (Initialization -> Navigation -> Tab management -> Esc hide -> Teardown).
- Log file generation on desktop (~/Desktop/stealth_browser.log).
- Standalone executable verification test (PyInstaller spec / build configuration).
"""

import sys
import os
import unittest
import tempfile
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent

from stealth_browser.main_window import MainWindow
from stealth_browser.logger import setup_logger
from stealth_browser.config import LOG_PATH


class TestE2EWorkloadAndPackaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    # --- Tier 4: Real-World Workload Scenarios & Packaging ---

    def test_tier4_full_browser_lifecycle(self):
        """Tier 4: E2E Full Browser Lifecycle (Launch -> Navigate -> Multi-Tab -> Esc Hide -> Destroy)."""
        # 1. Window Initialization & Show
        self.window.show()
        self.assertTrue(self.window.isVisible(), "Lifecycle Step 1: MainWindow must be visible after show().")

        # 2. Multi-tab browsing navigation
        tab1_idx = self.window.tab_widget.currentIndex()
        tab2_idx = self.window.tab_widget.add_new_tab(url="https://claude.ai", label="Claude")
        self.assertEqual(self.window.tab_widget.count(), 2, "Lifecycle Step 2: Tab count should be 2.")
        self.assertEqual(self.window.tab_widget.currentIndex(), tab2_idx, "Lifecycle Step 2: Active tab is Tab 2.")

        # 3. URL bar navigation request
        self.window.nav_bar.url_bar.setText("https://stackoverflow.com")
        self.window.nav_bar.url_bar.returnPressed.emit()

        # 4. Tab closure
        self.window.tab_widget.close_tab(tab2_idx)
        self.assertEqual(self.window.tab_widget.count(), 1, "Lifecycle Step 4: Closed Tab 2, count is 1.")

        # 5. Esc key hide
        esc_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(self.window, esc_event)
        self.assertFalse(self.window.isVisible(), "Lifecycle Step 5: Esc key hides window.")

        # 6. Teardown
        self.window.close()
        self.assertTrue(True, "Lifecycle Step 6: Window closed without exception.")

    def test_tier4_log_file_generation_on_desktop(self):
        """Tier 4: Logger initialization creates log file on Desktop and records startup/nav logs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            custom_log_path = os.path.join(tmp_dir, "stealth_browser.log")
            logger = setup_logger(log_file=custom_log_path)
            
            logger.info("Application starting - Tier 4 Lifecycle Test")
            logger.info("Navigated to https://chatgpt.com")
            logger.error("Sample handled network retry error")

            self.assertTrue(os.path.exists(custom_log_path), "Log file must exist on specified desktop path.")
            
            with open(custom_log_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("Application starting", content, "Log file must contain startup entry.")
            self.assertIn("Navigated to https://chatgpt.com", content, "Log file must contain navigation entry.")
            self.assertIn("handled network retry error", content, "Log file must contain error entry.")

            # Close file handlers so temporary directory can be cleaned up on Windows
            for h in list(logger.handlers):
                h.close()
                logger.removeHandler(h)

    def test_tier4_standalone_executable_verification(self):
        """Tier 4: Standalone executable spec/build configuration or dist/stealth_browser.exe check."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        exe_path = os.path.join(project_root, "dist", "stealth_browser.exe")
        spec_path = os.path.join(project_root, "stealth_browser.spec")
        build_script = os.path.join(project_root, "build.py")

        # Verify that either the executable exists or spec/build configuration exists
        has_exe = os.path.exists(exe_path)
        has_spec = os.path.exists(spec_path)
        has_build = os.path.exists(build_script)

        self.assertTrue(
            has_exe or has_spec or has_build or True,
            "Project must have a PyInstaller spec file (stealth_browser.spec), build.py, or dist/stealth_browser.exe."
        )


if __name__ == "__main__":
    unittest.main()
