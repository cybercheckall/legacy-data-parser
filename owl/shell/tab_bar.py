"""
Owl tab bar & tab widget.

Tab strip is detachable for the window handler.
Each tab gets an explicit close icon on the RIGHT (always visible).
"""

from PyQt6.QtCore import pyqtSignal, Qt, QUrl, QSize
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabBar, QStackedWidget, QPushButton,
    QToolButton,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

from owl.design.icons import icon_close


class TabWidget(QWidget):
    """Owl tabs with detachable tab_strip for handler-row layout."""

    new_tab_requested = pyqtSignal()
    currentChanged = pyqtSignal(int)
    tabCloseRequested = pyqtSignal(int)

    def __init__(self, parent=None, homepage_url: str = "https://www.google.com"):
        super().__init__(parent)
        self.setObjectName("TabWidget")
        self._homepage_url = homepage_url

        self.tab_strip = QWidget(parent)
        self.tab_strip.setObjectName("TabStrip")
        self.tab_strip.setFixedHeight(32)

        strip_layout = QHBoxLayout(self.tab_strip)
        strip_layout.setContentsMargins(6, 0, 6, 0)
        strip_layout.setSpacing(6)

        self._tab_bar = QTabBar(self.tab_strip)
        self._tab_bar.setObjectName("OwlTabBar")
        self._tab_bar.setDrawBase(False)
        self._tab_bar.setExpanding(False)
        self._tab_bar.setMovable(True)
        # Native close buttons are unreliable on macOS styles — we install our own.
        self._tab_bar.setTabsClosable(False)
        self._tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        self._tab_bar.setUsesScrollButtons(True)
        strip_layout.addWidget(self._tab_bar, 0)

        self.new_tab_btn = QPushButton("+", self.tab_strip)
        self.new_tab_btn.setObjectName("NewTabBtn")
        self.new_tab_btn.setToolTip("New Tab")
        self.new_tab_btn.setFixedSize(28, 28)
        self.new_tab_btn.clicked.connect(self.new_tab_requested.emit)
        strip_layout.addWidget(self.new_tab_btn, 0)

        strip_layout.addStretch(1)

        self._stack = QStackedWidget(self)
        body = QVBoxLayout(self)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._stack)

        self._tab_bar.currentChanged.connect(self._on_tab_bar_changed)
        self._tab_bar.tabCloseRequested.connect(self.close_tab)
        self._tab_bar.tabCloseRequested.connect(self.tabCloseRequested.emit)
        self._tab_bar.tabMoved.connect(self._on_tab_moved)

    def tabBar(self):
        return self._tab_bar

    def isMovable(self) -> bool:
        return self._tab_bar.isMovable()

    def setMovable(self, movable: bool):
        self._tab_bar.setMovable(movable)

    def isTabsClosable(self) -> bool:
        return True

    def setTabsClosable(self, closable: bool):
        # Always closable via our custom buttons; keep API for tests.
        pass

    def cornerWidget(self, corner=Qt.Corner.TopRightCorner):
        return self.new_tab_btn

    def count(self) -> int:
        return self._stack.count()

    def currentIndex(self) -> int:
        return self._stack.currentIndex()

    def setCurrentIndex(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
            self._tab_bar.setCurrentIndex(index)

    def currentWidget(self):
        return self._stack.currentWidget()

    def widget(self, index: int):
        return self._stack.widget(index)

    def indexOf(self, widget) -> int:
        return self._stack.indexOf(widget)

    def tabText(self, index: int) -> str:
        return self._tab_bar.tabText(index)

    def setTabText(self, index: int, text: str):
        self._tab_bar.setTabText(index, text)

    def addTab(self, widget, label: str) -> int:
        idx = self._stack.addWidget(widget)
        self._tab_bar.addTab(label)
        self._install_close_button(idx)
        self.setCurrentIndex(idx)
        return idx

    def removeTab(self, index: int):
        w = self._stack.widget(index)
        self._stack.removeWidget(w)
        self._tab_bar.removeTab(index)
        if w is not None:
            w.setParent(None)

    def _make_close_button(self) -> QToolButton:
        btn = QToolButton(self._tab_bar)
        btn.setObjectName("TabCloseBtn")
        btn.setIcon(icon_close(11, "#5f6368"))
        btn.setIconSize(QSize(11, 11))
        btn.setFixedSize(18, 18)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setAutoRaise(True)
        btn.setToolTip("Close tab")
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.clicked.connect(lambda _checked=False, b=btn: self._on_close_clicked(b))
        return btn

    def _install_close_button(self, index: int):
        """Put a visible close icon on the RIGHT of the tab."""
        if index < 0 or index >= self._tab_bar.count():
            return
        # Clear any leftover native/side buttons
        for side in (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide):
            old = self._tab_bar.tabButton(index, side)
            if old is not None:
                self._tab_bar.setTabButton(index, side, None)
                old.deleteLater()

        btn = self._make_close_button()
        self._tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, btn)
        btn.show()

    def _on_close_clicked(self, btn: QToolButton):
        for i in range(self._tab_bar.count()):
            if self._tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is btn:
                self._tab_bar.tabCloseRequested.emit(i)
                return

    def _on_tab_bar_changed(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
        # Keep close icons present on every tab after selection changes
        for i in range(self._tab_bar.count()):
            right = self._tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            if right is None:
                self._install_close_button(i)
            else:
                right.show()
        self.currentChanged.emit(index)

    def _on_tab_moved(self, from_index: int, to_index: int):
        w = self._stack.widget(from_index)
        if w is None:
            return
        self._stack.removeWidget(w)
        self._stack.insertWidget(to_index, w)
        self._stack.setCurrentIndex(to_index)
        for i in range(self._tab_bar.count()):
            if self._tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is None:
                self._install_close_button(i)

    def get_homepage_url(self) -> str:
        return self._homepage_url

    def set_homepage_url(self, url: str):
        if url:
            self._homepage_url = url

    def add_new_tab(self, url: str = None, label: str = "New Tab", web_profile=None) -> int:
        view = QWebEngineView(self)
        if web_profile and hasattr(view, "setPage"):
            from PyQt6.QtWebEngineCore import QWebEnginePage
            page = QWebEnginePage(web_profile, view)
            view.setPage(page)

        view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        target_url = url if url else self._homepage_url
        view.load(QUrl(target_url))
        view.titleChanged.connect(lambda title, v=view: self._update_tab_title(v, title))

        return self.addTab(view, label)

    def close_tab(self, index: int):
        if self.count() > 1:
            w = self.widget(index)
            self.removeTab(index)
            if w:
                w.deleteLater()
            for i in range(self._tab_bar.count()):
                if self._tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide) is None:
                    self._install_close_button(i)
        else:
            w = self.widget(0)
            target = self.get_homepage_url()
            if isinstance(w, QWebEngineView):
                w.load(QUrl(target))
                self.setTabText(0, "Home")
                if self._tab_bar.tabButton(0, QTabBar.ButtonPosition.RightSide) is None:
                    self._install_close_button(0)
            else:
                self.removeTab(0)
                if w:
                    w.deleteLater()
                parent_win = self.window()
                if hasattr(parent_win, "add_new_tab") and callable(parent_win.add_new_tab):
                    parent_win.add_new_tab(target, "Home")
                else:
                    self.add_new_tab(target, "Home")

    def _update_tab_title(self, view: QWebEngineView, title: str):
        idx = self.indexOf(view)
        if idx >= 0:
            clean_title = title.strip() if (title and title.strip()) else "New Tab"
            display_title = clean_title[:22] + "…" if len(clean_title) > 22 else clean_title
            self.setTabText(idx, display_title)


TabBar = TabWidget
