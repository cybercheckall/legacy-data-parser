# BRIEFING — 2026-08-05T01:08:49Z

## Mission
Investigate application entry point, Qt window structure, and single-instance IPC requirements (SingleInstanceGuard) for Milestone 1. Produce detailed specifications and implementation strategy in handoff.md.

## 🔒 My Identity
- Archetype: Explorer
- Roles: Explorer 2 (Milestone 1)
- Working directory: C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2
- Original parent: bc9ab4a1-e6aa-4e44-aeee-d8e57ca8c362
- Milestone: M1 (Profile System & Single Instance)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement application source code changes.
- Focus on `single_instance.py` design, Qt window structure, QLocalServer/QLocalSocket IPC protocol, Windows stale socket cleanup, and window activation logic.
- Deliver findings and implementation plan in `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2\handoff.md`.

## Current Parent
- Conversation ID: bc9ab4a1-e6aa-4e44-aeee-d8e57ca8c362
- Updated: 2026-08-05T01:08:49Z

## Investigation State
- **Explored paths**: `main.py`, `browser.py`, `PROJECT.md`, `SCOPE.md`, `ORIGINAL_REQUEST.md`, `tests/conftest.py`
- **Key findings**:
  - `main.py` entry point needs `SingleInstanceGuard` check before creating main window and starting Qt event loop.
  - `PhantomBrowser` (`browser.py`) window flags include `Window`, `WindowStaysOnTopHint`, `Tool` (no taskbar icon). Window activation method `activate_window_to_front()` should call `show()`, `showNormal()` if minimized, `raise_()`, `activateWindow()`, and optional Win32 `SetForegroundWindow`.
  - `SingleInstanceGuard` uses `QLocalServer`/`QLocalSocket` named pipes on Windows.
  - Socket key: `PhantomWorkspace_SingleInstance_<username>` guarantees per-user isolation.
  - Stale sockets are cleaned via `QLocalServer.removeServer(name)` if `waitForConnected(500)` fails.
  - Second instance sends `b"ACTIVATE\n"`, receives ACK/disconnects, returns `False`, causing `main.py` to `sys.exit(0)`.
- **Unexplored areas**: None for M1 Single Instance scope.

## Key Decisions Made
- Designed `SingleInstanceGuard` class API, signal/slot wiring, cleanup hooks, and pytest strategy.

## Artifact Index
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2\DISPATCH.md` — Task log
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2\BRIEFING.md` — Working memory index
- `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2\handoff.md` — 5-Component M1 Single Instance Report & Implementation Specification
