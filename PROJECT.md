# Project: Owl Stealth Browser Feature Enhancements

## Architecture
- PyQt6-based stealth browser architecture ("Owl") featuring frameless window design, display affinity screen capture exclusion (`SetWindowDisplayAffinity`), off-the-record ephemeral WebEngine profiles, single-instance IPC enforcement, and modular UI components (TitleBar, TabBar, NavBar, ProfileSelector, SettingsPage, AISidePanel).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1 Guest Mode Profile Selector | Default startup profile selector to show ONLY Guest mode initially ("Guest mode", "👤", google.com). | M1 | Follow-up 2026-08-05 |
| 2 | R2 Title Bar Transparency Slider | Window transparency/opacity slider (QSlider, 10%-100%) in custom TitleBar between title label and window controls. | M2 | Follow-up 2026-08-05 |
| 3 | R3 Chrome-Style Adjacent Tab Bar | Redesign tab bar for Chrome-style look with rounded top corners and '+' button placed immediately adjacent to the right of the last active tab. | M3 | Follow-up 2026-08-05 |
| 4 | R4 Clean Google Search Homepage | Default homepage to clean Google search page (`https://www.google.com`), remove all homepage quick-links/shortcuts, standard URL bar without AI Mode button, keep floating AI sparkle button & side panel 100% intact. | M4 | Follow-up 2026-08-05 |
| 5 | R5 Stealth & Non-Regression Hardening | Preserve all 4 stealth features (`WDA_EXCLUDEFROMCAPTURE`, `WS_EX_TOOLWINDOW`, `WindowStaysOnTopHint`, `Ctrl+Shift+B` hotkey) and pass all 159 existing automated tests. | M5 | Follow-up 2026-08-05 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Guest Mode Profile Selector | Update `profile_manager.py` defaults to Guest mode only (`id="guest"`, `name="Guest mode"`) and update `browser.py` startup trigger. | none | PLANNED |
| 2 | M2: Title Bar Transparency Slider | Add horizontal QSlider to `TitleBar`, isolate mouse drag events, connect to `setWindowOpacity`, and update QSS styling in `styles.py`. | M1 | PLANNED |
| 3 | M3: Chrome-Style Adjacent Tab Bar | Dynamic positioning of `new_tab_btn` immediately to the right of the last active tab, rounded top corner QSS styling, preserving test attributes. | M2 | PLANNED |
| 4 | M4: Clean Google Homepage & Nav Bar | Set `HOME_URL = "https://www.google.com"`, remove quick-links bar from UI, ensure standard URL bar without AI Mode button. | M3 | PLANNED |
| 5 | M5: E2E Verification & Non-Regression | Verify all 159 automated tests pass, verify stealth features intact, and ensure zero regressions across all requirements. | M4 | PLANNED |

## Interface Contracts
### `profile_manager` ↔ `browser`
- `_create_defaults()` returns single `Guest mode` profile (`id="guest"`, `name="Guest mode"`, `avatar="👤"`, `homepage="https://www.google.com"`).
- `show_profile_selector_on_start` triggers `ProfileSelector` view on launch.

### `title_bar` ↔ `OwlBrowser`
- `TitleBar` embeds `self.opacity_slider` (`QSlider`, `objectName="OpacitySlider"`, range 10..100).
- Slider value change updates parent `window().setWindowOpacity(val / 100.0)`. Mouse press/drag on slider is consumed and ignored by window move logic.

### `tab_bar` ↔ `OwlBrowser`
- `TabWidget` retains `self.new_tab_btn` (`QPushButton("+")`) emitting `new_tab_requested`.
- Positions `new_tab_btn` dynamically at `last_tab_rect.right() + 4` adjacent to active tab strip.

### `nav_bar` ↔ `browser`
- `NavBar` provides reload button and URL bar without AI Mode button.
- `HOME_URL = "https://www.google.com"`. Quick-links shortcuts hidden/removed from homepage view.

### Stealth Integration
- `display_affinity.py`: `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE = 0x11)`.
- `browser.py`: `Qt.WindowType.Tool` (`WS_EX_TOOLWINDOW`) and `Qt.WindowType.WindowStaysOnTopHint`.
- `hotkey.py`: `Ctrl+Shift+B` daemon toggle.

## Code Layout
- `main.py`: Application entry point, QSS loading, stealth startup
- `profile_manager.py`: Profile schema, Guest mode default, atomic JSON storage
- `profile_selector.py`: Startup profile selector view
- `title_bar.py`: Custom TitleBar with opacity slider and drag handling
- `tab_bar.py`: Chrome-style TabWidget with adjacent '+' button
- `nav_bar.py`: Navigation bar with reload button and URL bar
- `styles.py`: Application QSS stylesheet (dark glass theme, tabs, slider)
- `browser.py`: OwlBrowser QMainWindow assembling components
- `display_affinity.py`: Win32 display protection
- `hotkey.py`: Global hotkey listener
- `single_instance.py`: Single instance guard
- `tests/`: 19 test files containing 159 automated tests
