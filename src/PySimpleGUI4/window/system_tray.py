#!/usr/bin/env python3
"""System tray support for PySimpleGUI4 (Windows only).

A real tray icon backed by a hidden Win32 message window: balloon
notifications, a right-click context menu and mouse events, all delivered
through :meth:`SystemTray.Read`. The message pump is the Tk event loop, so
tray events fire while a window is being read; a standalone (windowless)
tray creates its own hidden Tk root to pump with::

    tray = sg.SystemTray(menu=["Show", "---", "Exit"])
    event, _ = tray.Read(timeout=100)   # menu item text / __CLICKED__ / ...
    tray.ShowMessage("Hello", "Body")
    tray.close()

On non-Windows platforms the constructor raises ``RuntimeError``.
"""

import base64
import ctypes
import ctypes.wintypes
import os
import queue
import struct
import tempfile
import time

from .. import constants as C

try:
    from typing import Any, List, Optional
except ImportError:
    Any = List = Optional = None

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
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
NIN_BALLOONUSERCLICK = WM_USER + 5
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_NCDESTROY = 0x0082
WM_NULL = 0x0000
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x10
TPM_LEFTBUTTON = 0x0000
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100
MF_STRING = 0x0000
MF_SEPARATOR = 0x0800

# event names posted into the queue
EVENT_CLICKED = "__CLICKED__"
EVENT_DOUBLE_CLICKED = "__DOUBLE CLICKED__"
EVENT_RIGHT_CLICKED = "__RIGHT CLICKED__"
EVENT_MESSAGE = "__MESSAGE__"

_ICONS = {}  # hwnd -> SystemTray (WndProc dispatch)

# Python 3.12 removed WNDCLASSW from ctypes.wintypes; define it ourselves.
_WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.wintypes.UINT),
        ("lpfnWndProc", _WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.wintypes.HINSTANCE),
        ("hIcon", ctypes.wintypes.HICON),
        ("hCursor", ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HBRUSH),
        ("lpszMenuName", ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
    ]


class SystemTray(object):
    """A system tray icon with a context menu and notifications."""

    def __init__(self, title="Tray", icon=None, tooltip=None, menu=None):
        if not hasattr(ctypes, "windll"):
            raise RuntimeError("SystemTray requires Windows")
        self._title = title
        self._tooltip = tooltip or title
        self._icon_data = icon
        self._menu = list(menu) if menu else []
        self._window_class = "PySimpleGUI4Tray{}".format(id(self))
        self._hwnd = None
        self._icon_handle = None
        self._created = False
        self._owns_root = False
        self._tk_root = None
        self._events = queue.Queue()
        self._register_and_show()

    # --- pump -----------------------------------------------------------------
    def _ensure_pump_root(self):
        """Tray events ride the tk message pump; borrow or create a root."""
        if self._tk_root is not None:
            return
        from .window import Window

        for window in Window._open_windows:
            if window._root_alive():
                self._tk_root = window.tk_root
                return
        import tkinter as tk

        self._tk_root = tk.Tk()
        self._tk_root.withdraw()
        self._owns_root = True

    # --- win32 plumbing ----------------------------------------------------
    def _register_and_show(self):
        user32 = ctypes.windll.user32
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.DefWindowProcW.argtypes = [
            ctypes.wintypes.HWND,
            ctypes.wintypes.UINT,
            ctypes.wintypes.WPARAM,
            ctypes.wintypes.LPARAM,
        ]
        user32.CreateWindowExW.restype = ctypes.wintypes.HWND
        user32.CreateWindowExW.argtypes = [
            ctypes.wintypes.DWORD,      # dwExStyle
            ctypes.wintypes.LPCWSTR,    # lpClassName
            ctypes.wintypes.LPCWSTR,    # lpWindowName
            ctypes.wintypes.DWORD,      # dwStyle
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.wintypes.HWND,       # hWndParent
            ctypes.wintypes.HMENU,      # hMenu
            ctypes.wintypes.HINSTANCE,  # hInstance
            ctypes.wintypes.LPVOID,     # lpParam
        ]
        wnd_class = WNDCLASSW()
        wnd_class.lpszClassName = self._window_class
        wnd_class.lpfnWndProc = _tray_wnd_proc_ref
        wnd_class.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
        atom = user32.RegisterClassW(ctypes.byref(wnd_class))
        if not atom:
            raise RuntimeError("RegisterClassW failed")
        self._hwnd = user32.CreateWindowExW(
            0, self._window_class, self._title, 0, 0, 0, 0, 0, None, None,
            wnd_class.hInstance, None,
        )
        _ICONS[self._hwnd] = self
        self._add_icon()

    def _icon_from_data(self):
        user32 = ctypes.windll.user32
        if self._icon_data is None:
            return user32.LoadIconW(None, 32512)  # IDI_APPLICATION
        try:
            raw = base64.b64decode(self._icon_data)
            if raw[:8] == b"\x89PNG\r\n\x1a\n":
                raw = _wrap_png_as_ico(raw)
            handle, path = tempfile.mkstemp(suffix=".ico")
            with os.fdopen(handle, "wb") as icon_file:
                icon_file.write(raw)
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

    # --- tray events -------------------------------------------------------------
    def _on_tray_event(self, l_param):
        if l_param == WM_LBUTTONUP:
            self._events.put(EVENT_CLICKED)
        elif l_param == WM_LBUTTONDBLCLK:
            self._events.put(EVENT_DOUBLE_CLICKED)
        elif l_param == WM_RBUTTONUP:
            if self._menu:
                selection = self._show_menu()
                if selection is not None:
                    self._events.put(selection)
            else:
                self._events.put(EVENT_RIGHT_CLICKED)
        elif l_param == NIN_BALLOONUSERCLICK:
            self._events.put(EVENT_MESSAGE)

    def _show_menu(self):
        """Popup the context menu; returns the chosen label (or None)."""
        user32 = ctypes.windll.user32
        menu = user32.CreatePopupMenu()
        command_to_label = {}
        command_id = 1
        try:
            for item in self._menu:
                if item == C.MENU_SEPARATOR_LINE:
                    user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
                    continue
                label = str(item).replace(C.MENU_SHORTCUT_CHARACTER, "")
                user32.AppendMenuW(menu, MF_STRING, command_id, label)
                command_to_label[command_id] = label
                command_id += 1
            point = ctypes.wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(point))
            user32.SetForegroundWindow(self._hwnd)
            selected = user32.TrackPopupMenu(
                menu,
                TPM_RIGHTBUTTON | TPM_RETURNCMD,
                point.x,
                point.y,
                0,
                self._hwnd,
                None,
            )
            user32.PostMessageW(self._hwnd, WM_NULL, 0, 0)
            return command_to_label.get(selected)
        finally:
            user32.DestroyMenu(menu)

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

    def read(self, timeout=None):
        """Pump events and return ``(event, None)``.

        Events: a menu item label, or one of the ``__...__`` mouse/balloon
        events. ``C.TIMEOUT_KEY`` when nothing arrived in ``timeout`` ms.
        """
        self._ensure_pump_root()
        deadline = None if timeout is None else time.time() + timeout / 1000.0
        while True:
            try:
                self._tk_root.update()
            except Exception:
                return C.WIN_CLOSED, None
            try:
                return self._events.get_nowait(), None
            except queue.Empty:
                pass
            if deadline is not None and time.time() >= deadline:
                return C.TIMEOUT_KEY, None
            time.sleep(0.01)

    Read = read  # PySimpleGUI style alias

    def close(self):
        """Remove the icon and release the tray resources."""
        self.Hide()
        if self._hwnd:
            _ICONS.pop(self._hwnd, None)
            ctypes.windll.user32.DestroyWindow(self._hwnd)
            self._hwnd = None
        if self._owns_root and self._tk_root is not None:
            try:
                self._tk_root.destroy()
            except Exception:
                pass
            self._tk_root = None
        return self

    # --- PSG style aliases -----------------------------------------------------
    ShowMsg = ShowMessage
    notify = ShowMessage


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


def _wrap_png_as_ico(png_bytes):
    """Wrap a single-image PNG into a minimal ICO container (Vista+)."""
    width = png_bytes[16]
    height = png_bytes[20]  # IHDR dimensions, big-endian; low bytes enough
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", width % 256, height % 256, 0, 0, 1, 32, len(png_bytes), 22)
    return header + entry + png_bytes


def _tray_wnd_proc(hwnd, msg, w_param, l_param):
    """Window procedure for the hidden tray window (per-hwnd dispatch).

    Tk owns the thread's message pump, so this must never call
    ``PostQuitMessage`` (a WM_QUIT would kill Tk's loop).
    """
    if msg == WM_TRAY_EVENT:
        tray = _ICONS.get(hwnd)
        if tray is not None:
            try:
                tray._on_tray_event(l_param)
            except Exception:
                pass
            return 0
    if msg in (WM_CLOSE, WM_DESTROY, WM_NCDESTROY):
        return 0
    return ctypes.windll.user32.DefWindowProcW(hwnd, msg, w_param, l_param)


# the callback object must outlive the window class registration
_tray_wnd_proc_ref = _WNDPROC(_tray_wnd_proc)
