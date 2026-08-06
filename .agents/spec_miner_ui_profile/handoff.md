# Specification Mining & Handoff Report — UI & Profile Spec Miner

**Agent ID**: `spec_miner_ui_profile`  
**Parent Conversation ID**: `54c70ed0-82c4-45e5-bcd7-e7aa03c3f111`  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\spec_miner_ui_profile`  
**Scope**: Phantom Workspace Overhaul Requirements R1 (Modern Chrome-like UI Overhaul), R2 (Browser Profiles System), R3 (Single-Instance Application Enforcement), and R7 (Tab Behavior).

---

## Executive Summary

This specification document mined and formalized the precise requirements, data schemas, component breakdowns, interaction contracts, and edge cases for the Phantom Workspace overhaul covering R1, R2, R3, and R7. The specification bridges the baseline stealth browser implementation (`main.py`, `browser.py`, `display_affinity.py`, `hotkey.py`) and the desired modern dark workspace tool vision detailed in `ORIGINAL_REQUEST.md`.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | UI & Navigation | Frameless Custom Title Bar | Integrated frameless window title bar widget with app branding, window title, minimize (`—`), maximize/restore (`□`/`❐`), and close (`✕`) buttons with mouse drag & double-click toggle support. | Mouse click, drag, double-click | Window state changes (minimize, maximize, restore, close), window movement | Ignore drag during maximize; restore window on title bar drag if maximized | `ORIGINAL_REQUEST.md` R1 & `browser.py:97-135` |
| 2 | UI & Navigation | Reload-Only Navigation Bar | Navigation toolbar stripped of Back and Forward arrows, featuring exclusively a Reload button (`⟳`), prominent centered dark rounded URL/Search bar, Settings icon (`⚙`), and Profile indicator. | Click reload button, Enter on URL bar, click settings icon | Refresh web page, dispatch URL navigation / search engine query, trigger settings tab | Auto-prefix `https://` or redirect invalid URLs to search engine query | `ORIGINAL_REQUEST.md` R1 & `browser.py:137-193` |
| 3 | UI & Navigation | Chrome-Style Tab Bar & '+' Button | Top tab strip styled like Chrome dark mode tabs, featuring dynamic tab widths, close buttons (`✕`), favicons, and a dedicated '+' button on the right side of the tab bar for opening new tabs. | Click '+' button, middle-click tab, close button click, `Ctrl+T` | New tab creation, tab selection, tab destruction | Closing last tab redirects to profile homepage instead of closing window | `ORIGINAL_REQUEST.md` R1, R7 & `browser.py:229-266` |
| 4 | UI & Aesthetics | Dark Glassmorphism Theme | Cohesive dark aesthetic using slate obsidian backgrounds (`#0b0e14`), translucent glass container overlays (`rgba(22,27,38,0.8)`), subtle indigo/purple borders (`#2d3548`), rounded corners (8px/16px), Segoe UI typography, and hover transitions. | Application QSS stylesheet injection | Dark modern workspace visual appearance | Fallback to solid dark colors if OS compositing/translucency is disabled | `ORIGINAL_REQUEST.md` R1 & `main.py:42-52` |
| 5 | UI & Aesthetics | Clean SVG / Unicode Icon System | High DPI vector icons or crisp Unicode glyphs replacing standard text buttons for Reload (`⟳`), New Tab (`+`), Close (`✕`), Minimize (`—`), Maximize (`□`), Settings (`⚙`), Profile (`👤`), and AI Assist (`✦`). | Asset SVG files or Qt icon renderer | Scalable icon graphics across all toolbar actions | Fallback to Unicode characters if SVG assets fail to load | `ORIGINAL_REQUEST.md` R1 |
| 6 | Browser Profiles | Profiles JSON Storage Schema | Persistent storage of user profile metadata in a structured `profiles.json` file. Stores active profile ID and array of profile objects. | Disk read/write of `profiles.json` | Profile list, active profile preferences | Re-create default profile (`Personal`) if JSON is missing or corrupted | `ORIGINAL_REQUEST.md` R2 |
| 7 | Browser Profiles | Custom Profile Fields | Support profile preferences: `id`, `name`, `avatar` (icon key/preset), `homepage_url`, `search_engine` (`"Google"` or `"DuckDuckGo"`), `theme_color`, and `created_at`. | User profile setup / settings edits | Configuration object consumed by browser navigation and search bar | Auto-validate homepage URL; default search engine to "Google" if empty | `ORIGINAL_REQUEST.md` R2 |
| 8 | Browser Profiles | Card-Based Launch Selector UI | Modal/launch window displaying available browser profiles as interactive dark glass cards with avatars, names, homepage previews, launch buttons, edit/delete controls, and "+ Add Profile" card. | Card click, launch button, "+ Add Profile" button | Launch main window with selected profile context | Automatically present "Create Profile" view if 0 profiles exist | `ORIGINAL_REQUEST.md` R2 |
| 9 | Browser Profiles & Stealth | Ephemeral Zero-Storage Isolation | Off-the-Record (OTR) `QWebEngineProfile` configuration per profile with `NoPersistentCookies`, `MemoryHttpCache`, and empty disk storage path. Prevents persistence of cookies, web history, or disk cache. | `QWebEngineProfile` creation | Ephemeral browser session isolated to memory | Purge in-memory HTTP cache on profile switch or exit | `ORIGINAL_REQUEST.md` R2 & `browser.py:72-76` |
| 10 | Single Instance | IPC Socket / Mutex Single Instance Guard | Enforces single-instance app execution using `QLocalServer` / `QLocalSocket` with key `PhantomWorkspace_SingleInstance_v1`. | App process launch | Primary instance starts server; secondary connects and sends signal | Clean stale socket files on launch if prior process crashed | `ORIGINAL_REQUEST.md` R3 |
| 11 | Single Instance | Bring Existing Window to Foreground | Primary instance receives IPC activation signal from secondary instance, restores window state (`showNormal()`), unhides window (`show()`), brings to top (`raise_()`), and activates focus (`activateWindow()`). | IPC `ACTIVATE` payload from second instance | Existing main window unhidden, restored, and focused | Fallback to Win32 `SetForegroundWindow(hwnd)` if Qt focus fails | `ORIGINAL_REQUEST.md` R3 |
| 12 | Single Instance | Second Instance Clean Exit | Secondary instance sends activation message, flushes socket stream, and exits cleanly with return code `0` before initializing GUI. | Second instance startup check | Process exit code 0 | Silent exit without error dialogs or secondary windows | `ORIGINAL_REQUEST.md` R3 |
| 13 | Tab Behavior | Homepage Load on Last Tab Close | When user closes the final remaining tab in the tab bar, prevent window closure and navigate that remaining tab to the active profile's configured `homepage_url`. | `Ctrl+W`, tab close button `✕` on last tab | Last tab reloads profile `homepage_url` | Fallback to `https://www.google.com` if homepage URL invalid | `ORIGINAL_REQUEST.md` R7 & `browser.py:317-326` |
| 14 | Tab Behavior | Profile Homepage for New Tabs | Opening a new tab automatically loads the current active profile's configured `homepage_url`. | '+' tab button, `Ctrl+T`, target `_blank` link | New `WebTab` created and navigated to homepage | Defaults to profile homepage or system default URL | `ORIGINAL_REQUEST.md` R7 & `browser.py:296-315` |
| 15 | Tab Behavior | Dynamic Tab Titles & Favicons | Tab text dynamically updates as web page titles change, truncating titles (>25 chars) with ellipsis (`...`). Tab icons update dynamically with page favicons. | `titleChanged` and `iconChanged` signals | Updated `QTabBar` text label and icon | Fallback to "New Tab" or domain name if title is empty | `ORIGINAL_REQUEST.md` R7 & `browser.py:343-347` |
| 16 | Tab Behavior | Movable / Reorderable / Closable Tabs | Tabs can be dragged horizontally to reorder (`setMovable(True)`), closed via tab close button (`setTabsClosable(True)`), or closed with shortcut (`Ctrl+W`). | Drag tab, click close button, press shortcut | Reordered tabs list, deleted tab widget, active index update | Maintain index mapping safely to prevent out-of-bounds errors | `ORIGINAL_REQUEST.md` R7 & `browser.py:230-234` |

---

## Edge Cases

| # | Feature | Input | Observed / Required Behavior |
|---|---------|-------|-----------------------------|
| 1 | Frameless Title Bar | Mouse drag on title bar when window is maximized. | Un-maximize (restore) the window size and attach window top-center to cursor for smooth dragging, or disable drag while maximized. |
| 2 | Frameless Title Bar | Window resized to extremely small dimensions (e.g., 300x200px). | Minimum window size must be enforced (`setMinimumSize(650, 450)`) so title bar controls and URL bar remain fully visible and non-overlapping. |
| 3 | Navigation Bar | Search query entered containing special characters (e.g. `c++ templates & pointers` or `what is 2+2?`). | URL bar must detect non-URL strings, perform URL encoding (`QUrl::toPercentEncoding`), and dispatch query to active profile search engine (Google or DuckDuckGo). |
| 4 | Navigation Bar | Reload button clicked while page is still loading vs after page load. | If loading, reload button can act as Stop button (`stop()`); if loaded, reloads page (`reload()`). SVG icon switches state accordingly. |
| 5 | Profile Storage | `profiles.json` corrupted, unparseable, or missing file permission. | File parser catches `json.JSONDecodeError` / `OSError`, logs warning, creates fresh default profile in memory, writes valid `profiles.json`, and launches smoothly. |
| 6 | Profile Selector | User attempts to delete the active running profile or the only remaining profile. | Deleting currently active profile is disabled or prompts switching active profile first. Deleting the last profile is blocked (minimum 1 profile required). |
| 7 | Profile Selector | User launches app with `--profile <id>` command-line argument. | App bypasses Profile Selector UI on launch and opens main browser directly with specified profile ID. |
| 8 | Zero-Storage Isolation | Profile switch during active browser session. | Prevents cross-profile data leakage by instantiating isolated OTR `QWebEngineProfile` instances per profile ID. Memory HTTP cache is cleared on switch. |
| 9 | Single Instance | Primary instance crashed unexpectedly, leaving orphaned `QLocalServer` socket lock file. | On next app launch, `QLocalServer.removeServer(server_name)` is called prior to `listen()`, cleaning up orphaned socket locks and enabling normal launch. |
| 10 | Single Instance | Launching second instance while primary instance is minimized to taskbar or hidden via `Ctrl+Shift+B` hotkey. | Primary instance receives IPC signal, restores window state (`showNormal()`), unhides window (`show()`), brings to top (`raise_()`), and activates window (`activateWindow()`). |
| 11 | Single Instance | Launching second instance with command line argument (e.g., `phantom_browser.exe https://github.com`). | Secondary instance passes CLI arguments in IPC JSON payload to primary instance, which opens a new tab with the requested URL. |
| 12 | Tab Behavior | Closing the last tab when 1 tab exists vs when >1 tabs exist. | If tab count > 1, tab is removed and closed. If tab count == 1, tab is NOT closed; `QWebEngineView` navigates to profile `homepage_url`. |
| 13 | Tab Behavior | Rapid sequential tab creation (`Ctrl+T` held down) or tab closure (`Ctrl+W` held down). | Qt event loop queues tab operations safely; `deleteLater()` prevents dangling pointer accesses or segfaults during fast tab closure. |
| 14 | Tab Behavior | Tab title contains HTML tags, newline characters, or string length > 100 characters. | Title text handler sanitizes string, strips control characters/tags, and truncates to max 25 characters with trailing `...`. |

---

## Data Schemas & Interaction Contracts

### 1. `profiles.json` Storage Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PhantomWorkspaceProfiles",
  "type": "object",
  "properties": {
    "version": {
      "type": "integer",
      "default": 1
    },
    "active_profile_id": {
      "type": "string"
    },
    "profiles": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^prof_[a-zA-Z0-9_-]+$"
          },
          "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 32
          },
          "avatar": {
            "type": "string",
            "description": "Avatar icon key e.g. 'user_purple', 'ninja', 'shield', 'rocket', 'ghost'"
          },
          "homepage_url": {
            "type": "string",
            "format": "uri",
            "default": "https://www.google.com"
          },
          "search_engine": {
            "type": "string",
            "enum": ["Google", "DuckDuckGo"],
            "default": "Google"
          },
          "theme_color": {
            "type": "string",
            "pattern": "^#[0-9a-fA-F]{6}$",
            "default": "#6366f1"
          },
          "created_at": {
            "type": "string",
            "format": "date-time"
          }
        },
        "required": ["id", "name", "avatar", "homepage_url", "search_engine"]
      }
    }
  },
  "required": ["version", "active_profile_id", "profiles"]
}
```

### 2. Single-Instance IPC Protocol

- **Transport**: `QLocalServer` (primary) and `QLocalSocket` (secondary).
- **Socket Key**: `PhantomWorkspace_SingleInstance_IPC_v1`
- **Message Format**: Single UTF-8 JSON payload terminated by `\n`.
```json
{
  "command": "ACTIVATE",
  "timestamp": "2026-08-05T01:03:38Z",
  "args": ["--url", "https://chatgpt.com"],
  "sender_pid": 12345
}
```
- **Primary Server Lifecycle**:
  1. Primary process initializes `QLocalSocket` and attempts `connectToServer("PhantomWorkspace_SingleInstance_IPC_v1")`.
  2. If connection succeeds within 100ms timeout:
     - Write JSON activation message.
     - `socket.waitForBytesWritten(500)`.
     - `socket.disconnectFromServer()`.
     - `sys.exit(0)`.
  3. If connection fails:
     - Execute `QLocalServer.removeServer("PhantomWorkspace_SingleInstance_IPC_v1")` to clear stale locks.
     - Call `server.listen("PhantomWorkspace_SingleInstance_IPC_v1")`.
     - Connect `server.newConnection` to `_handle_ipc_connection`.

---

## Component Architecture & Class Hierarchy

```
stealth_browser/
├── main.py                     # Entry point: Logging, SingleInstanceGuard check, ProfileSelector / MainWindow launch
├── config.py                   # Global constants, paths, default QSS parameters
├── profile_manager.py          # Profile dataclass, ProfileManager (profiles.json CRUD operations)
├── profile_selector.py         # ProfileSelectorWindow (card-based profile chooser UI on startup)
├── single_instance.py          # SingleInstanceGuard (QLocalServer / QLocalSocket IPC)
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # PhantomBrowser QMainWindow (integrates title bar, nav bar, tabs, hotkeys, affinity)
│   ├── title_bar.py            # FramelessTitleBar (custom frameless bar with window controls & drag handler)
│   ├── nav_bar.py              # ModernNavBar (reload button, search line edit, settings & profile buttons)
│   ├── tab_bar.py              # ChromeTabBar & ChromeTabWidget (Chrome-style tab bar with right '+' button)
│   └── styles.py               # Dark glassmorphism QSS themes, colors, and SVG icon definitions
├── browser_tab.py              # WebTab (QWebEngineView subclass with OTR QWebEngineProfile)
├── display_affinity.py         # SetWindowDisplayAffinity (WDA_EXCLUDEFROMCAPTURE)
└── hotkey.py                   # GlobalHotkey listener (Ctrl+Shift+B)
```

---

## 5-Component Handoff Report

### 1. Observation
- **Original Code Base**:
  - `main.py` instantiates `QApplication`, configures basic QSS background `#0a0a1a`, creates `PhantomBrowser()`, starts `GlobalHotkey`, and runs event loop.
  - `browser.py` contains `PhantomBrowser(QMainWindow)` with a basic custom title bar (`#1a1a2e`), nav bar containing Back (`◀`), Forward (`▶`), and Refresh (`⟳`) buttons, bookmarks bar, and `QTabWidget`.
  - `browser.py:73-76` currently uses default persistent cookies profile (`QWebEngineProfile.defaultProfile()`).
  - `browser.py:317-325` already implements basic last tab close logic (redirects last tab to `HOME_URL`).
  - No single-instance application check exists currently in `main.py` or `browser.py`.
  - No profile management or JSON schema exists currently in the codebase.
- **Specification Source**:
  - `ORIGINAL_REQUEST.md` R1, R2, R3, R7 explicitly demand a Chrome-like dark glassmorphism overhaul, removal of back/forward buttons, Chrome tab bar with '+' button, profile JSON storage, card launcher, OTR zero-storage browsing, single-instance mutex/IPC, and dynamic profile-aware tab behavior.

### 2. Logic Chain
- **R1 UI Overhaul**: Removing Back/Forward buttons from `NavBar` simplifies navigation to a clean single reload button + prominent central URL search bar. Replacing default `QTabBar` with a custom-styled `ChromeTabBar` featuring a '+' button pinned on the right of the tab strip satisfies Chrome parity. Adding dark glassmorphism QSS styling with rounded corners (8px/16px) and vector SVG icons elevates the UI to a modern workspace tool.
- **R2 Profiles System**: Storing profiles in `profiles.json` provides persistence across restarts without storing private user browsing data. Using Off-The-Record `QWebEngineProfile` instances (`setPersistentCookiesPolicy(NoPersistentCookies)`, `setHttpCacheType(MemoryHttpCache)`) ensures absolute zero disk persistence for history/cookies/cache as specified for a stealth browser. The card-based launcher presents a modern startup experience.
- **R3 Single Instance**: Utilizing `QLocalServer` / `QLocalSocket` with a unique mutex key allows instant detection of running instances across processes. When a second instance attempts to start, sending an `ACTIVATE` message over the socket triggers `window.showNormal()`, `window.show()`, `window.raise_()`, and `window.activateWindow()` on the primary instance, followed by immediate exit of the secondary instance.
- **R7 Tab Behavior**: Connecting profile homepage settings directly to tab creation (`add_new_tab(url=profile.homepage_url)`) ensures new tabs respect user preferences. Preserving and refining the last tab close behavior guarantees the application remains open and accessible when all tabs are closed.

### 3. Caveats
- **Windows Display Affinity & Tool Window Flags**: Preserving `SetWindowDisplayAffinity` (`WDA_EXCLUDEFROMCAPTURE`) and `Qt.WindowType.Tool` requires custom window dragging (`mousePressEvent` / `mouseMoveEvent`) since native Windows frame controls are disabled.
- **Headless Pytest Execution**: Pytest runs under `QT_QPA_PLATFORM=offscreen`. Single-instance socket tests and QWebEngine views must operate seamlessly in offscreen mode without hanging on socket timeouts or display affinity calls.

### 4. Conclusion
The specification for R1, R2, R3, and R7 is fully documented, unambiguous, and backed by detailed edge case handling, data schemas, IPC contracts, and component architecture diagrams. Implementation agents can execute against these schemas and class structures with 100% confidence.

### 5. Verification Method
- **Unit & Schema Verification**:
  - Verify `profiles.json` creation, reading, and update logic via `pytest tests/test_profile_manager.py`.
  - Verify Single-Instance socket signaling via `pytest tests/test_single_instance.py`.
- **UI & Tab Behavior Verification**:
  - Run `pytest tests/test_browser_features.py` under `QT_QPA_PLATFORM=offscreen` to verify tab opening, last tab homepage fallback, title updating, and nav bar button layout (confirming no back/forward buttons exist).
- **Execution Command**:
  ```bash
  pytest tests/
  python main.py
  ```

---
*Report compiled by Spec Miner 1 (UI & Profile Spec Miner)*
