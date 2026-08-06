"""
tests/test_challenger_m2_2.py - Empirical Challenger 2 Test Suite for M2 Iteration 2.

Covers:
1. Corner widget placement on TabWidget (+ button top-right corner widget).
2. Reload-only toolbar compliance (no back/forward in layout, reload btn present, centered url bar).
3. Last-tab close behavior (last tab fallback to homepage, tab title set to Home, count preserved).
4. Dark glass QSS theme loading (style application on PhantomBrowser and sub-components).
5. Window drag and double-click toggle maximize mechanics in TitleBar.
"""

import pytest
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

from browser import PhantomBrowser
from title_bar import TitleBar
from nav_bar import NavBar
from tab_bar import TabWidget
from styles import DARK_GLASS_STYLE


class TestChallengerM2It2Suite:
    """Rigorously challenge M2 Iteration 2 components and contracts."""

    def test_corner_widget_placement_on_tabwidget(self, qtbot):
        """Verify '+' new tab button is correctly placed as top-right corner widget of TabWidget."""
        tabs = TabWidget(homepage_url="https://www.google.com")
        qtbot.addWidget(tabs)

        corner_widget = tabs.cornerWidget(Qt.Corner.TopRightCorner)
        assert corner_widget is not None
        assert corner_widget == tabs.new_tab_btn
        assert tabs.new_tab_btn.text() == "+"
        assert tabs.new_tab_btn.objectName() == "NewTabBtn"

        # Signal emission test
        signal_received = []
        tabs.new_tab_requested.connect(lambda: signal_received.append(True))
        qtbot.mouseClick(tabs.new_tab_btn, Qt.MouseButton.LeftButton)
        assert len(signal_received) == 1

        tabs.deleteLater()
        QApplication.processEvents()

    def test_reload_only_toolbar_compliance(self, qtbot):
        """Verify NavBar complies with reload-only requirement R1 (no back/fwd in layout, reload present)."""
        nav = NavBar()
        qtbot.addWidget(nav)
        nav.show()

        # Confirm reload button, url bar, settings button, profile button in layout
        assert nav.reload_btn.text() == "⟳"
        assert nav.reload_btn.isVisible()
        assert nav.url_bar.objectName() == "NavUrlBar"
        assert nav.settings_btn.text() == "⚙"
        assert nav.profile_btn.text() == "👤"

        # Back & Fwd buttons exist for API compatibility but MUST be hidden and NOT in layout
        assert nav.back_btn.isHidden()
        assert nav.fwd_btn.isHidden()

        # Check layout items: visible widgets count in layout
        layout = nav.layout()
        layout_widgets = [layout.itemAt(i).widget() for i in range(layout.count()) if layout.itemAt(i).widget()]
        assert nav.reload_btn in layout_widgets
        assert nav.url_bar in layout_widgets
        assert nav.settings_btn in layout_widgets
        assert nav.profile_btn in layout_widgets
        assert nav.back_btn not in layout_widgets
        assert nav.fwd_btn not in layout_widgets

        nav.deleteLater()
        QApplication.processEvents()

    def test_last_tab_close_behavior_and_fallback(self, qtbot):
        """Verify closing non-last tab removes tab, while closing last tab navigates home instead of closing tab/window."""
        tabs = TabWidget(homepage_url="https://www.duckduckgo.com")
        qtbot.addWidget(tabs)

        # Add 3 tabs
        tabs.add_new_tab(url="https://example.com/1", label="Tab 1")
        tabs.add_new_tab(url="https://example.com/2", label="Tab 2")
        tabs.add_new_tab(url="https://example.com/3", label="Tab 3")
        assert tabs.count() == 3

        # Close index 1 -> count becomes 2
        tabs.close_tab(1)
        assert tabs.count() == 2

        # Close index 0 -> count becomes 1
        tabs.close_tab(0)
        assert tabs.count() == 1

        # Close the last tab (index 0)
        tabs.close_tab(0)
        # Should NOT remove tab
        assert tabs.count() == 1
        assert tabs.tabText(0) == "Home"

        # Repeated close_tab calls on last tab remain count 1
        tabs.close_tab(0)
        assert tabs.count() == 1

        tabs.deleteLater()
        QApplication.processEvents()

    def test_dark_glass_qss_theme_loading(self, qtbot):
        """Verify dark glass QSS stylesheet is properly loaded and contains all key component selectors."""
        browser = PhantomBrowser(show_profile_selector_on_start=False)
        qtbot.addWidget(browser)

        style = browser.styleSheet()
        assert style == DARK_GLASS_STYLE
        assert "#0a0a1a" in style  # Dark bg color
        assert "#TitleBar" in style
        assert "#NavBar" in style
        assert "#NavUrlBar" in style
        assert "#NewTabBtn" in style
        assert "QTabWidget::pane" in style
        assert "QTabBar::tab" in style
        assert "#ProfileSelector" in style

        browser.close()
        browser.deleteLater()
        QApplication.processEvents()

    def test_window_drag_and_double_click_mechanics(self, qtbot):
        """Verify TitleBar mouse drag calculation and double-click maximize toggle."""
        browser = PhantomBrowser(show_profile_selector_on_start=False)
        qtbot.addWidget(browser)
        browser.show()

        title_bar = browser.title_bar
        initial_pos = browser.pos()

        # Simulate left mouse press on TitleBar
        press_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(50, 15),
            QPointF(initial_pos.x() + 50, initial_pos.y() + 15),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        title_bar.mousePressEvent(press_event)
        assert title_bar._drag_pos is not None

        # Simulate mouse move by (30, 20)
        move_event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(80, 35),
            QPointF(initial_pos.x() + 80, initial_pos.y() + 35),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        title_bar.mouseMoveEvent(move_event)
        assert browser.pos() == initial_pos + QPointF(30, 20).toPoint()

        # Release mouse
        release_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            QPointF(80, 35),
            QPointF(initial_pos.x() + 80, initial_pos.y() + 35),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        title_bar.mouseReleaseEvent(release_event)
        assert title_bar._drag_pos is None

        # Simulate double-click on title bar -> toggle maximize
        was_maximized = browser.isMaximized()
        dbl_click_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPointF(50, 15),
            QPointF(browser.pos().x() + 50, browser.pos().y() + 15),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        title_bar.mouseDoubleClickEvent(dbl_click_event)
        assert browser.isMaximized() != was_maximized
        assert title_bar.max_btn.text() == ("❐" if browser.isMaximized() else "□")

        # Double click again -> restore
        title_bar.mouseDoubleClickEvent(dbl_click_event)
        assert browser.isMaximized() == was_maximized
        assert title_bar.max_btn.text() == "□"

        # Verify drag is disabled when maximized
        browser.showMaximized()
        maximized_pos = browser.pos()
        press_max_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(50, 15),
            QPointF(maximized_pos.x() + 50, maximized_pos.y() + 15),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        title_bar.mousePressEvent(press_max_event)
        assert title_bar._drag_pos is None  # Should NOT initiate drag when maximized

        browser.close()
        browser.deleteLater()
        QApplication.processEvents()
