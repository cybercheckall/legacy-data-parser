"""
test_m1_m4_features.py - Automated Unit & Integration Tests for Milestones M1, M2, M3, and M4.

Covers:
- M1: Guest Mode active profile default in root storage & ProfileManager.
- M2: Window Opacity Slider QSlider in TitleBar, range 10-100, opacity change handler, drag event guard.
- M3: Adjacent '+' new tab button positioning adjacent to last tab strip (last_rect.right() + 4).
- M4: Clean Google Search homepage (HOME_URL), hidden shortcuts bar (bookmarks_bar), standard URL bar.
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication, QSlider
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QMouseEvent

from owl.profiles.profile_manager import ProfileManager
from owl.shell.title_bar import TitleBar
from owl.shell.tab_bar import TabWidget
from owl.workspace.main_window import OwlBrowser, HOME_URL


class TestM1ToM4Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_m1_guest_mode_profile_selector_default(self):
        """M1: ProfileManager defaults active profile to Guest mode ('id=guest', 'name=Guest mode')."""
        pm = ProfileManager()
        active = pm.get_active_profile()
        self.assertEqual(active.id, "guest")
        self.assertEqual(active.name, "Guest mode")
        self.assertEqual(active.avatar, "👤")
        self.assertEqual(active.homepage, "https://www.google.com")
        self.assertEqual(active.search_engine, "Google")

    def test_m2_window_transparency_slider(self):
        """M2: TitleBar contains OpacitySlider (QSlider, range 10..100, default 100) and mousePress guard."""
        tb = TitleBar()
        self.assertTrue(hasattr(tb, "opacity_slider"))
        slider = tb.findChild(QSlider, "OpacitySlider")
        self.assertIsNotNone(slider, "TitleBar must contain QSlider with objectName OpacitySlider.")
        self.assertEqual(slider.minimum(), 10)
        self.assertEqual(slider.maximum(), 100)
        self.assertEqual(slider.value(), 100)
        self.assertEqual(slider.toolTip(), "Window Opacity (10% - 100%)")

        # Test slider value change handler
        tb._on_opacity_changed(75)

        # Test mousePressEvent guard on opacity slider
        slider.setGeometry(50, 5, 100, 20)
        press_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(60, 10),
            QPointF(60, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        tb.mousePressEvent(press_event)
        self.assertFalse(press_event.isAccepted(), "Mouse press over opacity slider must be ignored to prevent window drag.")
        tb.deleteLater()

    def test_m3_owl_style_adjacent_tab_button(self):
        """M3: '+' new tab button is parented to self/tabBar and positioned adjacent to active tab strip."""
        tab_widget = TabWidget()
        tab_widget.resize(800, 600)
        tab_widget.show()

        tab_widget.add_new_tab(url="https://www.google.com", label="Tab 1")
        tab_widget.add_new_tab(url="https://www.google.com", label="Tab 2")
        tab_widget._update_new_tab_btn_pos()

        count = tab_widget.count()
        self.assertEqual(count, 2)
        last_rect = tab_widget.tabBar().tabRect(count - 1)
        tb_x = tab_widget.tabBar().x()
        expected_x = tb_x + last_rect.right() + 4

        self.assertEqual(tab_widget.new_tab_btn.x(), expected_x)
        self.assertEqual(tab_widget.cornerWidget(Qt.Corner.TopRightCorner), tab_widget.new_tab_btn)

        tab_widget.deleteLater()

    def test_m4_clean_google_homepage_and_nav_bar(self):
        """M4: Default HOME_URL is Google search, bookmarks_bar is hidden, standard URL bar without AI buttons."""
        self.assertEqual(HOME_URL, "https://www.google.com")
        browser = OwlBrowser(show_profile_selector_on_start=False)
        self.assertTrue(hasattr(browser, "bookmarks_bar"))
        self.assertTrue(browser.bookmarks_bar.isHidden(), "Bookmarks shortcuts bar must be hidden per M4 clean homepage spec.")
        self.assertIsNotNone(browser.nav_bar)
        self.assertIsNotNone(browser.nav_bar.url_bar)
        self.assertIsNotNone(browser.ai_button, "Floating AI sparkle button must remain intact.")
        self.assertIsNotNone(browser.ai_panel, "AISidePanel must remain intact.")
        browser.close()
        browser.deleteLater()


if __name__ == "__main__":
    unittest.main()
