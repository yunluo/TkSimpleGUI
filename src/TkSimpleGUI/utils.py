#!/usr/bin/env python3
"""TkSimpleGUI utility helpers.

A grab-bag of small standalone utilities the package itself leans on:
``Timer`` (stopwatch), platform probes, font helpers, rgb conversion, etc.
Everything is re-exported from the package root.
"""

from typing import Any, Optional
import sys
import time
from .constants import FontSpec


class Timer:
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


def formatted_datetime_now():
    """Current local time as ``YYYY-MM-DD HH:MM:SS``."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def rgb(red: Any, green: Any, blue: Any):
    """Convert red/green/blue ints (clamped to 0-255) to a Tk color string."""
    values = []
    for component in (red, green, blue):
        values.append(max(0, min(255, int(component))))
    return f"#{values[0]:02x}{values[1]:02x}{values[2]:02x}"


def running_windows():
    """True when running on Windows."""
    return sys.platform.startswith("win")


def _hresult_awareness_set(result: int) -> bool:
    """True for S_OK or E_ACCESSDENIED (an awareness level is already set).

    ctypes returns the HRESULT as a plain c_int without raising, so failure
    codes must be checked explicitly; E_ACCESSDENIED means an earlier call
    (ours or a manifest) already set awareness, which is success for us.
    """
    return (result & 0xFFFFFFFF) in (0, 0x80070005)


def set_dpi_awareness(prefer_per_monitor: bool = True):
    """Opt-in Windows DPI awareness for crisp rendering on high-DPI screens.

    Call once before creating the first window (a process-wide setting).
    Tries per-monitor awareness first (or, with ``prefer_per_monitor=False``,
    system awareness — the level Tk 8.6 actually supports), then falls back
    to the legacy ``SetProcessDPIAware``. No-op on other platforms; returns
    True when an awareness level is active (including one set by an earlier
    call). The package calls this automatically at root creation with the
    system level; see ``ts.settings.dpi_aware`` to opt out.
    """
    if not sys.platform.startswith("win"):
        return False
    import ctypes

    levels = (2, 1) if prefer_per_monitor else (1,)
    for level in levels:
        try:
            if _hresult_awareness_set(
                ctypes.windll.shcore.SetProcessDpiAwareness(level)
            ):
                return True
        except Exception:
            pass
    try:
        if ctypes.windll.user32.SetProcessDPIAware():
            return True
    except Exception:
        return False
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

    from ._scaling import apply_tk_scaling, ensure_dpi_awareness

    ensure_dpi_awareness()
    root = tk.Tk()
    apply_tk_scaling(root)
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


def font_measure(text: str, font: Optional[FontSpec]):
    """Pixel width of ``text`` rendered in ``font`` (a name-size tuple)."""
    import tkinter.font as tkfont

    root = _font_root()
    try:
        named = tkfont.Font(root=root, font=font)
        return named.measure(str(text))
    finally:
        if not _window_alive():
            root.destroy()


def font_actual(font: Optional[FontSpec]):
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
