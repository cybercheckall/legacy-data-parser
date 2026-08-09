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

DEFAULT_APP_KEY = "OwlBrowser_SingleInstance"


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
            return f"OwlWorkspace_{hashed}_{user}"
        return f"OwlWorkspace_{clean_key}_{user}"

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

