"""
diagnose_pipe.py - Diagnose QLocalServer/QLocalSocket behavior on Windows.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from single_instance import SingleInstanceGuard

def test_pipe_diagnostics():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Test 1: Send corrupt bytes, release server, then try acquiring fresh guard on another key
    key1 = "diag_key_1"
    g1 = SingleInstanceGuard(app_key=key1)
    print("g1 acquire:", g1.try_acquire(key1))
    
    # Connect socket and send corrupt bytes
    sock = QLocalSocket()
    sock.connectToServer(g1._get_server_name(key1))
    if sock.waitForConnected(500):
        sock.write(b"\x00\xff\xfe\xfd\x00")
        sock.flush()
        sock.waitForBytesWritten(500)
        sock.disconnectFromServer()
        sock.close()
    
    QCoreApplication.processEvents()
    g1.release()
    QCoreApplication.processEvents()
    
    # Test 2: Next key acquire
    key2 = "diag_key_2"
    g2 = SingleInstanceGuard(app_key=key2)
    res2 = g2.try_acquire(key2)
    print("g2 acquire:", res2)
    g2.release()
    QCoreApplication.processEvents()

if __name__ == "__main__":
    test_pipe_diagnostics()
