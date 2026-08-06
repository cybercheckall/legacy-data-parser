"""
test_harness.py - Empirical test harness for Challenger M2 IT2.
Tests:
1. ProfileSelector layout recycling & widget lifecycle under rapid profile resets.
2. Tab title fallback logic under whitespace/empty/null strings.
3. Navigation input parsing for URL schemes, localhost, file://, and quote_plus search query encoding (+).
4. IPC socket cleanup and multi-thread single instance lock acquisition race condition.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import unittest
import threading
import time

from profile_selector import ProfileSelector
from profile_manager import Profile, ProfileManager
from browser import PhantomBrowser
from single_instance import SingleInstanceGuard
from tab_bar import TabWidget

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl

# Ensure QApplication exists for Qt tests
app = QApplication.instance() or QApplication(sys.argv)


class TestChallengerM2IT2Harness(unittest.TestCase):

    def test_1_profile_selector_layout_recycling(self):
        """Verify ProfileSelector.set_profiles does not duplicate layouts or leak card widgets."""
        selector = ProfileSelector()
        initial_layout_children = selector.layout().count()
        
        # Initial set with 2 profiles
        p1 = Profile(id="p1", name="Prof1")
        p2 = Profile(id="p2", name="Prof2")
        selector.set_profiles([p1, p2])
        self.assertEqual(len(selector.cards), 2)
        
        # Repeated set_profiles calls
        for i in range(20):
            profs = [Profile(id=f"p_{i}_{j}", name=f"Prof_{i}_{j}") for j in range(i % 5 + 1)]
            selector.set_profiles(profs)
            self.assertEqual(len(selector.cards), len(profs))
            # Layout count should stay constant (header, subtitle, cards_layout, stretch)
            self.assertEqual(selector.layout().count(), initial_layout_children)

    def test_2_tab_title_whitespace_fallback(self):
        """Verify tab title whitespace fallback to 'New Tab' across TabWidget and PhantomBrowser."""
        tw = TabWidget()
        view = tw.widget(0) if tw.count() > 0 else None
        idx = tw.add_new_tab(label="Initial")
        tab_view = tw.widget(idx)
        
        # Test whitespace and empty titles
        for whitespace_title in ["", "   ", " \t \n ", None]:
            tw._update_tab_title(tab_view, whitespace_title)
            title = tw.tabText(idx)
            self.assertEqual(title, "New Tab", f"Failed for title input: {repr(whitespace_title)}")

    def test_3_url_input_parsing(self):
        """Verify URL navigation parsing: schemes, localhost:8080, file://, and + search encoding."""
        browser = PhantomBrowser(show_profile_selector_on_start=False)
        
        # Mock _navigate to capture target URL
        navigated_urls = []
        browser._navigate = lambda url: navigated_urls.append(url)
        
        # Test direct schemes
        browser._navigate_from_input("file:///C:/Users/test/doc.txt")
        self.assertEqual(navigated_urls[-1], "file:///C:/Users/test/doc.txt")

        browser._navigate_from_input("http://localhost:8080")
        self.assertEqual(navigated_urls[-1], "http://localhost:8080")

        browser._navigate_from_input("localhost:3000/api/v1")
        self.assertEqual(navigated_urls[-1], "http://localhost:3000/api/v1")

        browser._navigate_from_input("127.0.0.1:8000")
        self.assertEqual(navigated_urls[-1], "http://127.0.0.1:8000")

        # Test search query with spaces -> should convert to +
        browser._navigate_from_input("python pyqt6 tutorial")
        self.assertIn("q=python+pyqt6+tutorial", navigated_urls[-1])

    def test_4_single_instance_concurrent_race(self):
        """Verify multi-threaded single instance lock acquisition race condition handling."""
        key = f"harness_race_test_{time.time()}"
        results = []
        lock = threading.Lock()

        def try_acquire_worker():
            guard = SingleInstanceGuard(app_key=key)
            res = guard.try_acquire(key)
            with lock:
                results.append((guard, res))
            time.sleep(0.05)
            guard.release()

        threads = [threading.Thread(target=try_acquire_worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = sum(1 for g, res in results if res is True)
        self.assertEqual(successes, 1, f"Expected 1 successful lock acquisition, got {successes}.")


if __name__ == "__main__":
    unittest.main()
