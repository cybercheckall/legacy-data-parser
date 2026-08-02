"""
Phantom Browser — Main entrypoint.

Launches the stealth Chromium browser with global hotkey support
and desktop logging.
"""
import logging
import os
import sys

LOG_FILE = os.path.expanduser("~/Desktop/stealth_browser.log")


def setup_logging():
    """Configure application-wide file + console logging."""
    handlers = [
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=== Phantom Browser starting ===")

    # Must be imported after logging is configured
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    from browser import PhantomBrowser
    from hotkey import GlobalHotkey

    app = QApplication(sys.argv)
    app.setApplicationName("Phantom Browser")
    app.setQuitOnLastWindowClosed(True)

    # Apply global dark stylesheet
    app.setStyleSheet(
        """
        QMainWindow {
            background-color: #0a0a1a;
        }
        QWidget {
            background-color: #0a0a1a;
        }
        """
    )

    browser = PhantomBrowser()
    browser.show()

    # Global hotkey: Ctrl+Shift+B toggles visibility
    def toggle_browser():
        if browser.isVisible():
            browser.hide()
            logger.info("Browser hidden via global hotkey")
        else:
            browser.show()
            browser.activateWindow()
            browser.raise_()
            logger.info("Browser shown via global hotkey")

    hotkey = GlobalHotkey(on_toggle=toggle_browser)
    hotkey.start()

    logger.info("Phantom Browser ready — Ctrl+Shift+B to toggle visibility")

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        pass
    finally:
        hotkey.stop()
        logger.info("=== Phantom Browser stopped ===")


if __name__ == "__main__":
    main()
