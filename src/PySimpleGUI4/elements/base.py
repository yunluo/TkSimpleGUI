#!/usr/bin/env python3
"""PySimpleGUI4 element class hierarchy.

:class:`Element` is the abstract base of every widget. Subclasses implement
``_create_widget``; the template method :meth:`Element._build` orchestrates
creation, post configuration and event binding. State is fully encapsulated:
subclasses declare ``__slots__`` and expose behaviour through properties and
methods instead of public attributes.
"""

from abc import ABCMeta, abstractmethod

from .. import constants as C
from .. import _theming as theme_mod
from .. import settings as settings_mod

try:
    from typing import Any, Dict, Optional, Tuple
except ImportError:
    Any = Dict = Optional = Tuple = None


class ElementBaseMeta(ABCMeta):
    """Metaclass that merges ``__slots__`` declarations down the hierarchy.

    Declaring ``__slots__`` on every subclass by hand is error prone; this
    metaclass auto-merges the parent slots so subclasses only declare their
    own additions.
    """

    def __new__(mcs, name, bases, namespace):
        declared = namespace.get("__slots__", ())
        inherited = []
        for base in bases:
            for klass in reversed(base.__mro__):
                for slot in getattr(klass, "__slots__", ()):
                    if slot not in declared and slot not in inherited:
                        inherited.append(slot)
        namespace["__slots__"] = tuple(inherited) + tuple(declared)
        return super(ElementBaseMeta, mcs).__new__(mcs, name, bases, namespace)


class Element(object, metaclass=ElementBaseMeta):
    """Abstract base class for every PySimpleGUI4 element."""

    __slots__ = ("_key", "_window", "_widget", "_visible", "_tooltip", "_size")

    def __init__(self, key=None, size=(None, None), tooltip=None, visible=True):
        self._key = key
        self._window = None
        self._widget = None
        self._visible = bool(visible)
        self._tooltip = tooltip
        self._size = size

    # --- identity ------------------------------------------------------------
    @property
    def key(self):
        """The element's lookup key inside its window (may be None)."""
        return self._key

    @key.setter
    def key(self, value):
        old = self._key
        self._key = value
        if self._window is not None:
            if old is not None:
                self._window._unregister_key(old)
            if value is not None:
                self._window._register_key(self)

    @property
    def widget(self):
        """The underlying tk widget (None until the window is finalized)."""
        return self._widget

    @property
    def window(self):
        """The :class:`~PySimpleGUI4.window.Window` this element belongs to."""
        return self._window

    @property
    def size(self):
        return self._size

    @property
    def visible(self):
        return self._visible

    # --- template method ------------------------------------------------------
    def _build(self, master, window):
        """Template method: create the widget and wire it up.

        Called by the window during layout construction; user code should
        never need to call this.
        """
        self._window = window
        self._widget = self._create_widget(master)
        self._post_create()
        self._bind_events()
        if not self._visible:
            self._widget.grid_remove()
        if self._tooltip is not None:
            self._attach_tooltip()
        return self._widget

    @abstractmethod
    def _create_widget(self, master):
        """Create and return the tk widget (subclass responsibility)."""

    def _post_create(self):
        """Hook run right after widget creation (default: nothing)."""

    def _bind_events(self):
        """Hook for event bindings (default: nothing)."""

    # --- internals -------------------------------------------------------------
    def _post_event(self, key=None):
        """Push an event into the owning window's queue."""
        if self._window is not None:
            self._window._post_event(key if key is not None else self._key)

    def _attach_tooltip(self):
        from ..tooltip import Tooltip

        self._tooltip_binding = Tooltip(self._widget, self._tooltip)

    def _resolve_font(self, font):
        return font if font is not None else settings_mod.settings.font

    # --- user API ---------------------------------------------------------------
    def get(self):
        """Return the element's current value (type depends on element)."""
        return None

    def update(self, **kwargs):
        """Change the element's runtime state (element specific)."""
        raise NotImplementedError(
            "{} does not support update()".format(self.__class__.__name__)
        )

    def set_focus(self):
        """Give the keyboard focus to this element."""
        if self._widget is not None:
            self._widget.focus_set()
        return self

    def hide(self):
        """Hide the element (its row keeps its space)."""
        self._visible = False
        if self._widget is not None:
            self._widget.grid_remove()
        return self

    def unhide(self):
        """Show the element again."""
        self._visible = True
        if self._widget is not None:
            self._widget.grid()
        return self

    def refresh(self):
        """Process pending tk events for the owning window."""
        if self._window is not None:
            self._window.refresh()
        return self

    def __repr__(self):
        return "<{} key={!r}>".format(self.__class__.__name__, self._key)


class Tooltip(object):
    """Minimal hover tooltip bound to a widget."""

    def __init__(self, widget, text, delay_ms=None):
        self._widget = widget
        self._text = text
        self._tip = None
        self._id = None
        delay = delay_ms if delay_ms is not None else settings_mod.settings.tooltip_time
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        self._delay = delay

    def _schedule(self, _event):
        if self._id is None:
            self._id = self._widget.after(self._delay, self._show)

    def _show(self):
        self._id = None
        if self._tip is not None:
            return
        x = self._widget.winfo_rootx() + 10
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 10
        self._tip = tk_wrapper = self._make_tip_window(x, y)
        return tk_wrapper

    def _make_tip_window(self, x, y):
        import tkinter as tk

        tip = tk.Toplevel(self._widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry("+{}+{}".format(x, y))
        label = tk.Label(
            tip,
            text=self._text,
            background="#ffffe0",
            foreground="#000000",
            justify="left",
            relief="solid",
            borderwidth=1,
        )
        label.pack()
        return tip

    def _hide(self, _event=None):
        if self._id is not None:
            self._widget.after_cancel(self._id)
            self._id = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class InputElement(Element):
    """Intermediate base for elements that hold a readable value."""

    __slots__ = ()

    def get(self):
        """Return the element's current value."""
        raise NotImplementedError

    def update(self, value=None, **kwargs):
        raise NotImplementedError


class ContainerElement(Element):
    """Intermediate base for elements that own a nested layout.

    Subclasses hold ``_layout`` and let the window build it inside their
    widget once the widget exists.
    """

    __slots__ = ("_layout",)

    def __init__(self, layout, key=None, size=(None, None), tooltip=None, visible=True):
        super(ContainerElement, self).__init__(
            key=key, size=size, tooltip=tooltip, visible=visible
        )
        self._layout = _validate_layout(layout)

    @property
    def layout(self):
        """The nested layout rows owned by this container."""
        return self._layout

    def _post_create(self):
        if self._layout:
            self._window._build_layout(self._layout, self._widget)


def _validate_layout(layout):
    """Normalize a layout (list of rows) raising on malformed input."""
    if layout is None:
        return []
    if not isinstance(layout, (list, tuple)):
        raise TypeError("layout must be a list of rows")
    rows = []
    for row in layout:
        if row is None:
            continue
        if not isinstance(row, (list, tuple)):
            row = [row]
        rows.append(list(row))
    return rows


def theme_window_kwargs():
    """Window background kwargs for the current theme (empty when native)."""
    return theme_mod.theme_manager.window_kwargs()
