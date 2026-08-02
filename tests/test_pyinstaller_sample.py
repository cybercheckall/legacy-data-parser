import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView

def main():
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("PyInstaller Test")
    view = QWebEngineView(win)
    win.setCentralWidget(view)
    win.resize(400, 300)
    win.show()
    
    hwnd = int(win.winId())
    res = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
    print(f"Test App Loaded! HWND: {hwnd}, SetAffinity: {res}")
    
    # Process events for a moment then quit
    app.processEvents()
    print("Test finished successfully!")

if __name__ == "__main__":
    main()
