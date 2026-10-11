#!/usr/bin/env python3
"""System tray support for PySimpleGUI4.

The implementation is Windows-only (via ``Shell_NotifyIcon`` through ctypes)
and intentionally minimal: show an icon, show balloon notifications and hide
it again. Menus inside the tray are planned but not implemented yet.
On non-Windows platforms the constructor raises ``RuntimeError``.
"""

import ctypes
import ctypes.wintypes
import threading

from .. import constants as C

try:
    from typing import Optional
except ImportError:
    Optional = None

# --- win32 constants ---------------------------------------------------------
NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIF_MESSAGE = 1
NIF_ICON = 2
NIF_TIP = 4
NIF_INFO = 16
NIIF_INFO = 1
NIIF_WARNING = 2
NIIF_ERROR = 3
WM_USER = 0x400
WM_TRAY_EVENT = WM_USER + 1
WM_RBUTTONUP = 0x0205
WM_LBUTTONUP = 0x0206
WM_CLOSE = 0x0010
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x10


class SystemTray(object):
    """A system tray icon with balloon notifications (Windows only).

    Usage::

        tray = sg.SystemTray(title="My App", icon=sg.DEFAULT_BASE64_ICON)
        tray.ShowMessage("Hello", "Body of the notification")
        tray.close()
    """

    def __init__(self, title="Tray", icon=None, tooltip=None):
        if not ctypes.windll.shell32:
            raise RuntimeError("SystemTray requires Windows")
        self._title = title
        self._tooltip = tooltip or title
        self._icon_data = icon
        self._window_class = "PySimpleGUI4Tray{}".format(id(self))
        self._hwnd = None
        self._icon_handle = None
        self._created = False
        self._register_and_show()

    # --- win32 plumbing ----------------------------------------------------
    def _register_and_show(self):
        user32 = ctypes.windll.user32
        wnd_class = ctypes.wintypes.WNDCLASSW()
        wnd_class.lpszClassName = self._window_class
        wnd_class.lpfnWndProc = _tray_wnd_proc
        wnd_class.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
        atom = user32.RegisterClassW(ctypes.byref(wnd_class))
        if not atom:
            raise RuntimeError("RegisterClassW failed")
        self._hwnd = user32.CreateWindowExW(
            0, self._window_class, self._title, 0, 0, 0, 0, 0, None, None,
            wnd_class.hInstance, None,
        )
        self._add_icon()

    def _icon_from_data(self):
        user32 = ctypes.windll.user32
        if self._icon_data is None:
            return user32.LoadIconW(None, 32512)  # IDI_APPLICATION
        try:
            import base64
            import os
            import tempfile

            raw = base64.b64decode(self._icon_data)
            handle, path = tempfile.mkstemp(suffix=".ico")
            with os.fdopen(handle, "wb") as f:
                f.write(raw)
            hicon = user32.LoadImageW(
                None, path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE
            )
            os.remove(path)
            return hicon or user32.LoadIconW(None, 32512)
        except Exception:
            return user32.LoadIconW(None, 32512)

    def _add_icon(self):
        shell32 = ctypes.windll.shell32
        self._icon_handle = self._icon_from_data()
        notify_data = _NotifyIconData()
        notify_data.hWnd = self._hwnd
        notify_data.uID = 1
        notify_data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        notify_data.uCallbackMessage = WM_TRAY_EVENT
        notify_data.hIcon = self._icon_handle
        tip = self._tooltip[:127].encode("utf-16-le") + b"\x00\x00"
        ctypes.memmove(notify_data.szTip, tip, min(len(tip), 256))
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(notify_data))
        self._created = True

    # --- public API ----------------------------------------------------------
    def ShowMessage(self, title, message, messageicon=NIIF_INFO):
        """Show a balloon notification."""
        if not self._created:
            return self
        shell32 = ctypes.windll.shell32
        notify_data = _NotifyIconData()
        notify_data.hWnd = self._hwnd
        notify_data.uID = 1
        notify_data.uFlags = NIF_INFO
        notify_data.uTimeout = 3000
        notify_data.dwInfoFlags = messageicon
        title_bytes = title[:63].encode("utf-16-le") + b"\x00\x00"
        body_bytes = message[:255].encode("utf-16-le") + b"\x00\x00"
        ctypes.memmove(notify_data.szInfoTitle, title_bytes, min(len(title_bytes), 128))
        ctypes.memmove(notify_data.szInfo, body_bytes, min(len(body_bytes), 512))
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(notify_data))
        return self

    def Update(self, tooltip=None, icon=None):
        """Change the tooltip or icon."""
        if tooltip is not None:
            self._tooltip = tooltip
        if icon is not None:
            self._icon_data = icon
        if self._created:
            shell32 = ctypes.windll.shell32
            notify_data = _NotifyIconData()
            notify_data.hWnd = self._hwnd
            notify_data.uID = 1
            notify_data.uFlags = NIF_ICON | NIF_TIP
            notify_data.hIcon = self._icon_from_data()
            tip = self._tooltip[:127].encode("utf-16-le") + b"\x00\x00"
            ctypes.memmove(notify_data.szTip, tip, min(len(tip), 256))
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(notify_data))
        return self

    def Hide(self):
        """Remove the icon from the tray (can be shown again via UnHide)."""
        if self._created:
            notify_data = _NotifyIconData()
            notify_data.hWnd = self._hwnd
            notify_data.uID = 1
            ctypes.windll.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(notify_data))
            self._created = False
        return self

    def UnHide(self):
        """Put the icon back into the tray."""
        if not self._created:
            self._add_icon()
        return self

    def close(self):
        """Remove the icon and release the tray resources."""
        self.Hide()
        if self._hwnd:
            ctypes.windll.user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
            self._hwnd = None
        return self

    # --- PSG style aliases -----------------------------------------------------
    ShowMsg = ShowMessage
    notify = ShowMessage

    def Read(self, timeout=None):
        """Compatibility stub: tray events are not implemented yet."""
        return (None, None)


class _NotifyIconData(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("hWnd", ctypes.wintypes.HWND),
        ("uID", ctypes.wintypes.UINT),
        ("uFlags", ctypes.wintypes.UINT),
        ("uCallbackMessage", ctypes.wintypes.UINT),
        ("hIcon", ctypes.wintypes.HICON),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", ctypes.wintypes.DWORD),
        ("dwStateMask", ctypes.wintypes.DWORD),
        ("szInfo", ctypes.c_wchar * 256),
        ("uVersion", ctypes.wintypes.UINT),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", ctypes.wintypes.DWORD),
    ]

    def __init__(self):
        super(_NotifyIconData, self).__init__()
        self.cbSize = ctypes.sizeof(self)


def _tray_wnd_proc(hwnd, msg, w_param, l_param):
    """Minimal window procedure for the hidden tray window."""
    if msg == WM_CLOSE:
        ctypes.windll.user32.DestroyWindow(hwnd)
        return 0
    if msg == ctypes.wintypes.WM_DESTROY:
        ctypes.windll.user32.PostQuitMessage(0)
        return 0
    return ctypes.windll.user32.DefWindowProcW(hwnd, msg, w_param, l_param)
