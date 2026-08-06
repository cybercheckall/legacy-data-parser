"""
verify_remediation.py - Verification script to test proposed SingleInstanceGuard remediation.
Monkeys-patches single_instance module in-memory and runs pytest suite.
"""

import sys
import os
import unittest
import pytest

sys.path.insert(0, os.path.abspath("."))

# Target implementation to verify
import single_instance
from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
import getpass
import hashlib
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

class RefactoredSingleInstanceGuard(QObject):
    activation_requested = pyqtSignal()
    activated = activation_requested
    _instances = set()
    _lock = threading.RLock()

    def __init__(self, app_key: Optional[str] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.app_key = app_key or single_instance.DEFAULT_APP_KEY
        self._server: Optional[QLocalServer] = None
        self._active_key: Optional[str] = None
        with RefactoredSingleInstanceGuard._lock:
            RefactoredSingleInstanceGuard._instances.add(self)

    def __del__(self):
        try:
            self.release()
        except Exception:
            pass

    @classmethod
    def release_all(cls):
        with cls._lock:
            for guard in list(cls._instances):
                try:
                    guard.release()
                except Exception:
                    pass
            cls._instances.clear()

    def _get_server_name(self, key: str) -> str:
        user = getpass.getuser()
        clean_key = key.strip()
        if len(clean_key) > 60:
            hashed = hashlib.sha256(clean_key.encode("utf-8")).hexdigest()[:24]
            return f"PhantomWorkspace_{hashed}_{user}"
        return f"PhantomWorkspace_{clean_key}_{user}"

    def try_acquire(self, app_key: Optional[str] = None) -> bool:
        key = app_key if app_key is not None else self.app_key
        if not key or not isinstance(key, str) or not key.strip():
            raise ValueError("Application key must be a non-empty string.")

        with RefactoredSingleInstanceGuard._lock:
            self.app_key = key
            server_name = self._get_server_name(key)
            self._active_key = server_name

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

            socket.abort()
            socket.disconnectFromServer()
            socket.close()
            socket.deleteLater()
            QCoreApplication.processEvents()

            if self._server:
                try:
                    self._server.close()
                    self._server.deleteLater()
                except Exception:
                    pass
                self._server = None

            QLocalServer.removeServer(server_name)
            QCoreApplication.processEvents()

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
        with RefactoredSingleInstanceGuard._lock:
            if not self._server:
                return
            while self._server and self._server.hasPendingConnections():
                client = self._server.nextPendingConnection()
                if client:
                    try:
                        _ = client.readAll()
                    except Exception:
                        pass
                    logger.info("Activation request received from secondary instance.")
                    self.activation_requested.emit()
                    try:
                        client.disconnectFromServer()
                        client.close()
                        client.deleteLater()
                    except Exception:
                        pass

    def release(self, app_key: Optional[str] = None) -> None:
        with RefactoredSingleInstanceGuard._lock:
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

            RefactoredSingleInstanceGuard._instances.discard(self)
            QCoreApplication.processEvents()


# Apply patch to single_instance module
single_instance.SingleInstanceGuard = RefactoredSingleInstanceGuard

if __name__ == "__main__":
    ret = pytest.main(["tests/", "-v"])
    sys.exit(ret)
