#!/usr/bin/env python3
"""Windows desktop integration beyond Tk (ctypes, Windows only).

- :class:`GlobalHotkeys` — system-wide hotkeys via ``RegisterHotKey``;
  messages arrive on a dedicated thread and are delivered into a Window's
  event queue.
- :func:`taskbar_progress` — Windows task bar progress indicator for the
  window via ``ITaskbarList3`` (the green/red overlay on the task bar
  button). No-op on other platforms.

Both classes degrade to silent no-ops off Windows so applications stay
cross-platform.
"""

import ctypes
import ctypes.wintypes
import threading
from typing import Dict, Tuple

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

# task bar status constants (THBF)
TBPF_NOPROGRESS = 0
TBPF_INDETERMINATE = 1
TBPF_NORMAL = 2
TBPF_ERROR = 4
TBPF_PAUSED = 8

# hotkey modifier name aliases
_MOD_ALIASES = {
    "CTRL": MOD_CONTROL,
    "CONTROL": MOD_CONTROL,
    "ALT": MOD_ALT,
    "SHIFT": MOD_SHIFT,
    "WIN": MOD_WIN,
}


class GlobalHotkeys:
    """Register system-wide hotkeys that post events into a Window.

    Usage::

        hotkeys = sg.GlobalHotkeys()
        hotkeys.register("Ctrl-Alt-P", "-HOTKEY-PRINT")
        hotkeys.start(window)          # events appear in window.read()
        ...
        hotkeys.stop()

    Modifier names: Ctrl/Control, Alt, Shift, Win separated by "-", final
    component is the key (letters, digits, F1-F24). Works even when the
    application has no focus. Windows only; a no-op elsewhere.
    """

    _MODIFIERS = _MOD_ALIASES

    def __init__(self):
        self._id_by_combo: Dict[str, int] = {}
        _key_by_id: Dict[int, str] = {}
        self._key_by_id = _key_by_id
        self._thread = None
        self._hwnd = None
        self._thread_id = None
        self._running = False
        self._window = None
        self._next_id = 1
        self._wndproc_ref = None

    # --- registration ----------------------------------------------------------
    @staticmethod
    def parse(combo: str) -> Tuple[int, int]:
        """Parse "Ctrl-Alt-P" into ``(modifiers, virtual_key)``."""
        modifiers = 0
        key = None
        for part in str(combo).split("-"):
            upper = part.strip().upper()
            if upper in _MOD_ALIASES:
                modifiers |= _MOD_ALIASES[upper]
            else:
                key = upper
        if key is None:
            raise ValueError(f"hotkey {combo!r} needs a final key")
        if len(key) == 1:
            vk = ord(key.upper())
        elif key.startswith("F") and key[1:].isdigit():
            vk = 0x70 + int(key[1:]) - 1  # VK_F1 = 0x70
        else:
            raise ValueError(f"unsupported hotkey key {key!r}")
        return modifiers, vk

    def register(self, combo: str, key: str):
        """Bind ``combo`` ("Ctrl-Alt-P") to an event ``key``."""
        modifiers, virtual_key = self.parse(combo)
        hotkey_id = self._next_id
        self._next_id += 1
        if not ctypes.windll.user32.RegisterHotKey(None, hotkey_id, modifiers, virtual_key):
            raise RuntimeError(
                f"hotkey {combo!r} is already registered by another application"
            )
        self._id_by_combo[combo] = hotkey_id
        self._key_by_id[hotkey_id] = key
        return self

    def unregister(self, combo: str):
        """Remove a previously registered hotkey."""
        hotkey_id = self._id_by_combo.pop(combo, None)
        if hotkey_id is not None:
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
            self._key_by_id.pop(hotkey_id, None)
        return self

    # --- pump --------------------------------------------------------------------
    def start(self, window):
        """Begin dispatching hotkey events into ``window``. Returns self."""
        if self._running:
            return self
        self._window = window
        self._running = True

        def pump():
            message = ctypes.wintypes.MSG()
            while self._running:
                result = ctypes.windll.user32.GetMessageW(
                    ctypes.byref(message), None, WM_HOTKEY, WM_HOTKEY
                )
                if result <= 0:
                    break
                key = self._key_by_id.get(message.wParam)
                if key is not None and self._window is not None:
                    self._window.write_event_value(key)

        self._thread = threading.Thread(target=pump, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        """Unregister every hotkey and stop the dispatch thread."""
        self._running = False
        for _combo, hotkey_id in list(self._id_by_combo.items()):
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
        self._id_by_combo.clear()
        self._key_by_id.clear()
        if self._thread is not None:
            # unblock GetMessageW with a synthetic quit
            ctypes.windll.user32.PostThreadMessageW(
                self._thread.ident, 0x0012, 0, 0
            )  # WM_QUIT
            self._thread = None
        return self

    @property
    def combos(self):
        """The registered hotkey combos."""
        return list(self._id_by_combo)


# hotkey modifier aliases (module level so parse() can read them)
_MOD_ALIASES = _MOD_ALIASES


class _TaskbarProgress:
    """ITaskbarList3 wrapper for the Windows task bar progress overlay."""

    def __init__(self, window):
        self._window = window
        self._taskbar_list = None
        self._hwnd = None
        self._initialized = False

    def _ensure(self) -> bool:
        if self._initialized:
            return True
        if not hasattr(ctypes, "windll") or not self._window._root_alive():
            return False
        hwnd = self._window.tk_root.winfo_id()
        # the tk toplevel's actual top-level HWND is its wrapper's parent
        hwnd_parent = ctypes.windll.user32.GetParent(hwnd)
        self._hwnd = hwnd_parent or hwnd
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)
        iid = (ctypes.c_ubyte * 16)(
            0xEA, 0x1E, 0xB1, 0x6B, 0x3A, 0x6E, 0xC7, 0x44,
            0x85, 0x73, 0xA5, 0xCE, 0x5F, 0x88, 0x3A, 0x93,
        )  # ITaskbarList3 {EA1EB16B-3A6E-44C7-8573-A5CE5F883A93}
        self._taskbar_list = ctypes.c_void_p()
        hr = ole32.CoCreateInstance(
            ctypes.byref((ctypes.c_ubyte * 16)(
                0x56, 0xFD, 0xFD, 0xF0, 0x06, 0x62, 0x38, 0x4E,
                0xB0, 0xA9, 0x06, 0xB3, 0x53, 0xEF, 0x27, 0xAF,
            )),  # CLSID_TaskbarList
            None,
            1,  # CLSCTX_INPROC_SERVER
            ctypes.byref(iid),
            ctypes.byref(self._taskbar_list),
        )
        if hr != 0:
            return False
        hr_init = self._vtable_call(self._taskbar_list, 3)
        self._initialized = hr_init == 0
        return self._initialized

    @staticmethod
    def _vtable_slot(interface: ctypes.c_void_p, slot: int):
        """The raw function pointer at COM vtable slot ``slot``."""
        # *interface is the pointer to the vtable; dereference it as an
        # array of function pointers and index the requested slot
        vtable_ptr = ctypes.cast(interface, ctypes.POINTER(ctypes.c_void_p)).contents
        vtable = ctypes.cast(
            ctypes.cast(vtable_ptr, ctypes.POINTER(ctypes.c_void_p)),
            ctypes.POINTER(ctypes.c_void_p * 32),
        ).contents
        address = vtable[slot]
        return address

    @classmethod
    def _vtable_call(cls, interface: ctypes.c_void_p, slot: int, *args):
        address = cls._vtable_slot(interface, slot)
        signature = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, *([ctypes.c_void_p] * len(args))
        )
        function = ctypes.cast(address, signature)
        return function(interface, *args)

    def _call(self, slot, *args):
        if not self._ensure() or self._taskbar_list is None:
            return
        self._vtable_call(self._taskbar_list, slot, *args)

    def set_value(self, current, maximum):
        """Show a determinate progress overlay at ``current``/``maximum``."""
        self._call(5, ctypes.c_void_p(int(current)), ctypes.c_void_p(int(maximum)))
        self._call(4, ctypes.c_void_p(TBPF_NORMAL))
        return self

    def set_indeterminate(self, indeterminate=True):
        """Show a marquee (indeterminate) overlay, or clear it."""
        state = TBPF_INDETERMINATE if indeterminate else TBPF_NOPROGRESS
        self._call(4, ctypes.c_void_p(state))
        return self

    def set_state(self, state):
        """Set the overlay state: "normal"/"paused"/"error"/"none"."""
        states = {
            "none": TBPF_NOPROGRESS,
            "normal": TBPF_NORMAL,
            "paused": TBPF_PAUSED,
            "error": TBPF_ERROR,
        }
        self._call(4, ctypes.c_void_p(states.get(str(state).lower(), TBPF_NOPROGRESS)))
        return self

    def clear(self):
        """Remove the progress overlay."""
        self._call(4, ctypes.c_void_p(TBPF_NOPROGRESS))
        return self


def taskbar_progress(window):
    """Return a task bar progress controller for ``window`` (Windows only).

    Returns ``None`` off Windows or before the window is finalized. Usage::

        progress = sg.taskbar_progress(window)
        progress.set_value(30, 100)     # 30% on the task bar button
        progress.set_state("error")     # red overlay
        progress.clear()
    """
    if not hasattr(ctypes, "windll"):
        return None
    if not window._root_alive():
        return None
    return _TaskbarProgress(window)
