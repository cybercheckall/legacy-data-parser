"""
Display affinity module — applies Windows SetWindowDisplayAffinity
to make a window invisible to screen capture/sharing software.
"""
import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger(__name__)

WDA_EXCLUDEFROMCAPTURE = 0x00000011


def apply_display_affinity(hwnd: int) -> bool:
    """Apply WDA_EXCLUDEFROMCAPTURE to the given HWND."""
    if not hwnd or hwnd < 0:
        logger.warning("Invalid HWND: %s", hwnd)
        return False

    try:
        user32 = ctypes.windll.user32
        result = user32.SetWindowDisplayAffinity(
            wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE
        )
        if result:
            logger.info(
                "Successfully applied display affinity 0x%X to HWND %s",
                WDA_EXCLUDEFROMCAPTURE, hwnd
            )
            return True
        else:
            error_code = ctypes.GetLastError()
            logger.warning(
                "SetWindowDisplayAffinity failed for HWND %s, error code: %s",
                hwnd, error_code
            )
            return False
    except Exception as e:
        logger.error("Exception applying display affinity: %s", e)
        return False
