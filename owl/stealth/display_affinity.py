"""
Display affinity / screen-capture exclusion.

Windows: SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)
macOS:   NSWindow setSharingType:NSWindowSharingNone
"""
from __future__ import annotations

import ctypes
import logging
import sys

logger = logging.getLogger(__name__)

WDA_EXCLUDEFROMCAPTURE = 0x00000011
NS_WINDOW_SHARING_NONE = 0
NS_APPLICATION_ACTIVATION_POLICY_ACCESSORY = 1


def apply_display_affinity(hwnd: int) -> bool:
    """Exclude the given native window handle from screen capture when supported."""
    if not hwnd or hwnd < 0:
        logger.warning("Invalid window handle: %s", hwnd)
        return False

    if sys.platform == "win32":
        return _apply_windows(hwnd)
    if sys.platform == "darwin":
        return _apply_macos(hwnd)

    logger.warning("Screen-capture exclusion is not supported on %s", sys.platform)
    return False


def apply_app_stealth_policy() -> bool:
    """
    Apply process-level stealth behavior where the OS supports it.

    On macOS, switch to accessory activation policy so the app does not
    appear in the Dock (analogous to Windows Tool-window / no-taskbar).
    """
    if sys.platform == "darwin":
        return _set_macos_activation_policy_accessory()
    return True


def set_stealth_affinity(hwnd: int) -> bool:
    """Alias used by legacy tests and compatibility shims."""
    return apply_display_affinity(hwnd)


def _apply_windows(hwnd: int) -> bool:
    try:
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        result = user32.SetWindowDisplayAffinity(
            wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE
        )
        if result:
            logger.info(
                "Applied Windows display affinity 0x%X to HWND %s",
                WDA_EXCLUDEFROMCAPTURE,
                hwnd,
            )
            return True

        error_code = ctypes.GetLastError()
        logger.warning(
            "SetWindowDisplayAffinity failed for HWND %s, error code: %s",
            hwnd,
            error_code,
        )
        return False
    except Exception as exc:
        logger.error("Exception applying Windows display affinity: %s", exc)
        return False


def _apply_macos(nsview_ptr: int) -> bool:
    """
    Set NSWindow.sharingType = NSWindowSharingNone for the Qt NSView's window.

    On macOS, QWidget.winId() returns an NSView pointer.
    """
    try:
        libobjc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")

        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        libobjc.sel_registerName.restype = ctypes.c_void_p

        sel_window = libobjc.sel_registerName(b"window")
        sel_set_sharing_type = libobjc.sel_registerName(b"setSharingType:")

        objc_msg_send = libobjc.objc_msgSend
        objc_msg_send.restype = ctypes.c_void_p
        objc_msg_send.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        ns_window = objc_msg_send(ctypes.c_void_p(nsview_ptr), sel_window)
        if not ns_window:
            logger.warning("macOS NSView %s has no NSWindow yet", nsview_ptr)
            return False

        set_sharing = libobjc.objc_msgSend
        set_sharing.restype = None
        set_sharing.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
        set_sharing(
            ctypes.c_void_p(ns_window),
            sel_set_sharing_type,
            NS_WINDOW_SHARING_NONE,
        )

        logger.info(
            "Applied macOS NSWindowSharingNone to NSWindow from NSView %s",
            nsview_ptr,
        )
        return True
    except Exception as exc:
        logger.error("Exception applying macOS sharing type: %s", exc)
        return False


def _set_macos_activation_policy_accessory() -> bool:
    try:
        libobjc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")

        libobjc.objc_getClass.argtypes = [ctypes.c_char_p]
        libobjc.objc_getClass.restype = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        libobjc.sel_registerName.restype = ctypes.c_void_p

        ns_application = libobjc.objc_getClass(b"NSApplication")
        if not ns_application:
            return False

        sel_shared = libobjc.sel_registerName(b"sharedApplication")
        sel_set_policy = libobjc.sel_registerName(b"setActivationPolicy:")

        msg = libobjc.objc_msgSend
        msg.restype = ctypes.c_void_p
        msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        ns_app = msg(ns_application, sel_shared)
        if not ns_app:
            return False

        set_policy = libobjc.objc_msgSend
        set_policy.restype = ctypes.c_bool
        set_policy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
        ok = bool(
            set_policy(
                ctypes.c_void_p(ns_app),
                sel_set_policy,
                NS_APPLICATION_ACTIVATION_POLICY_ACCESSORY,
            )
        )
        if ok:
            logger.info("macOS activation policy set to accessory (hidden from Dock)")
        else:
            logger.warning("Failed to set macOS activation policy to accessory")
        return ok
    except Exception as exc:
        logger.error("Exception setting macOS activation policy: %s", exc)
        return False
