"""
Global hotkey listener for toggling the Phantom Browser visibility.
Uses pynput for system-wide keyboard monitoring.
"""
import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class GlobalHotkey:
    """Listens for Ctrl+Shift+B globally to toggle browser visibility."""

    def __init__(self, on_toggle: Callable):
        self._on_toggle = on_toggle
        self._listener = None
        self._pressed_keys = set()
        self._target_keys = {"ctrl", "shift", "b"}
        self._running = False

    def start(self):
        """Start the global hotkey listener in a background thread."""
        try:
            from pynput import keyboard

            def on_press(key):
                try:
                    if hasattr(key, 'char') and key.char:
                        self._pressed_keys.add(key.char.lower())
                    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self._pressed_keys.add("ctrl")
                    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                        self._pressed_keys.add("shift")
                except AttributeError:
                    pass

                if self._target_keys.issubset(self._pressed_keys):
                    self._pressed_keys.clear()
                    logger.info("Global hotkey Ctrl+Shift+B triggered")
                    self._on_toggle()

            def on_release(key):
                try:
                    if hasattr(key, 'char') and key.char:
                        self._pressed_keys.discard(key.char.lower())
                    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                        self._pressed_keys.discard("ctrl")
                    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                        self._pressed_keys.discard("shift")
                except AttributeError:
                    pass

            self._listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release,
            )
            self._listener.daemon = True
            self._listener.start()
            self._running = True
            logger.info("Global hotkey listener started (Ctrl+Shift+B)")

        except ImportError:
            logger.warning("pynput not available — global hotkey disabled")
        except Exception as e:
            logger.error("Failed to start global hotkey listener: %s", e)

    def stop(self):
        """Stop the global hotkey listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None
            self._running = False
            logger.info("Global hotkey listener stopped")
