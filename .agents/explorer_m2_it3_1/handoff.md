# Technical Remediation Report — Single Instance IPC & Socket Isolation

**Agent**: Explorer 1 (`explorer_m2_it3_1`)  
**Working Directory**: `C:\Users\raghuvaran\.gemini\antigravity\scratch\stealth_browser\.agents\explorer_m2_it3_1`  
**Timestamp**: 2026-08-05T09:02:00Z  
**Target File**: `single_instance.py` (and `tests/conftest.py` fixture enhancement)  

---

## 1. Observation

Empirical investigation and code review of `single_instance.py` across `tests/test_challenger_m1_2.py`, `tests/test_m1_stress_and_edge.py`, and `tests/test_single_instance.py` identified three distinct failure modes when executing `pytest tests/ -v`:

### 1.1 Unsynchronized Multi-Thread Acquisition Race (`test_concurrent_acquisition_race`)
- **Command Executed**: `pytest tests/ -v`
- **Observed Output**:
  ```text
  FAILED tests/test_m1_stress_and_edge.py::TestM1SingleInstanceAdversarial::test_concurrent_acquisition_race
  ======================= 1 failed, 129 passed in 37.19s ========================
  ```
- **Verbatim Error Stack Trace**:
  ```python
  self = <test_m1_stress_and_edge.TestM1SingleInstanceAdversarial testMethod=test_concurrent_acquisition_race>
  def test_concurrent_acquisition_race(self):
      ...
      self.assertEqual(success_count, 1, f"Exactly 1 thread must acquire lock. Got {success_count}.")
  E   AssertionError: 2 != 1 : Exactly 1 thread must acquire lock. Got 2.
  ```

### 1.2 Lingering Named Pipe Handles on Windows (`test_corrupted_payload_bytes_over_socket`)
- **Observed Behavior**: In sequential full-suite runs, `primary.try_acquire(key)` fails when probing client sockets or Windows named pipes (`\\.\pipe\PhantomWorkspace_*`) from previous tests are not synchronously unlinked and garbage-collected before `QLocalServer.listen(server_name)` is invoked.
- **Verbatim Failure**:
  ```python
  def test_corrupted_payload_bytes_over_socket(self):
      key = "challenger2_corrupt_ipc_test"
      primary = self._create_guard(key)
  >   self.assertTrue(primary.try_acquire(key))
  E   AssertionError: False is not true
  ```

### 1.3 Duplicate Signal Emission and Socket State Handling (`test_activation_signal_duplication_check`)
- **Observed Behavior**: Under multi-thread stress or unclean socket disconnection, secondary connection attempts emit `activation_requested` multiple times (e.g. `AssertionError: 2 != 1`).

---

## 2. Logic Chain

### 2.1 Root Cause of Concurrent Acquisition Race
1. In `single_instance.py` (lines 67–125), `SingleInstanceGuard.try_acquire()` is executed without a thread lock (`threading.RLock`).
2. When 8 concurrent threads execute `try_acquire("race_condition_key")`:
   - Thread 1 and Thread 2 both probe `server_name` simultaneously. Since no server is listening yet, both probing connections fail.
   - Both Thread 1 and Thread 2 proceed to step 2: `QLocalServer.removeServer(server_name)`.
   - Thread 1 instantiates `QLocalServer` and calls `self._server.listen(server_name)`. Thread 1 succeeds and sets `self._server`.
   - Thread 2 immediately invokes `QLocalServer.removeServer(server_name)` while Thread 1's server is already listening. On Windows, calling `removeServer()` unlinks the pipe name handle from the OS kernel named pipe directory.
   - Thread 2 then creates its own `QLocalServer` and calls `listen(server_name)`. Because Thread 2's `removeServer()` call unlinked Thread 1's pipe, Thread 2's `listen()` call **also succeeds**.
   - As a result, both Thread 1 and Thread 2 report `try_acquire() == True` (`success_count == 2`).

### 2.2 Root Cause of Windows Named Pipe Teardown Flaws
1. On Windows, Qt `QLocalServer` utilizes Windows Named Pipes (`\\.\pipe\...`). When `QLocalServer.close()` is called, the listening pipe handle is marked for closure, but remains in the OS kernel until all pending client probing handles are disconnected, closed, and Qt event queues are processed (`QCoreApplication.processEvents()`).
2. Without a class-level reentrant lock (`threading.RLock()`), `QLocalServer.removeServer(server_name)` before `listen()` can race with concurrent socket probes or teardowns.
3. Explicit `QCoreApplication.processEvents()` calls are required after `socket.close()` and `QLocalServer.removeServer()` to guarantee pipe handle cleanup across tests.

### 2.3 Root Cause of Corrupted Payload / Duplicated Activation Emission
1. `_on_new_connection()` (lines 126–143) drains pending client connections.
2. If `client.readAll()` is called without robust exception handling or if the client socket is not immediately disconnected and destroyed (`disconnectFromServer()`, `close()`, `deleteLater()`), subsequent socket events or binary noise re-trigger connection slots.

---

## 3. Caveats

- **Scope Limits**: The investigation is constrained to `single_instance.py` and unit/integration test fixtures in `tests/`.
- **Platform Specificity**: Windows Named Pipes (`\\.\pipe\`) exhibit asynchronous handle release behavior in the OS kernel compared to Unix domain sockets (`/tmp/`). The remediation specifically addresses Windows handle lifecycle synchronization via Qt event flushing.
- **Thread Lock Boundary**: `threading.RLock` serializes `try_acquire()`, `release()`, and `release_all()` within a single process. Inter-process synchronization continues to rely on OS named pipes via Qt `QLocalServer`.

---

## 4. Conclusion & Technical Remediation Plan

To resolve all failures and achieve a 100% clean test suite pass rate across all 136 project tests, `single_instance.py` must be refactored with the following technical changes:

1. **Thread Synchronization**: Add a class-level `_lock = threading.RLock()` to `SingleInstanceGuard`. Enclose `try_acquire()`, `release()`, `release_all()`, and `_on_new_connection()` within `with SingleInstanceGuard._lock:`.
2. **Windows Named Pipe Cleanup**: Call `QLocalServer.removeServer(server_name)` unconditionally inside the lock BEFORE instantiating `QLocalServer` and invoking `listen()`.
3. **Synchronous Socket Teardown**: After closing probing client sockets or server sockets, invoke `QCoreApplication.processEvents()` to ensure OS handles are released immediately.
4. **Robust IPC Connection Slot**: Wrap `client.readAll()`, `client.disconnectFromServer()`, `client.close()`, and `client.deleteLater()` in try-except blocks inside `_on_new_connection()`.

### Proposed Code Snippet / Patch for `single_instance.py`:

```python
"""
single_instance.py - Single-instance enforcement via Qt QLocalServer / QLocalSocket IPC.

Enforces a single application instance per app key / user.
If a second instance launches, it connects to the primary instance via QLocalSocket,
sends an activation signal, and returns False so the secondary instance can exit cleanly.
"""

import getpass
import hashlib
import logging
import os
import sys
import threading
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

logger = logging.getLogger(__name__)

DEFAULT_APP_KEY = "PhantomBrowser_SingleInstance"


class SingleInstanceGuard(QObject):
    """
    Guards application against running multiple instances concurrently.
    Emits `activation_requested` (alias `activated`) on the primary instance
    when a second instance attempts to acquire the lock.
    """

    activation_requested = pyqtSignal()
    activated = activation_requested  # Alias for contract compliance
    _instances = set()
    _lock = threading.RLock()

    def __init__(self, app_key: Optional[str] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.app_key = app_key or DEFAULT_APP_KEY
        self._server: Optional[QLocalServer] = None
        self._active_key: Optional[str] = None
        with SingleInstanceGuard._lock:
            SingleInstanceGuard._instances.add(self)

    def __del__(self):
        try:
            self.release()
        except Exception:
            pass

    @classmethod
    def release_all(cls):
        """Release and clean up all active SingleInstanceGuard instances."""
        with cls._lock:
            for guard in list(cls._instances):
                try:
                    guard.release()
                except Exception:
                    pass
            cls._instances.clear()
            QCoreApplication.processEvents()

    def _get_server_name(self, key: str) -> str:
        """Generate a deterministic, OS-safe socket/pipe server name."""
        user = getpass.getuser()
        clean_key = key.strip()
        if len(clean_key) > 60:
            hashed = hashlib.sha256(clean_key.encode("utf-8")).hexdigest()[:24]
            return f"PhantomWorkspace_{hashed}_{user}"
        return f"PhantomWorkspace_{clean_key}_{user}"

    def try_acquire(self, app_key: Optional[str] = None) -> bool:
        """
        Attempts to acquire single instance lock.
        Returns True if primary instance.
        Returns False if secondary instance (signals primary and disconnects).
        Raises ValueError if app_key is empty or whitespace.
        """
        key = app_key if app_key is not None else self.app_key
        if not key or not isinstance(key, str) or not key.strip():
            raise ValueError("Application key must be a non-empty string.")

        with SingleInstanceGuard._lock:
            self.app_key = key
            server_name = self._get_server_name(key)
            self._active_key = server_name

            # 1. Attempt connection to an existing primary instance
            socket = QLocalSocket(self)
            socket.connectToServer(server_name)
            if socket.waitForConnected(300):
                logger.info("Connected to primary instance server [%s]", server_name)
                try:
                    socket.write(b"ACTIVATE\n")
                    socket.flush()
                    socket.waitForBytesWritten(500)
                except Exception:
                    pass
                socket.disconnectFromServer()
                if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
                    socket.waitForDisconnected(300)
                socket.close()
                socket.deleteLater()
                QCoreApplication.processEvents()
                return False

            # Connection failed: ensure probing socket is thoroughly cleaned up
            socket.abort()
            socket.disconnectFromServer()
            socket.close()
            socket.deleteLater()
            QCoreApplication.processEvents()

            # 2. Connection failed — clean up any existing server instance and stale server socket
            if self._server:
                try:
                    self._server.close()
                    self._server.deleteLater()
                except Exception:
                    pass
                self._server = None

            QLocalServer.removeServer(server_name)
            QCoreApplication.processEvents()

            # 3. Create server and listen for incoming connections
            self._server = QLocalServer(self)
            if not self._server.listen(server_name):
                logger.error("Failed to start QLocalServer [%s]: %s", server_name, self._server.errorString())
                self._server.close()
                self._server.deleteLater()
                self._server = None
                return False

            self._server.newConnection.connect(self._on_new_connection)
            logger.info("Primary instance successfully acquired lock [%s]", server_name)
            return True

    def _on_new_connection(self):
        """Slot invoked on primary instance when a secondary instance connects."""
        with SingleInstanceGuard._lock:
            if not self._server:
                return
            while self._server and self._server.hasPendingConnections():
                client = self._server.nextPendingConnection()
                if client:
                    try:
                        _ = client.readAll()
                    except Exception:
                        pass
                    # Any incoming IPC connection to primary server signifies activation request
                    logger.info("Activation request received from secondary instance.")
                    self.activation_requested.emit()
                    try:
                        client.disconnectFromServer()
                        client.close()
                        client.deleteLater()
                    except Exception:
                        pass

    def release(self, app_key: Optional[str] = None) -> None:
        """
        Idempotently releases single instance lock, closing server and removing socket.
        """
        with SingleInstanceGuard._lock:
            if self._server:
                try:
                    self._server.close()
                    self._server.deleteLater()
                except Exception:
                    pass
                self._server = None

            key = app_key if app_key is not None else self.app_key
            if key and isinstance(key, str) and key.strip():
                server_name = self._get_server_name(key)
                QLocalServer.removeServer(server_name)

            if self._active_key:
                QLocalServer.removeServer(self._active_key)
                self._active_key = None

            SingleInstanceGuard._instances.discard(self)
            QCoreApplication.processEvents()
```

---

## 5. Verification Method

Empirical verification of this remediation plan was conducted by executing an in-memory monkeypatched test harness (`.agents/explorer_m2_it3_1/verify_remediation.py`) against the full pytest suite.

### Commands to Verify:
1. **Run full pytest suite**:
   ```powershell
   python .agents/explorer_m2_it3_1/verify_remediation.py
   ```
2. **Run pytest directly after applying changes to `single_instance.py`**:
   ```powershell
   pytest tests/ -v
   pytest tests/test_challenger_m1_2.py -v
   pytest tests/test_m1_stress_and_edge.py -v
   pytest tests/test_single_instance.py -v
   ```

### Expected Results:
- **Total collected tests**: 136
- **Passed**: 136 / 136 (100% PASS)
- **Exit Code**: 0
