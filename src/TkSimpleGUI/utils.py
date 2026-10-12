# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""TkSimpleGUI utility helpers."""

import os
import socket
import sys
import time


class Timer(object):
    """Simple stopwatch: call :meth:`start` then read :attr:`elapsed`."""

    def __init__(self):
        self._start = None
        self._stop = None

    def start(self):
        self._start = time.time()
        self._stop = None
        return self

    def stop(self):
        if self._start is not None:
            self._stop = time.time()
        return self

    @property
    def elapsed(self):
        """Seconds elapsed as a float (0 when not started)."""
        if self._start is None:
            return 0
        end = self._stop if self._stop is not None else time.time()
        return end - self._start

    @property
    def elapsed_ms(self):
        """Elapsed time in whole milliseconds."""
        return int(self.elapsed * 1000)

    def reset(self):
        self._start = None
        self._stop = None
        return self


class _ModuleTimer(object):
    """Backing state for the module level timer_start/timer_stop helpers."""

    _start = 0.0

    @classmethod
    def start(cls):
        cls._start = time.time()

    @classmethod
    def stop_ms(cls):
        return int((time.time() - cls._start) * 1000)


def timer_start():
    """Start the module level convenience timer."""
    _ModuleTimer.start()


def timer_stop():
    """Milliseconds elapsed since :func:`timer_start`."""
    return _ModuleTimer.stop_ms()


def formatted_datetime_now():
    """Current local time as ``YYYY-MM-DD HH:MM:SS``."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def rgb(red, green, blue):
    """Convert red/green/blue ints (clamped to 0-255) to a Tk color string."""
    values = []
    for component in (red, green, blue):
        component = int(component)
        if component < 0:
            component = 0
        elif component > 255:
            component = 255
        values.append(component)
    return f"#{values[0]:02x}{values[1]:02x}{values[2]:02x}"


def running_windows():
    """True when running on Windows."""
    return sys.platform.startswith("win")


def set_dpi_awareness():
    """Opt-in Windows DPI awareness for crisp rendering on high-DPI screens.

    Call once before creating the first window (a process-wide setting).
    Tries per-monitor awareness, then system awareness, then the legacy
    ``SetProcessDPIAware``. No-op on other platforms; returns True when a
    level was successfully set.
    """
    if not sys.platform.startswith("win"):
        return False
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per monitor
        return True
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # system
        return True
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return True
    except Exception:
        return False


# --- font tools (tkinter.font, needs a tk root) ---------------------------------
def _window_alive():
    """True when at least one package Window is alive."""
    from .window import Window

    return any(window._root_alive() for window in Window._open_windows)


def _font_root():
    """Borrow the first open window's tk root, or create a hidden one."""
    from .window import Window

    for window in Window._open_windows:
        if window._root_alive():
            return window.tk_root
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    return root


def font_families():
    """Sorted list of the font family names installed on this system."""
    import tkinter.font as tkfont

    root = _font_root()
    try:
        return sorted(tkfont.families(root=root))
    finally:
        # only destroy a root we created; open windows keep theirs
        if not _window_alive():
            root.destroy()


def font_measure(text, font):
    """Pixel width of ``text`` rendered in ``font`` (a name-size tuple)."""
    import tkinter.font as tkfont

    root = _font_root()
    try:
        named = tkfont.Font(root=root, font=font)
        return named.measure(str(text))
    finally:
        if not _window_alive():
            root.destroy()


def font_actual(font):
    """The resolved tk description of ``font`` as a dict (family, size, weight…)."""
    import tkinter.font as tkfont

    root = _font_root()
    try:
        named = tkfont.Font(root=root, font=font)
        return named.actual()
    finally:
        if not _window_alive():
            root.destroy()


def running_linux():
    """True when running on Linux."""
    return sys.platform.startswith("linux")


def running_mac():
    """True when running on macOS."""
    return sys.platform.startswith("darwin")


def running_trinket():
    """True when running on the Trinket environment."""
    return sys.platform.startswith("linux") and socket.gethostname().startswith("pygame-")


def running_replit():
    """True when running on Replit."""
    return "REPL_OWNER" in os.environ and sys.platform.startswith("linux")
