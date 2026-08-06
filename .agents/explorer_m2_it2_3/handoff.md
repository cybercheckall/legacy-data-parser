# Handoff Report — Technical Remediation Plan for Milestone 2 Iteration 2

**Agent**: Explorer 3 (`explorer_m2_it2_3`)  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m2_it2_3`  
**Timestamp**: 2026-08-05T03:15:00Z  
**Verdict**: **REMEDIATION PLAN READY**

---

## 1. Observation

Based on direct inspection of code files, review report `reviewer_m2_1/handoff.md`, challenger report `challenger_m2_1/handoff.md`, gate status `GATE_STATUS.md`, and empirical test suite runs (`pytest tests/ -v`):

1. **URL Input Navigation Flaw (`browser.py:279-296`)**:
   - `PhantomBrowser._navigate_from_input()` checks `if "." in cleaned and " " not in cleaned:` to classify input as a direct URL.
   - `localhost:8080`, `localhost:3000`, `127.0.0.1:8080` (or `localhost` without port) do not contain a dot `.`, so they are wrongly formatted into search engine queries (e.g. `https://www.google.com/search?q=localhost:8080`).
   - `file:///C:/path/page.html`, `about:blank`, `chrome://`, `data:` either get prepended with `https://` (`https://file:///...`) or routed to search.
   - Search query space encoding: `Profile.get_search_url` formats spaces via `urllib.parse.quote` (`%20`), whereas `quote_plus` or standard browser query formatting uses `+` or `%20`.

2. **`QMouseEvent` Test Harness Typing (`tests/test_challenger_m2_1.py:127,175,192`)**:
   - In PyQt6 6.11, `QMouseEvent` requires `QPointF` for `position` and `globalPosition` arguments.
   - `QPoint(50, 10)` in test harness constructor calls triggers `TypeError: arguments did not match any overloaded call` on strict PyQt6 signature validation.

3. **IPC Single-Instance Socket Teardown & Contention (`single_instance.py`, `tests/test_e2e_scenarios.py`, `tests/test_challenger_m1_2.py`)**:
   - Running full test suites sequentially can leave active `QLocalServer` instances if a test fails before reaching `guard.release()`.
   - `SingleInstanceGuard` lacks a `__del__` destructor to clean up socket servers upon object garbage collection.
   - Test methods using fixed application key strings (`scenario2_single_instance`, `tier3_stealth_ipc`) fail in `try_acquire()` if previous instances were not released cleanly in a `try...finally` block.

4. **`ProfileSelector.set_profiles()` Layout Stacking & Widget Memory Leak (`profile_selector.py:98-106`)**:
   - `set_profiles()` invokes `self._init_ui()`, which instantiates `QVBoxLayout(self)` a second time on an already-initialized widget.
   - This triggers Qt layout warnings (`QLayout: Attempting to add QLayout "" to ProfileSelector "ProfileSelector", which already has a layout`), duplicates header labels, and leaks card widgets.

5. **`TabWidget._update_tab_title()` Whitespace Fallback Bug (`tab_bar.py:79-85`, `browser.py:265-271`)**:
   - When page title consists of whitespace (e.g. `"   "`), `bool("   ")` is `True`. `title.strip()` evaluates to `""`.
   - Code evaluates `clean_title = title.strip() if title else "New Tab"`, setting `clean_title` to `""` instead of defaulting to `"New Tab"`.

6. **Duplicate `unittest.main()` in `test_challenger_m2_1.py`**:
   - Lines 321-322 contain a duplicate `if __name__ == "__main__": unittest.main()` block.

---

## 2. Logic Chain

1. **URL Navigation Logic**: Direct URLs must be differentiated from search queries using a deterministic, multi-tier check:
   - Tier A: If input starts with known explicit schemes (`http://`, `https://`, `file://`, `about:`, `chrome://`, `data:`), use input as-is.
   - Tier B: If input starts with `localhost` or `127.0.0.1`, prepend `http://`.
   - Tier C: If input has no spaces and contains a dot `.`, prepend `https://`.
   - Tier D: Otherwise, route through profile search engine (`get_search_url`).

2. **ProfileSelector Layout Logic**: Layout construction (`QVBoxLayout` and `cards_layout`) must happen ONCE in `_init_ui()`. Card creation must be decoupled into `_populate_cards()`, which removes existing card widgets from `cards_layout`, deletes them, and adds new cards. `set_profiles()` then simply calls `_populate_cards()`.

3. **Tab Title Fallback Logic**: Checking `title.strip()` must ensure the stripped string is non-empty before accepting it. If `title.strip()` is empty (`""`), it must fall back to `"New Tab"`:
   `clean_title = title.strip() if (title and title.strip()) else "New Tab"`.

4. **Single-Instance IPC Teardown Logic**:
   - Adding `__del__` to `SingleInstanceGuard` calling `self.release()` guarantees socket server cleanup even when test fixture references are dropped.
   - Wrapping guard creation/acquisition in `try...finally` in test fixtures ensures `release()` is called regardless of test assertions.

5. **PyQt6 QMouseEvent Typing Logic**: Using `QPointF(50.0, 10.0)` instead of `QPoint` guarantees compatibility across PyQt6 overloads.

---

## 3. Caveats

- Offscreen platform execution (`QT_QPA_PLATFORM=offscreen`) is used for automated test suites.
- `urllib.parse.quote_plus` encodes spaces as `+`, matching standard web search URL expectations, while `urllib.parse.quote` encodes as `%20`. Standardizing `Profile.get_search_url` to `quote_plus` or accepting both in test assertions ensures search query test robustness.

---

## 4. Conclusion & Technical Remediation Plan

Worker agent must apply the following exact code modifications across the 5 target files:

### Modification 1: `profile_selector.py`
Refactor `ProfileSelector` to reuse the layout cleanly:

```python
class ProfileSelector(QWidget):
    profile_selected = pyqtSignal(object)

    def __init__(self, profiles=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ProfileSelector")
        self.profiles = profiles or []
        self.cards = []

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

        # Container layout for profile cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(self.cards_layout)
        main_layout.addStretch()

        self._populate_cards()

    def _populate_cards(self):
        for card in self.cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

        for p in self.profiles:
            card_btn = self._create_profile_card(p)
            self.cards_layout.addWidget(card_btn)
            self.cards.append(card_btn)

    def set_profiles(self, profiles):
        """Update list of profiles and rebuild UI cards cleanly without duplicating layout."""
        self.profiles = profiles or []
        self._populate_cards()
```

### Modification 2: `tab_bar.py`
Update `_update_tab_title()` in `tab_bar.py`:

```python
    def _update_tab_title(self, view: QWebEngineView, title: str):
        idx = self.indexOf(view)
        if idx >= 0:
            clean_title = title.strip() if (title and title.strip()) else "New Tab"
            display_title = clean_title[:25] + "..." if len(clean_title) > 25 else clean_title
            self.setTabText(idx, display_title)
```

### Modification 3: `browser.py`
1. Update `_update_tab_title()` in `browser.py`:

```python
    def _update_tab_title(self, tab: QWidget, title: str):
        """Update tab title text with truncation."""
        idx = self.tab_widget.indexOf(tab)
        if idx >= 0:
            clean_title = title.strip() if (title and title.strip()) else "New Tab"
            display_title = clean_title[:25] + "..." if len(clean_title) > 25 else clean_title
            self.tab_widget.setTabText(idx, display_title)
```

2. Update `_navigate_from_input()` in `browser.py`:

```python
    def _navigate_from_input(self, text: str):
        """Parse input text as direct URL, localhost, file URI, or search query."""
        cleaned = text.strip()
        if not cleaned:
            return

        known_schemes = ("http://", "https://", "file://", "about:", "chrome://", "data:")
        if cleaned.lower().startswith(known_schemes):
            url_str = cleaned
        elif cleaned.lower().startswith(("localhost", "127.0.0.1")):
            url_str = "http://" + cleaned
        elif "." in cleaned and " " not in cleaned:
            url_str = "https://" + cleaned
        else:
            if hasattr(self, "_active_profile") and hasattr(self._active_profile, "get_search_url"):
                url_str = self._active_profile.get_search_url(cleaned)
            else:
                url_str = f"https://www.google.com/search?q={cleaned}"

        self._navigate(url_str)
```

### Modification 4: `single_instance.py` & Test Fixture Teardown
1. Add destructor to `SingleInstanceGuard` in `single_instance.py`:

```python
    def __del__(self):
        try:
            self.release()
        except Exception:
            pass
```

2. Update single-instance test cases (e.g. `tests/test_e2e_scenarios.py` lines 164-188):

```python
    def test_tier4_scenario_2_multiple_launches_single_instance(self):
        """Tier 4 Scenario 2: Multiple App Launches -> Single Instance Activation across 3 launches."""
        app_key = "scenario2_single_instance"
        g1 = SingleInstanceGuard(app_key=app_key)
        g2 = SingleInstanceGuard(app_key=app_key)
        g3 = SingleInstanceGuard(app_key=app_key)

        activations = []
        g1.activation_requested.connect(lambda: activations.append(True))

        try:
            # Launch 1 (Primary)
            self.assertTrue(g1.try_acquire())

            # Launch 2 (Secondary)
            self.assertFalse(g2.try_acquire())
            self.assertEqual(len(activations), 1)

            # Launch 3 (Tertiary)
            self.assertFalse(g3.try_acquire())
            self.assertEqual(len(activations), 2)
        finally:
            g1.release()
            g2.release()
            g3.release()
```

### Modification 5: `tests/test_challenger_m2_1.py`
1. Update `test_tab_title_truncation_and_whitespace` assertion:

```python
        # Test whitespace title
        self.tab_widget._update_tab_title(view, "   ")
        self.assertEqual(self.tab_widget.tabText(0), "New Tab")
```

2. Verify all `QMouseEvent` constructors use `QPointF`:

```python
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(50.0, 10.0),
            press_point.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
```

3. Remove trailing duplicate `if __name__ == "__main__": unittest.main()` block at bottom of `tests/test_challenger_m2_1.py`.

---

## 5. Verification Method

Execute the following commands after applying the remediation modifications:

1. **Run full test suite**:
   ```powershell
   pytest tests/ -v
   ```
   *Expected Output*: `129 passed in ~25-30s` with exit code `0`.

2. **Run M2 Challenger test suite**:
   ```powershell
   pytest tests/test_challenger_m2_1.py -v
   ```
   *Expected Output*: `13 passed in ~1.5s` with exit code `0`.

3. **Run M1 Challenger test suite**:
   ```powershell
   pytest tests/test_challenger_m1_2.py -v
   ```
   *Expected Output*: `14 passed in ~2.0s` with exit code `0`.
