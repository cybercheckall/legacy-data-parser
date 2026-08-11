"""
main.py - Phantom Workspace Application Entrypoint.

Launches Phantom Workspace with single-instance enforcement, modern dark glassmorphic styling,
and profile selector startup flow.
"""

import logging
import os
import sys

LOG_FILE = os.path.expanduser("~/Desktop/stealth_browser.log")
APP_VERSION = "0.9.0"


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
    logger.info("=== Owl starting ===")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    from PyQt6.QtGui import QIcon

    from browser import OwlBrowser, PhantomBrowser
    from single_instance import SingleInstanceGuard
    from styles import DARK_GLASS_STYLE

    app = QApplication(sys.argv)
    app.setApplicationName("Owl")
    app.setQuitOnLastWindowClosed(True)

    icon_path = os.path.join(os.path.dirname(__file__), "owl_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(os.path.dirname(__file__), "owl_icon.jpg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Enforce single instance application guard
    guard = SingleInstanceGuard("OwlBrowserApp")
    if not guard.try_acquire():
        logger.info("Secondary instance detected. Primary instance notified; exiting with code 0.")
        sys.exit(0)

    app.aboutToQuit.connect(guard.release)

    # Apply modern dark glassmorphism stylesheet application-wide
    app.setStyleSheet(DARK_GLASS_STYLE)

    browser = OwlBrowser(show_profile_selector_on_start=True)
    guard.activation_requested.connect(browser.activate_window_to_front)
    if hasattr(guard, "activated"):
        guard.activated.connect(browser.activate_window_to_front)

    import updater
    logger.info(f"Checking for updates. Current version: {APP_VERSION}")
    updater.check_for_updates(APP_VERSION, parent_widget=browser)

    browser.show()
    logger.info("Owl ready")

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        pass
    finally:
        guard.release()
        logger.info("=== Owl stopped ===")


if __name__ == "__main__":
    main()
