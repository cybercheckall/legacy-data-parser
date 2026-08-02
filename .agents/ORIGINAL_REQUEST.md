# Original User Request

## 2026-08-02T10:34:23Z

A standalone Windows executable containing a full-featured, next-generation embedded Chromium browser that is completely invisible to all screen-sharing and screen-capture software via Windows `SetWindowDisplayAffinity`. It is a real browser — with tabs, bookmarks, history, URL bar, and full web support — packaged as a single portable `.exe`. The user can freely browse ChatGPT, Claude, Google, documentation, LeetCode solutions, or any website while screen sharing, and nobody will see it.

Working directory: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser`
Integrity mode: `development`

## Requirements

### R1. Stealth Chromium Browser Window (PyQt6 + QWebEngineView)
- Build a real, full-featured embedded Chromium browser using PyQt6 and `QWebEngineView`.
- Apply the Windows API `SetWindowDisplayAffinity` with flag `WDA_EXCLUDEFROMCAPTURE` (`0x00000011`) on the browser window's HWND so it is invisible to all screen sharing, screen recording, and screenshot software (Zoom, Teams, OBS, Slack, Windows Snip, etc.).
- The window must have no taskbar icon, remain always-on-top, and be freely resizable and draggable.
- The window should support minimize, maximize/restore (double-click title bar), and close.

### R2. Full Browser Functionality
- Support tabbed browsing: open new tabs (`Ctrl+T`), close tabs (`Ctrl+W`), switch between tabs.
- Include a URL/address bar with navigation (Enter to go), back/forward buttons, and a refresh button.
- Include a bookmarks bar pre-loaded with useful sites: ChatGPT, Claude, Google, Stack Overflow, and GitHub.
- Support full modern web features: JavaScript, cookies, localStorage, sessionStorage, WebSocket, file uploads/downloads, clipboard copy/paste, and form auto-fill.
- Support keyboard shortcuts: `Ctrl+L` to focus URL bar, `Ctrl+R` to refresh, `F5` to refresh, `Alt+Left` for back, `Alt+Right` for forward.

### R3. Global Hotkey & Window Controls
- Implement a global hotkey (`Ctrl+Shift+B`) to toggle visibility (show/hide) of the browser window from anywhere.
- The browser window size should be freely adjustable by the user (drag edges to resize, maximize, restore).
- Pressing `Esc` hides the window (does not close it).

### R4. Standalone Executable Packaging & Logging
- Package the application into a standalone `.exe` using PyInstaller, including all QtWebEngine dependencies.
- The executable must run consoleless without requiring Python installed.
- Write application logs (startup, navigation events, errors) to `~/Desktop/stealth_browser.log`.

## Acceptance Criteria

### Browser & Stealth
- [ ] The browser window renders modern web pages with full JavaScript support (e.g., ChatGPT, Claude web apps load and function correctly).
- [ ] Programmatic verification: A test checks that `SetWindowDisplayAffinity` is called on the browser window's active HWND with capture-exclude value `0x00000011`.
- [ ] The window has no taskbar icon and stays on top of other windows.
- [ ] The window is freely resizable by dragging edges/corners.

### Tabbed Browsing & Navigation
- [ ] New tabs can be opened and closed with keyboard shortcuts.
- [ ] A URL typed into the address bar navigates to the correct page.
- [ ] Back/forward/refresh buttons work correctly.
- [ ] Bookmarks bar loads and navigates to the pre-configured sites.

### Hotkey & Visibility
- [ ] Global hotkey (`Ctrl+Shift+B`) toggles browser window visibility from any application.
- [ ] Pressing Esc hides the window without closing it.

### Packaging
- [ ] PyInstaller builds a standalone `.exe` without errors.
- [ ] The `.exe` launches the stealth browser consoleless and produces a desktop log file.
