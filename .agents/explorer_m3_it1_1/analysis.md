# Technical Analysis & Implementation Strategy: Feature 6 (AI Side Panel & Floating AI Sparkle Button)

**Author**: Explorer 1 (Milestone 3, Iteration 1)  
**Target Architecture**: Phantom Workspace Browser  
**Scope**: Feature 6 — Floating AI Sparkle Button (`AIFloatingButton`) & Sliding ChatGPT Side Panel (`AISidePanel`)  

---

## 1. Architectural Overview & Component Decomposition

Feature 6 integrates an embedded AI assistant into the Phantom Workspace browser window. The system consists of two primary UI widgets and their integration into `PhantomBrowser`:

1. **`AIFloatingButton` (`QPushButton`)**:
   - A circular ~52x52px floating button positioned at the bottom-center of the browser viewport.
   - Displays a sparkle icon (`✦`), features modern indigo glassmorphic styling, and includes an animated pulse/glow effect.
   - Clicking toggles the AI side panel visibility.

2. **`AISidePanel` (`QWidget`)**:
   - A 380–420px wide (target: 400px) slide-in side panel container anchored to the right side of the main window.
   - Contains a header bar with title `"ChatGPT"` and a close (`✕`) button.
   - Embeds a `QWebEngineView` loading `https://chatgpt.com`.
   - Uses `QPropertyAnimation` for smooth slide-in and slide-out transitions.

3. **`PhantomBrowser` Integration**:
   - Manages parenting and layout stacking.
   - Overrides `resizeEvent()` to dynamically reposition the floating button and side panel on window resize.
   - Handles z-order management (`raise_()`) so the floating button and side panel sit cleanly above browser tab content.

---

## 2. Detailed Technical Specifications

### 2.1 `AIFloatingButton` Module Specification (`ai_panel.py`)

- **Class Definition**: `class AIFloatingButton(QPushButton)`
- **Dimensions**: Fixed size `52px` x `52px` (`setFixedSize(52, 52)`).
- **Icon / Text**: Displays `"✦"` (Unicode sparkle character `\u2726` or `✦`), styled with bold 20px font.
- **Visual Style**:
  - Border radius: `26px` (perfect circle).
  - Background: Indigo glass gradient `qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5)`.
  - Cursor: `Qt.CursorShape.PointingHandCursor`.
  - Glow / Pulse Effect: `QGraphicsDropShadowEffect` with blur radius `12px`, color `#818cf8` (indigo-accent). An internal `QPropertyAnimation` or `QTimer` smoothly pulses `blurRadius` between `8px` and `22px`.
- **Parenting**: Parented directly to `PhantomBrowser` or `workspace_widget`.

#### Positioning Logic:
```python
def update_position(self, parent_width: int, parent_height: int, margin_bottom: int = 24):
    x = (parent_width - self.width()) // 2
    y = parent_height - self.height() - margin_bottom
    self.move(x, y)
    self.raise_()
```

---

### 2.2 `AISidePanel` Module Specification (`ai_panel.py`)

- **Class Definition**: `class AISidePanel(QWidget)`
- **Dimensions**: Width: `400px` fixed (`DEFAULT_WIDTH = 400`). Height: matches parent window workspace height (`parent_height - top_offset`).
- **Initial State**: Hidden (`self.setVisible(False)`), located off-screen at `x = parent_width`.
- **Child Components**:
  1. **Header Container** (`QWidget`, `setObjectName("AISidePanelHeader")`, fixed height `42px`):
     - Horizontal layout (`QHBoxLayout`) with 12px margins.
     - Title Label (`QLabel("ChatGPT")`, `setObjectName("AISidePanelTitle")`, `header_label` attribute).
     - Close Button (`QPushButton("✕")`, `setObjectName("AISidePanelCloseBtn")`, `close_btn` attribute, fixed size `28x28px`).
  2. **Web Engine View** (`QWebEngineView`, `setObjectName("AISidePanelWebview")`, `webview` attribute):
     - Initial URL set to `QUrl("https://chatgpt.com")`.
     - Parented inside vertical layout below header.

- **Animation Mechanics (`QPropertyAnimation`)**:
  - Target property: `b"geometry"`.
  - Duration: `250ms`.
  - Easing curve: `QEasingCurve.Type.OutCubic`.
  - State Tracking: `self._is_expanded = False`.
  - **`show_panel()`**:
    - Calculates target visible geometry: `QRect(parent_width - 400, top_offset, 400, panel_height)`.
    - Makes widget visible (`self.show()`), brings to front (`self.raise_()`).
    - Animates from current geometry (or off-screen `parent_width`) to target visible geometry.
    - Sets `self._is_expanded = True`.
  - **`hide_panel()`**:
    - Calculates target hidden geometry: `QRect(parent_width, top_offset, 400, panel_height)`.
    - Animates from current geometry to off-screen geometry.
    - On animation finished signal (`anim.finished.connect`), calls `self.hide()`.
    - Sets `self._is_expanded = False`.
  - **`toggle_panel()`**:
    - If `self._is_expanded` (or target is open), calls `hide_panel()`.
    - Else, calls `show_panel()`.

---

### 2.3 `styles.py` QSS Extensions

Add the following style rules to `DARK_GLASS_STYLE` in `styles.py`:

```css
/* AI Floating Button */
#AIFloatingButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 26px;
    font-size: 20px;
    font-weight: bold;
}

#AIFloatingButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #818cf8, stop:1 #6366f1);
    border: 1px solid #a5b4fc;
}

#AIFloatingButton:pressed {
    background-color: #4338ca;
}

/* AI Side Panel */
#AISidePanel {
    background-color: rgba(15, 23, 42, 0.95);
    border-left: 1px solid rgba(255, 255, 255, 0.12);
}

#AISidePanelHeader {
    background-color: rgba(30, 41, 59, 0.85);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

#AISidePanelTitle {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

#AISidePanelCloseBtn {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}

#AISidePanelCloseBtn:hover {
    background-color: #ef4444;
    color: #ffffff;
}
```

---

## 3. Window Integration & Resize Logic in `browser.py`

In `PhantomBrowser._build_workspace_ui()`:

```python
# Instantiate AI Side Panel & Floating Button
self.ai_side_panel = AISidePanel(self)
self.ai_floating_button = AIFloatingButton(self)

# Connect triggers
self.ai_floating_button.clicked.connect(self.ai_side_panel.toggle_panel)
self.ai_side_panel.close_btn.clicked.connect(self.ai_side_panel.hide_panel)
```

In `PhantomBrowser.resizeEvent(event)`:

```python
def resizeEvent(self, event):
    super().resizeEvent(event)
    
    # Reposition floating button at bottom-center
    if hasattr(self, "ai_floating_button"):
        bw, bh = 52, 52
        btn_x = (self.width() - bw) // 2
        btn_y = self.height() - bh - 24
        self.ai_floating_button.move(btn_x, btn_y)
        self.ai_floating_button.raise_()

    # Reposition side panel
    if hasattr(self, "ai_side_panel"):
        top_offset = self.title_bar.height() + self.nav_bar.height()
        panel_h = self.height() - top_offset
        panel_w = self.ai_side_panel.width()
        
        if self.ai_side_panel._is_expanded:
            self.ai_side_panel.setGeometry(self.width() - panel_w, top_offset, panel_w, panel_h)
        else:
            self.ai_side_panel.setGeometry(self.width(), top_offset, panel_w, panel_h)
        
        if self.ai_side_panel.isVisible():
            self.ai_side_panel.raise_()
```

---

## 4. Test Strategy & Headless Compatibility

Existing test file `tests/test_ai_side_panel.py` specifies 10 unit tests:
1. `test_tier1_floating_button_creation_and_position`: Verifies 52x52px size and `"✦"` icon text.
2. `test_tier1_panel_slide_in_toggle`: Verifies starting hidden state and toggle mechanics.
3. `test_tier1_panel_dimensions_and_header`: Verifies width within 380–420px, `"ChatGPT"` header label, and `close_btn`.
4. `test_tier1_panel_chatgpt_webview_url`: Verifies `webview` presence and URL pointing to `https://chatgpt.com`.
5. `test_tier1_panel_close_button`: Verifies clicking `close_btn` hides side panel.
6. `test_tier2_rapid_toggle_panel_animation`: Verifies 10 rapid toggles leave panel in expected state without crash or desync.
7. `test_tier2_window_resize_repositions_button`: Verifies window resize maintains valid geometry.
8. `test_tier2_panel_hidden_by_default`: Verifies newly created panel starts hidden.
9. `test_tier2_floating_button_z_order_top`: Verifies `raise_()` call on floating button.
10. `test_tier2_multiple_toggle_calls_idempotent`: Verifies repeated `show_panel()` and `hide_panel()` calls are idempotent.

All tests run in standard off-screen Qt environment without requiring an active GPU or internet connection.

---

## 5. Summary Strategy for Implementation Phase

1. Create `ai_panel.py` implementing `AIFloatingButton` and `AISidePanel` per specifications above.
2. Update `styles.py` with `#AIFloatingButton` and `#AISidePanel` QSS.
3. Integrate `AISidePanel` and `AIFloatingButton` into `PhantomBrowser` in `browser.py` with proper resize handling and signal wiring.
4. Execute `pytest tests/test_ai_side_panel.py -v` and `pytest tests/ -v` to verify 100% test passage across the full suite.
