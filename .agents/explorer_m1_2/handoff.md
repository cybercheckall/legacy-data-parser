# Milestone 1 Handoff Report: Single-Instance Enforcement & Application Entry Point

**Author**: Explorer 2 (Milestone 1)  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m1_2`  
**Date**: 2026-08-05  

---

## 1. Observation

### 1.1 Existing Entry Point (`main.py`)
Direct view of `main.py` (lines 38-79):
```python
app = QApplication(sys.argv)
app.setApplicationName("Phantom Browser")
app.setQuitOnLastWindowClosed(True)

# ... stylesheet setup ...

browser = PhantomBrowser()
browser.show()

# Global hotkey setup
hotkey = GlobalHotkey(on_toggle=toggle_browser)
hotkey.start()

sys.exit(app.exec())
```
- **Current Behavior**: `main.py` initializes `QApplication` and immediately creates a new `PhantomBrowser` window regardless of whether another instance is already running.
- **Defect/Gap**: Launching `python main.py` twice spawns two separate process instances and windows. Requirement **R3** (ORIGINAL_REQUEST.md lines 32-38) requires enforcing a single instance.

### 1.2 Existing Window Structure (`browser.py`)
Direct view of `PhantomBrowser` in `browser.py` (lines 58-70):
```python
class PhantomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phantom Browser")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # No taskbar icon
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.resize(1100, 750)
```
- Window visibility controls currently implemented:
  - `show()` / `hide()` toggled via `GlobalHotkey` (Ctrl+Shift+B) and `Escape` shortcut (lines 58-67, 283).
  - `showMinimized()` and `showNormal()` toggled via title bar minimize/maximize buttons (lines 117, 403).
  - `activateWindow()` and `raise_()` called in hotkey toggle (lines 64-65).

### 1.3 Requirements & Contracts
- **ORIGINAL_REQUEST.md (R3)**: Enforce single-instance behavior. If user launches second instance, bring existing window to foreground and exit second instance.
- **PROJECT.md (Interface Contract)**:
  - `SingleInstanceGuard.try_acquire(app_key: str) -> bool`: Returns `True` if primary instance, `False` if second instance (signals primary and exits).
- **SCOPE.md (M1 Scope)**:
  - `single_instance.py`: `SingleInstanceGuard` using `QLocalServer`/`QLocalSocket` for cross-process IPC.

---

## 2. Logic Chain

### 2.1 IPC Mechanism Selection (`QLocalServer` / `QLocalSocket`)
1. **Why `QLocalServer` / `QLocalSocket`?**
   - Win32 Named Mutex (`CreateMutexW`) can detect a running instance, but cannot transfer data/messages across processes without separate IPC (like WM_COPYDATA or pipes).
   - `QLocalServer` on Windows utilizes Win32 Named Pipes (`\\.\pipe\<name>`) under the hood.
   - It seamlessly integrates with PyQt6's event loop (`QApplication`), emitting Qt signals asynchronously when incoming connections arrive.
   - It allows the second process to send a message payload (e.g., `b"ACTIVATE\n"`) to the primary process before exiting.

### 2.2 Socket Naming & Isolation Convention
1. Socket names on Windows are global pipe names in `\\.\pipe\`.
2. To avoid naming collisions between different users on a multi-user machine or conflicts across standard app runs, the socket key convention should be:
   ```python
   import getpass
   DEFAULT_APP_KEY = f"PhantomWorkspace_SingleInstance_{getpass.getuser()}"
   ```
3. This guarantees user-level process isolation while remaining deterministic for instances launched by the same logged-in Windows user.

### 2.3 IPC Protocol & Instance Detection Workflow

```
+--------------------------+                  +--------------------------+
|  Second Instance (App 2) |                  | Primary Instance (App 1) |
+--------------------------+                  +--------------------------+
             |                                             |
  1. try_acquire(app_key)                                  |
             |                                             |
  2. QLocalSocket.connectToServer()                        |
             |-------------------------------------------->| (QLocalServer listening)
  3. Connection SUCCESS                                    |
             |                                 4. newConnection signal emitted
  5. socket.write(b"ACTIVATE\n")                           |
     socket.waitForBytesWritten(1000)                      |
     socket.disconnectFromServer()                         |
             |-------------------------------------------->| 6. nextPendingConnection()
  7. try_acquire() returns False                           |    Reads payload: b"ACTIVATE"
             |                                             |    Emits activated signal
  8. sys.exit(0) (Clean exit)                              |
                                                           v
                                              9. activate_window_to_front()
                                                 - show()
                                                 - showNormal() [if minimized]
                                                 - raise_()
                                                 - activateWindow()
```

#### Step-by-Step Handshake:
1. **Second Instance (`App 2`)**:
   - Instantiates `QLocalSocket`.
   - Calls `socket.connectToServer(server_name)`.
   - Waits up to 500 ms for connection: `socket.waitForConnected(500)`.
   - If state is `QLocalSocket.LocalSocketState.ConnectedState`:
     - Primary server exists!
     - Sends payload: `socket.write(b"ACTIVATE\n")`.
     - Waits for bytes written: `socket.waitForBytesWritten(1000)`.
     - Disconnects and closes socket.
     - `try_acquire()` returns `False`.
     - `main.py` logs message and exits with status `0` (`sys.exit(0)`).

2. **Primary Instance (`App 1`)**:
   - Connection attempt by App 2 triggers `server.newConnection`.
   - Primary instance slot `_on_new_connection()` executes:
     - Obtains socket: `client_socket = self._server.nextPendingConnection()`.
     - Connects `client_socket.readyRead` to `_on_ready_read(client_socket)` (or reads synchronously if available).
     - Reads payload `b"ACTIVATE\n"`.
     - Emits `guard.activated` Qt signal (`pyqtSignal()`).
     - Closes `client_socket`.
   - Connected slot on `PhantomBrowser` (`activate_window_to_front()`) executes on the GUI thread.

### 2.4 Server Cleanup & Stale Socket Handling on Windows
1. **Problem**: If the primary process crashes abruptly (e.g. killed via Task Manager, system shutdown, `SIGKILL`), the OS named pipe / socket handle might remain stale in the system namespace. Subsequent calls to `server.listen(server_name)` would fail with `AddressInUseError`.
2. **Solution**:
   - `QLocalServer.removeServer(server_name)` static method explicitly removes leftover socket/pipe entries on disk/system namespace.
   - **Algorithm in `try_acquire()`**:
     ```python
     # 1. First attempt to connect to an existing server
     socket = QLocalSocket()
     socket.connectToServer(server_name)
     if socket.waitForConnected(500):
         # Active server is live -> send signal and return False
         ...
         return False
     
     # 2. If connection failed, server is either not running or left a stale socket.
     # Force clean any stale socket before listening:
     QLocalServer.removeServer(server_name)
     
     # 3. Create server and start listening
     self._server = QLocalServer(self)
     if not self._server.listen(server_name):
         logger.error("Failed to start QLocalServer [%s]: %s", server_name, self._server.errorString())
         return False
     
     self._server.newConnection.connect(self._on_new_connection)
     return True
     ```
3. **Graceful Shutdown**:
   - Implement `cleanup()` / `close()` on `SingleInstanceGuard` to close `QLocalServer` and invoke `QLocalServer.removeServer(server_name)` during `QApplication.aboutToQuit` or `main()` `finally` block.

### 2.5 Window Foreground Activation Protocol
To guarantee the primary window is brought to top across all states (hidden, minimized, covered by other windows):

```python
def activate_window_to_front(self):
    """Bring browser window to foreground and give focus."""
    # 1. Ensure window is visible (unhide if hidden by Esc or hotkey)
    if not self.isVisible():
        self.show()
    
    # 2. Restore if minimized
    if self.isMinimized():
        self.showNormal()
        
    # 3. Bring to top of Qt window stack & request focus
    self.raise_()
    self.activateWindow()
    
    # 4. Windows OS Win32 Fallback (Optional extra boost if OS focus lock blocks activateWindow)
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            logger.debug("Win32 SetForegroundWindow failed: %s", e)
```

---

## 3. Caveats

1. **Qt Offscreen Mode in Pytest (`QT_QPA_PLATFORM=offscreen`)**:
   - `QLocalServer` and `QLocalSocket` rely on OS IPC mechanisms (named pipes / domain sockets) and do NOT require a GUI display server. They function identically under headless/offscreen pytest environments.
2. **Win32 Foreground Lock Restrictions**:
   - Windows restricts background processes from stealing focus (`SetForegroundWindow`). Since the second process is launched directly by the user, Windows grants foreground activation permission to the process group, allowing `activateWindow()` / `SetForegroundWindow()` to successfully bring the primary window to the front.
3. **Multi-Instance Profiles (Future Extension)**:
   - For Milestone 1, single-instance protection is application-wide. If future requirements allow running multiple profiles in separate process instances, `app_key` can be extended to include `profile_id` (e.g. `f"PhantomWorkspace_{profile_id}"`).

---

## 4. Conclusion & Recommended Implementation Plan

### 4.1 Class Design for `single_instance.py`

```python
"""
single_instance.py — Single Instance Enforcement via QLocalServer / QLocalSocket IPC.
"""
import getpass
import logging
import sys
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

logger = logging.getLogger(__name__)


class SingleInstanceGuard(QObject):
    """
    Enforces a single application instance per user using Qt Local Server IPC.
    Emits `activated` signal when a second instance attempts to launch.
    """
    activated = pyqtSignal()

    def __init__(self, app_key: str = None, parent: QObject = None):
        super().__init__(parent)
        user = getpass.getuser()
        base_key = app_key or "PhantomWorkspace_SingleInstance"
        self._server_name = f"{base_key}_{user}"
        self._server = None

    def try_acquire(()) -> bool:
        """
        Attempts to acquire single instance lock.
        Returns True if primary instance.
        Returns False if second instance (sends activation payload and disconnects).
        """
        # Attempt connection to existing instance
        socket = QLocalSocket(self)
        socket.connectToServer(self._server_name)
        if socket.waitForConnected(500):
            logger.info("Connected to existing primary instance [%s]", self._server_name)
            socket.write(b"ACTIVATE\n")
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            socket.close()
            return False

        # No active instance found — clean stale socket and listen
        QLocalServer.removeServer(self._server_name)
        self._server = QLocalServer(self)
        if not self._server.listen(self._server_name):
            logger.error("Could not start QLocalServer [%s]: %s", self._server_name, self._server.errorString())
            return False

        self._server.newConnection.connect(self._on_new_connection)
        logger.info("Primary instance acquired lock [%s]", self._server_name)
        return True

    def _on_new_connection(self):
        client = self._server.nextPendingConnection()
        if not client:
            return
        if client.waitForReadyRead(500):
            data = client.readAll().data()
            if b"ACTIVATE" in data:
                logger.info("Activation payload received from second instance")
                self.activated.emit()
        client.disconnectFromServer()
        client.close()

    def cleanup(self):
        """Close server and remove local socket."""
        if self._server:
            self._server.close()
            QLocalServer.removeServer(self._server_name)
            self._server = None
```

### 4.2 Integration in `main.py`

```python
from single_instance import SingleInstanceGuard

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Phantom Browser")
    
    # 1. Single Instance Check
    guard = SingleInstanceGuard()
    if not guard.try_acquire():
        logger.info("Second instance launched. Signaled primary instance and exiting with code 0.")
        sys.exit(0)
        
    app.aboutToQuit.connect(guard.cleanup)
    
    # 2. Window Instantiation
    browser = PhantomBrowser()
    guard.activated.connect(browser.activate_window_to_front)
    browser.show()
    
    # ... setup hotkeys & exec ...
```

---

## 5. Verification Method

### 5.1 Automated Unit & Integration Tests (`tests/test_single_instance.py`)
Run command:
```powershell
pytest tests/test_single_instance.py -v
```

#### Test Cases to Implement:
1. **`test_primary_instance_acquisition`**:
   - Initialize `guard1 = SingleInstanceGuard(app_key="TestKey_Primary")`.
   - Call `guard1.try_acquire()`. Expect `True`.
   - Clean up `guard1.cleanup()`.
2. **`test_second_instance_rejection_and_signal`**:
   - Initialize `guard1 = SingleInstanceGuard(app_key="TestKey_IPC")`.
   - Assert `guard1.try_acquire()` is `True`.
   - Set up Qt signal spy / flag on `guard1.activated`.
   - Initialize `guard2 = SingleInstanceGuard(app_key="TestKey_IPC")`.
   - Assert `guard2.try_acquire()` is `False`.
   - Process events / wait for signal emission on `guard1`.
   - Assert `guard1.activated` was triggered.
   - Clean up both guards.
3. **`test_stale_socket_recovery`**:
   - Create a dummy socket or simulate crash by leaving `QLocalServer.removeServer("TestKey_Stale")` without closing cleanly.
   - Call `SingleInstanceGuard(app_key="TestKey_Stale").try_acquire()`.
   - Assert returns `True` after clearing stale server.
4. **`test_window_activation_method`**:
   - Create `PhantomBrowser` instance.
   - Minimize window / hide window.
   - Call `browser.activate_window_to_front()`.
   - Assert `browser.isVisible()` is `True`.

### 5.2 Full Test Suite Verification
Run all existing and new tests:
```powershell
pytest tests/ -v
```
Ensure 100% pass rate.
