#!/usr/bin/env python3
"""Windows DWM window beautification for TkSimpleGUI, pure ctypes.

Wraps the small subset of ``DwmSetWindowAttribute`` that makes sense for
tk windows: the immersive dark title bar (Windows 10 1809+) and the
system backdrop (Mica / Acrylic, Windows 11 22H2+). Every attribute that
a Windows build does not support simply returns False — nothing raises.

Window corner preference is deliberately NOT wrapped: Windows 11 rounds
corners by default and the toolkit leaves that to the system.

This module imports cleanly on every platform; the functions raise
``NotImplementedError`` on non-Windows.
"""

import ctypes
import sys
from ctypes.wintypes import BOOL, DWORD, HWND, UINT

# DWM window attributes
DWMWA_USE_IMMERSIVE_DARK_MODE = 20   # BOOL: dark title bar / caption (1809+)
DWMWA_SYSTEMBACKDROP_TYPE = 38       # UINT: Win11 22H2+ system backdrop

# DWMSBT_* values for DWMWA_SYSTEMBACKDROP_TYPE
DWMSBT_NONE = 1            # no backdrop
DWMSBT_MAINWINDOW = 2      # Mica
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic
DWMSBT_TABBEDWINDOW = 4    # Mica Alt

_BACKDROP_NAMES = {
    "none": DWMSBT_NONE,
    "mica": DWMSBT_MAINWINDOW,
    "acrylic": DWMSBT_TRANSIENTWINDOW,
    "mica_alt": DWMSBT_TABBEDWINDOW,
}


def dwm_hwnd(window_or_wid) -> int:
    """The real top-level HWND of a tk window, as an int.

    ``winfo_id()`` of a Toplevel returns the child window tk draws into;
    the DWM frame belongs to its wrapper, which is the parent HWND
    (same trick the hotkey module uses for the taskbar API).
    """
    if not sys.platform == "win32":
        raise NotImplementedError("DWM window attributes are Windows only")
    user32 = ctypes.windll.user32
    # c_void_p restype: returns the address as int (None for NULL HWND)
    user32.GetParent.restype = ctypes.c_void_p
    user32.GetParent.argtypes = [HWND]
    wid = int(window_or_wid)
    parent = user32.GetParent(wid)
    return int(parent) if parent else wid


if sys.platform == "win32":

    def _set_attribute(hwnd: int, attribute: int, value: int, size: int) -> bool:
        """One DwmSetWindowAttribute call; False when unsupported/failed."""
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = [
            HWND, DWORD, ctypes.c_void_p, DWORD,
        ]
        dwmapi.DwmSetWindowAttribute.restype = ctypes.HRESULT
        try:
            return dwmapi.DwmSetWindowAttribute(
                HWND(hwnd), DWORD(attribute),
                ctypes.byref(ctypes.c_int(value)), DWORD(size),
            ) == 0
        except OSError:
            return False

else:  # non-Windows: the module imports, the API does not exist

    def _set_attribute(hwnd: int, attribute: int, value: int, size: int) -> bool:
        raise NotImplementedError("DWM window attributes are Windows only")


def apply_dark_titlebar(hwnd: int, dark: bool) -> bool:
    """Switch the window caption between dark and light (Windows 10 1809+).

    Returns True when the attribute was accepted; False on older builds
    (and, in the negative-space of Windows theming, when the caller has
    overridden the caption itself).
    """
    return _set_attribute(
        hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0,
        ctypes.sizeof(BOOL),
    )


def apply_backdrop(hwnd: int, backdrop: str) -> bool:
    """Apply a Win11 22H2+ system backdrop ("mica"/"acrylic"/"mica_alt"/"none").

    The frame is extended into the client area first so the backdrop has
    somewhere to show through — Tk paints its own background on top, so
    the effect is only visible where the toolkit leaves the surface bare
    (e.g. together with a transparent color key). ``None``/``"none"``
    restores the default. Returns True when both calls were accepted.
    """
    name = str(backdrop or "none").lower()
    if name not in _BACKDROP_NAMES:
        raise ValueError(
            f"backdrop must be one of {sorted(_BACKDROP_NAMES)}, got {backdrop!r}"
        )
    if not sys.platform == "win32":
        raise NotImplementedError("DWM window attributes are Windows only")

    dwmapi = ctypes.windll.dwmapi
    dwmapi.DwmExtendFrameIntoClientArea.argtypes = [
        HWND, ctypes.c_void_p,
    ]
    dwmapi.DwmExtendFrameIntoClientArea.restype = ctypes.HRESULT
    # MARGINS {cxLeftWidth, cxRightWidth, cyTopHeight, cyBottomHeight}:
    # all -1 extends the frame across the whole client area
    margins = (ctypes.c_int * 4)(-1, -1, -1, -1)
    try:
        extended = dwmapi.DwmExtendFrameIntoClientArea(
            HWND(hwnd), ctypes.byref(margins),
        ) == 0
    except OSError:
        extended = False
    accepted = _set_attribute(
        hwnd, DWMWA_SYSTEMBACKDROP_TYPE, _BACKDROP_NAMES[name], ctypes.sizeof(UINT),
    )
    return extended and accepted
