"""System-level input blocking for forced-modal windows (Windows only).

A low-level mouse + keyboard hook pair (``WH_MOUSE_LL``/``WH_KEYBOARD_LL``)
swallows every click and system key chord whose target window does not
belong to this process: the user cannot interact with any other desktop
software while a forced window is up, yet the forced window itself stays
fully usable. This is the standard technique behind exam/kiosk overlays.

* Blocking is a PRIVILEGED, intrusive behaviour — call it only on windows
  that genuinely require an answer (forced input dialogs, lock screens).
* The hook thread must pump messages; a dedicated thread owns the loop and
  is torn down on :meth:`InputBlocker.release`.
* Keyboard blocking keeps the forced window's own key events alive (they
  are dispatched through the Tk pump, not through the hook), so text input
  inside the dialog is unaffected.
* On non-Windows platforms the module import fails cleanly with
  ``ImportError`` (callers degrade instead of blocking).
"""

import ctypes
import threading

if not hasattr(ctypes, "windll"):
    raise ImportError("input_blocker requires Windows")

import ctypes.wintypes

# --- win32 constants ---------------------------------------------------------
WH_MOUSE_LL = 14
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_F4 = 0x73
LLKHF_ALTDOWN = 0x20

_HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# blocked mouse messages: L/R/X button-down events only. Button-UP events
# pass through so a click started on our window still completes cleanly.
_BLOCKED_MOUSE = frozenset((0x0201, 0x0204, 0x0206, 0x0207, 0x020A, 0x020B))


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", _POINT),
        ("mouseData", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


def _is_own_window(hwnd):
    """True when the window under the cursor belongs to this process."""
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value == kernel32.GetCurrentProcessId()


class InputBlocker(object):
    """Blocks all desktop input outside this process until released."""

    def __init__(self):
        self._hooks = []
        self._thread = None
        self._thread_id = None
        self._running = False
        self._ref: tuple = ()  # keep the HOOKPROC objects alive

    # --- hook procedures (run on the hook thread) -----------------------------
    def _mouse_proc(self, code, w_param, l_param):
        if code >= 0 and w_param in _BLOCKED_MOUSE:
            info = ctypes.cast(
                l_param, ctypes.POINTER(_MSLLHOOKSTRUCT)
            ).contents
            hwnd = user32.WindowFromPoint(info.pt)
            if hwnd and not _is_own_window(hwnd):
                return 1  # swallow
        return user32.CallNextHookEx(None, code, w_param, l_param)

    def _keyboard_proc(self, code, w_param, l_param):
        if code >= 0 and w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
            info = ctypes.cast(
                l_param, ctypes.POINTER(_KBDLLHOOKSTRUCT)
            ).contents
            vk = info.vkCode
            alt = bool(info.flags & LLKHF_ALTDOWN)
            # block system chords: Alt+Tab, Alt+F4, Alt+Esc, Win keys,
            # and plain Escape outside our own foreground window
            if (
                (alt and vk in (VK_TAB, VK_F4, VK_ESCAPE))
                or vk in (VK_LWIN, VK_RWIN)
                or (vk == VK_ESCAPE and not _is_own_window(
                    user32.GetForegroundWindow()
                ))
            ):
                return 1
        return user32.CallNextHookEx(None, code, w_param, l_param)

    # --- lifecycle --------------------------------------------------------------
    def acquire(self):
        """Install the hooks on a dedicated message-pump thread."""
        if self._running:
            return self
        self._running = True
        self._ref = (_HOOKPROC(self._mouse_proc), _HOOKPROC(self._keyboard_proc))
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        return self

    def release(self):
        """Remove the hooks and stop the pump thread."""
        self._running = False
        if self._thread_id:
            # posting WM_QUIT to the hook thread ends GetMessage loop;
            # unhook first so no callback lands on a dead thread
            for handle in self._hooks:
                user32.UnhookWindowsHookEx(handle)
            self._hooks = []
            user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT
            if self._thread is not None:
                self._thread.join(timeout=2)
            self._thread = None
            self._thread_id = None
            self._ref = ()  # drop the HOOKPROC references
        return self

    def _pump(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        mouse = self._ref[0]
        keyboard = self._ref[1]
        self._hooks = [
            user32.SetWindowsHookExW(WH_MOUSE_LL, mouse, None, 0),
            user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard, None, 0),
        ]
        if 0 in self._hooks:
            for handle in self._hooks:
                if handle:
                    user32.UnhookWindowsHookEx(handle)
            self._hooks = []
            self._running = False
            return
        msg = ctypes.wintypes.MSG()
        while self._running and user32.GetMessageW(
            ctypes.byref(msg), None, 0, 0
        ) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        for handle in self._hooks:
            user32.UnhookWindowsHookEx(handle)
        self._hooks = []


_blocker = None


def block_input():
    """Start blocking input outside this process (no-op when already on)."""
    global _blocker
    if _blocker is None:
        _blocker = InputBlocker()
    _blocker.acquire()
    return _blocker


def unblock_input():
    """Stop blocking input (no-op when not blocking)."""
    global _blocker
    if _blocker is not None:
        _blocker.release()
    return None
