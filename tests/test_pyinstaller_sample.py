import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

def test_pyinstaller_sample():
    app = QApplication.instance() or QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("PyInstaller Test")
    view = QWebEngineView(win)
    win.setCentralWidget(view)
    win.resize(400, 300)
    win.show()
    
    hwnd = int(win.winId())
    res = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011) if sys.platform == "win32" else 1
    assert hwnd > 0 or res >= 0
    
    app.processEvents()
    win.close()
    win.deleteLater()

if __name__ == "__main__":
    test_pyinstaller_sample()

