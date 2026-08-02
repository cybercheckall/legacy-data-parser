# Project: Stealth Chromium Browser

## Architecture
Stealth Chromium Browser is a standalone Windows desktop application built with PyQt6 (`QWebEngineView`) and native Windows Win32 API (`SetWindowDisplayAffinity`).

### Core Modules
1. **`stealth_browser/config.py`**: Configuration constants, bookmark URLs, log paths (`~/Desktop/stealth_browser.log`), default settings.
2. **`stealth_browser/logger.py`**: Custom logger setting up standard file handlers pointing to `~/Desktop/stealth_browser.log`.
3. **`stealth_browser/win32_utils.py`**: Native Windows API integration: `SetWindowDisplayAffinity(hwnd, 0x11)` (`WDA_EXCLUDEFROMCAPTURE`), taskbar icon manipulation, HWND helpers using `ctypes`.
4. **`stealth_browser/browser_tab.py`**: Custom `QWebEngineView` tab component supporting JS, cookies, WebSockets, downloads, local storage, clipboard, auto-fill.
5. **`stealth_browser/tab_widget.py`**: `QTabWidget` wrapper handling new tabs (`Ctrl+T`), close tabs (`Ctrl+W`), tab title updates, active URL syncing.
6. **`stealth_browser/nav_bar.py`**: Navigation toolbar containing Back, Forward, Refresh, URL line edit, Bookmarks bar.
7. **`stealth_browser/hotkey_manager.py`**: Global hotkey listener (`Ctrl+Shift+B`) using native Win32 `RegisterHotKey` / `QAbstractNativeEventFilter` or background listener to toggle window visibility safely across all Windows apps.
8. **`stealth_browser/main_window.py`**: Main `QMainWindow` subclass integrating all sub-components, applying `Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint`, handling drag/resize, custom double-click maximize/restore, Esc to hide, and display affinity call after native window creation.
9. **`main.py`**: Application entry point initializing `QApplication`, logging setup, instantiating `MainWindow`, and running event loop consoleless.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1_stealth_window | Core PyQt6 window, SetWindowDisplayAffinity 0x11, Tool flag (no taskbar icon), StaysOnTop, Esc hide, Logger setup | none | PLANNED |
| 2 | M2_browser_features | Tabbed browsing (Ctrl+T/W), URL navigation (Ctrl+L), Back/Forward/Refresh (Ctrl+R/F5), Bookmarks bar, full web settings | M1 | PLANNED |
| 3 | M3_hotkeys_controls | Global hotkey Ctrl+Shift+B, Win32 event filter / background listener, drag-resize & window control refinements | M1, M2 | PLANNED |
| 4 | M4_pyinstaller_package | PyInstaller standalone packaging (.exe), PySide6/PyQt6 QtWebEngine dynamic dependencies inclusion, consoleless verification, desktop log validation | M1, M2, M3 | PLANNED |
| 5 | M5_e2e_hardening | Full E2E test suite validation (Tiers 1-4), Tier 5 adversarial coverage hardening, clean forensic integrity audit | M1, M2, M3, M4 | PLANNED |

## Interface Contracts

### win32_utils ↔ main_window
- `set_stealth_affinity(hwnd: int) -> bool`: Calls `ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)` and returns True if successful.
- `hide_from_taskbar(hwnd: int)`: Ensures window style has `WS_EX_TOOLWINDOW` or Qt Tool flag applied.

### hotkey_manager ↔ main_window
- `register_global_hotkey(callback: Callable[[], None])`: Registers `Ctrl+Shift+B` to trigger window toggle visibility.

## Code Layout
```
stealth_browser/
├── __init__.py
├── config.py
├── logger.py
├── win32_utils.py
├── browser_tab.py
├── tab_widget.py
├── nav_bar.py
├── hotkey_manager.py
└── main_window.py
main.py
tests/
├── test_stealth_affinity.py
├── test_browser_features.py
├── test_hotkey.py
└── test_e2e.py
build.py / stealth_browser.spec
```
