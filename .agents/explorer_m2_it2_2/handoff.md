# Technical Remediation Plan & Handoff Report — Milestone 2 Iteration 2

**Agent**: Explorer 2 (`explorer_m2_it2_2`)  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m2_it2_2`  
**Timestamp**: 2026-08-05T03:15:00Z  
**Status**: COMPLETE (Read-Only Remediation Strategy)  

---

## 1. Observation

A detailed investigation was conducted across the codebase, gate status reports (`GATE_STATUS.md`), Reviewer 1 report (`reviewer_m2_1/handoff.md`), Challenger 1 report (`challenger_m2_1/handoff.md`), source modules (`profile_selector.py`, `tab_bar.py`, `browser.py`, `single_instance.py`), and test suites (`tests/test_challenger_m2_1.py`, `tests/test_ui_and_tabs.py`).

### Key Codebase Observations:

1. **`profile_selector.py` Layout Stacking & Widget Memory Leak**:
   - `ProfileSelector.__init__` calls `self._init_ui()`, creating `main_layout = QVBoxLayout(self)`.
   - `set_profiles(self, profiles)` clears `self.cards` and calls `self._init_ui()` again.
   - Calling `_init_ui()` repeatedly invokes `QVBoxLayout(self)` on an already-laid-out widget, triggering Qt warnings (`QLayout: Attempting to add QLayout "" to ProfileSelector "ProfileSelector", which already has a layout`), creating duplicate `title` and `subtitle` header labels, and leaking child widgets.

2. **`tab_bar.py` & `browser.py` Whitespace Tab Title Fallback**:
   - `TabWidget._update_tab_title()` does `clean_title = title.strip() if title else "New Tab"`.
   - For a whitespace title string `"   "`, `bool("   ")` evaluates to `True`, executing `title.strip()`, which evaluates to `""` (empty string).
   - This sets `self.setTabText(idx, "")`, producing empty/blank tab labels instead of falling back to `"New Tab"`.
   - `PhantomBrowser._update_tab_title()` in `browser.py` suffers from the same issue: `title[:25] + "..." if len(title) > 25 else (title or "New Tab")`.

3. **`browser.py` URL Input Parsing Limitations**:
   - `PhantomBrowser._navigate_from_input(text)` checks `if "." in cleaned and " " not in cleaned:`.
   - Localhost inputs like `localhost:8080` contain no dot (`.`), causing them to be misparsed as search engine queries (`https://www.google.com/search?q=localhost:8080`) instead of navigating to `http://localhost:8080`.
   - Inputs with non-HTTP schemes like `file:///C:/page.html` have `.` and no spaces, but `if not cleaned.startswith(("http://", "https://")):` prepends `https://`, resulting in `https://file:///C:/page.html`.

4. **`tests/test_challenger_m2_1.py` `QMouseEvent` Types & Test Assertion**:
   - Lines 127, 141, 157, 175 in `test_challenger_m2_1.py` pass `QPoint` objects to `QMouseEvent` constructors where `QPointF` is required by PyQt6, triggering `TypeError: arguments did not match any overloaded call` on certain PyQt6 environments.
   - Line 94 in `test_challenger_m2_1.py` currently asserts `self.assertEqual(self.tab_widget.tabText(0), "")` for whitespace title inputs because it mirrored the pre-remediation buggy behavior. Once `tab_bar.py` is fixed, this assertion must expect `"New Tab"`.

5. **`single_instance.py` & Inter-Test Socket Cleanup**:
   - Sequential execution of `pytest tests/ -v` can leave open `QLocalServer` instances if test fixtures fail to invoke `.release()` in `tearDown`, causing subsequent tests with fixed `app_key` strings to fail lock acquisition.

---

## 2. Logic Chain

1. **Observation 1** demonstrates that `ProfileSelector.set_profiles()` is not idempotent. Extracting card population into a dedicated helper method `_populate_cards()` and using `set_profiles()` to clean up existing card widgets from `cards_layout` without re-running `_init_ui()` resolves layout stacking, removes Qt warnings, and prevents widget memory leaks.
2. **Observation 2** proves that truthy evaluation of non-empty whitespace strings (`"   "`) bypasses the `else "New Tab"` fallback in `_update_tab_title()`. Changing the expression to `clean_title = (title.strip() if title else "") or "New Tab"` in both `tab_bar.py` and `browser.py` guarantees tab labels are never blank.
3. **Observation 3** proves that relying solely on `"." in cleaned` misclassifies `localhost:port` and `file://` schemes. Enhancing `_navigate_from_input` to explicitly handle scheme prefixes (`http://`, `https://`, `file://`, `about:`, `chrome://`) and local host patterns (`localhost`, `127.0.0.1`) ensures correct URL routing.
4. **Observation 4** proves that `test_challenger_m2_1.py` requires `QPointF` for `QMouseEvent` positions and must update line 94 to assert `"New Tab"`.
5. **Observation 5** proves that standardizing `g.release()` cleanup across single-instance test fixtures eliminates inter-test socket contention.

---

## 3. Caveats

- Tests are executed under offscreen QPA mode (`QT_QPA_PLATFORM=offscreen`).
- `QWebEngineView` tab title updates are asynchronous in live page loads; direct calls to `_update_tab_title()` in unit tests simulate the signal handler directly.

---

## 4. Conclusion & Technical Remediation Plan

The worker must apply the following exact code modifications:

### 4.1 `profile_selector.py` Modifications

Replace `ProfileSelector` class implementation with layout-reusing structure:

```python
class ProfileSelector(QWidget):
    """Card-based profile selector view/overlay widget."""

    profile_selected = pyqtSignal(object)  # Emits Profile object

    def __init__(self, profiles=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ProfileSelector")
        self.profiles = profiles or []
        self.cards = []  # List of clickable card buttons for test contract compatibility
        self.cards_layout = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Header Title
        title = QLabel("👻 Phantom Workspace", self)
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #f8fafc; background: transparent; margin-bottom: 4px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Select a profile to launch your stealth ephemeral workspace", self)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent; margin-bottom: 30px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Grid for profile cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(self.cards_layout)
        main_layout.addStretch()

        self._populate_cards()

    def _populate_cards(self):
        """Instantiate card buttons for active profiles and add to cards_layout."""
        for p in self.profiles:
            card_btn = self._create_profile_card(p)
            if self.cards_layout:
                self.cards_layout.addWidget(card_btn)
            self.cards.append(card_btn)

    def _create_profile_card(self, profile: Profile) -> QPushButton:
        """Create a styled card button representing a browser profile."""
        card_text = f"{profile.avatar}\n\n{profile.name}\n({profile.search_engine})"
        card_btn = QPushButton(card_text, self)
        card_btn.setProperty("class", "ProfileCard")
        card_btn.setFixedSize(200, 160)
        card_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        card_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(30, 41, 59, 0.80);
                color: #f8fafc;
                border: 2px solid rgba(255, 255, 255, 0.10);
                border-radius: 16px;
                padding: 16px;
                font-size: 15px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba(51, 65, 85, 0.95);
                border: 2px solid {profile.theme_color or '#6366f1'};
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: #6366f1;
            }}
            """
        )
        card_btn.clicked.connect(lambda _, prof=profile: self._on_card_clicked(prof))
        return card_btn

    def _on_card_clicked(self, profile: Profile):
        self.profile_selected.emit(profile)

    def set_profiles(self, profiles):
        """Update list of profiles and rebuild UI cards without re-creating layout."""
        self.profiles = profiles or []
        for card in self.cards:
            if self.cards_layout:
                self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        self._populate_cards()
```

---

### 4.2 `tab_bar.py` Modifications

Update `TabWidget._update_tab_title`:

```python
    def _update_tab_title(self, view: QWebEngineView, title: str):
        idx = self.indexOf(view)
        if idx >= 0:
            clean_title = (title.strip() if title else "") or "New Tab"
            display_title = clean_title[:25] + "..." if len(clean_title) > 25 else clean_title
            self.setTabText(idx, display_title)
```

---

### 4.3 `browser.py` Modifications

1. Update `PhantomBrowser._update_tab_title`:
```python
    def _update_tab_title(self, tab: QWidget, title: str):
        """Update tab title text with truncation."""
        idx = self.tab_widget.indexOf(tab)
        if idx >= 0:
            clean_title = (title.strip() if title else "") or "New Tab"
            display_title = clean_title[:25] + "..." if len(clean_title) > 25 else clean_title
            self.tab_widget.setTabText(idx, display_title)
```

2. Update `PhantomBrowser._navigate_from_input`:
```python
    def _navigate_from_input(self, text: str):
        """Parse input text as direct URL or search query using active profile's search engine."""
        cleaned = text.strip()
        if not cleaned:
            return

        # Handle explicit schemes and local host ports
        if cleaned.startswith(("http://", "https://", "file://", "about:", "chrome://")):
            url_str = cleaned
        elif (cleaned.startswith("localhost") or cleaned.startswith("127.0.0.1")) and " " not in cleaned:
            url_str = "http://" + cleaned
        elif "." in cleaned and " " not in cleaned:
            url_str = "https://" + cleaned
        else:
            if hasattr(self, "_active_profile") and hasattr(self._active_profile, "get_search_url"):
                url_str = self._active_profile.get_search_url(cleaned)
            else:
                import urllib.parse
                url_str = f"https://www.google.com/search?q={urllib.parse.quote(cleaned)}"

        self._navigate(url_str)
```

---

### 4.4 `tests/test_challenger_m2_1.py` Modifications

1. Update line 94 in `test_tab_title_truncation_and_whitespace`:
```python
        # Test whitespace title
        self.tab_widget._update_tab_title(view, "   ")
        self.assertEqual(self.tab_widget.tabText(0), "New Tab")
```

2. Standardize `QMouseEvent` parameters in `TestTitleBarDragAndControls`:
Ensure all `QMouseEvent` initializations pass `QPointF` for `localPos` and `globalPos`:
```python
        press_point = QPointF(150.0, 110.0)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(50.0, 10.0),
            press_point,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
```

---

## 5. Verification Method

To verify complete 100% remediation:

1. Execute full test suite:
   ```powershell
   pytest tests/ -v
   ```
   *Expected Output*: `129 passed` (or `141 passed`) with **0 failures**.

2. Execute M2 Challenger test suite:
   ```powershell
   pytest tests/test_challenger_m2_1.py -v
   ```
   *Expected Output*: `13 passed in ~1.5s` with **0 failures**.

3. Execute UI & Tabs test suite:
   ```powershell
   pytest tests/test_ui_and_tabs.py -v
   ```
   *Expected Output*: `10 passed` with **0 failures**.
