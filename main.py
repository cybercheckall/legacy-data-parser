"""
main.py — Owl application entrypoint.

Launches Owl with single-instance enforcement, workspace styling,
and profile selector startup flow.
"""

import logging
import os
import sys

from owl.paths import BRAND_DIR, PROJECT_ROOT

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
    logger.info("=== Owl starting ===")

    # Ensure project root is importable when launched as a script
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon

    from owl.workspace.main_window import OwlBrowser
    from owl.stealth.display_affinity import apply_app_stealth_policy
    from owl.stealth.single_instance import SingleInstanceGuard
    from owl.design.stylesheet import DARK_GLASS_STYLE

    app = QApplication(sys.argv)
    app.setApplicationName("Owl")
    app.setQuitOnLastWindowClosed(True)
    apply_app_stealth_policy()

    icon_path = os.path.join(BRAND_DIR, "owl_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(BRAND_DIR, "owl_icon.jpg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    guard = SingleInstanceGuard("OwlBrowserApp")
    if not guard.try_acquire():
        logger.info("Secondary instance detected. Primary instance notified; exiting with code 0.")
        sys.exit(0)

    app.aboutToQuit.connect(guard.release)

    app.setStyleSheet(DARK_GLASS_STYLE)

    browser = OwlBrowser(show_profile_selector_on_start=True)
    guard.activation_requested.connect(browser.activate_window_to_front)
    if hasattr(guard, "activated"):
        guard.activated.connect(browser.activate_window_to_front)

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
