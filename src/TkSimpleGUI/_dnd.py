#!/usr/bin/env python3
"""Windows file drag-and-drop for Tk windows, pure ctypes.

Uses the legacy shell route (same as the windnd project):
``DragAcceptFiles`` puts a window into file-drop mode and a WndProc
subclass receives ``WM_DROPFILES`` — a plain window message, so the file
list is delivered by the ordinary Tk message pump on the main thread.
No COM, no third-party extension.

This module imports cleanly on every platform; the functions raise on
non-Windows.
"""

import ctypes
import logging
import sys
from ctypes import WINFUNCTYPE, c_int, c_void_p
from ctypes.wintypes import BOOL, HANDLE, HWND, LPARAM, UINT, WPARAM
from typing import Any, Callable, Dict, List, Tuple

_drop_logger = logging.getLogger("TkSimpleGUI.drop")

WM_DROPFILES = 0x0233
GWL_WNDPROC = -4
# LRESULT is pointer-sized (missing from ctypes.wintypes)
_LRESULT = ctypes.c_longlong if sys.maxsize > 2 ** 32 else ctypes.c_long


def _files_from_hdrop(hdrop: int) -> List[str]:
    """The file paths carried by an ``HDROP`` handle (wide API, full
    length paths). Drains the handle with ``DragFinish``."""
    _shell32.DragQueryFileW.argtypes = [HANDLE, UINT, c_void_p, UINT]
    _shell32.DragQueryFileW.restype = UINT
    count = _shell32.DragQueryFileW(hdrop, UINT(0xFFFFFFFF), None, 0)
    buffer = ctypes.create_unicode_buffer(32768)
    files: List[str] = []
    for index in range(count):
        _shell32.DragQueryFileW(hdrop, index, buffer, len(buffer))
        files.append(buffer.value)
    _shell32.DragFinish(hdrop)
    return files


def _deliver_drop_files(hdrop: int, func: Callable[[List[str]], Any]) -> None:
    """Deliver one ``WM_DROPFILES`` payload to the user callback.

    Runs on the main thread (window messages are pumped there). A failing
    callback must not break the window procedure: the error goes to the
    ``TkSimpleGUI.drop`` logger instead.
    """
    try:
        func(_files_from_hdrop(hdrop))
    except Exception as error:
        _drop_logger.error(
            "drop_target callback %s failed",
            getattr(func, "__name__", None) or repr(func),
            exc_info=error)


if sys.platform == "win32":
    _user32 = ctypes.windll.user32
    _shell32 = ctypes.windll.shell32
    _shell32.DragAcceptFiles.argtypes = [HANDLE, BOOL]
    _shell32.DragFinish.argtypes = [HANDLE]
    _user32.CallWindowProcW.argtypes = [c_void_p, HWND, UINT, WPARAM, LPARAM]
    _user32.CallWindowProcW.restype = _LRESULT

    # GetWindowLongPtr/SetWindowLongPtr only exist in 64-bit user32; on
    # 32-bit builds the plain *W exports are the same call (pointers fit
    # into a DWORD there).
    if sys.maxsize > 2 ** 32:
        _get_wndproc = _user32.GetWindowLongPtrW
        _set_wndproc = _user32.SetWindowLongPtrW
    else:
        _get_wndproc = _user32.GetWindowLongW
        _set_wndproc = _user32.SetWindowLongW
    _get_wndproc.argtypes = [HWND, c_int]
    _get_wndproc.restype = c_void_p
    _set_wndproc.argtypes = [HWND, c_int, c_void_p]
    _set_wndproc.restype = c_void_p

    _WndProc = WINFUNCTYPE(_LRESULT, HWND, UINT, WPARAM, LPARAM)

    # hwnd -> (original proc address, kept-alive ctypes callback)
    _hooked: Dict[int, Tuple[int, Any]] = {}

    def register_drop_target(hwnd: int, func: Callable[[List[str]], Any]) -> None:
        """Make the window accept file drops, delivered as
        ``func([path, ...])``. A second registration replaces the first."""
        if not callable(func):
            raise TypeError(f"func must be callable, not {type(func).__name__}")
        revoke_drop_target(hwnd)
        _shell32.DragAcceptFiles(hwnd, True)
        original = _get_wndproc(hwnd, GWL_WNDPROC)

        @_WndProc
        def _subclass(hwnd_: int, msg: int, wparam: int, lparam: int) -> int:
            if msg == WM_DROPFILES:
                try:
                    _deliver_drop_files(wparam, func)
                except Exception as error:
                    _drop_logger.error(
                        "WM_DROPFILES handling failed", exc_info=error)
            return _user32.CallWindowProcW(original, hwnd_, msg, wparam, lparam)

        _set_wndproc(hwnd, GWL_WNDPROC, _subclass)
        _hooked[hwnd] = (original or 0, _subclass)

    def revoke_drop_target(hwnd: int) -> None:
        """Restore the original window procedure and stop accepting drops
        (unknown handles are ignored)."""
        entry = _hooked.pop(hwnd, None)
        if entry is None:
            return
        original, _callback = entry
        _set_wndproc(hwnd, GWL_WNDPROC, original)
        _shell32.DragAcceptFiles(hwnd, False)
else:
    def register_drop_target(hwnd: int, func: Callable[[List[str]], Any]) -> None:
        raise NotImplementedError("drop_target requires Windows")

    def revoke_drop_target(hwnd: int) -> None:
        return None
