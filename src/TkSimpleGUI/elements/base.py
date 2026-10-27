#!/usr/bin/env python3
"""TkSimpleGUI element class hierarchy.

:class:`Element` is the abstract base of every widget. Subclasses implement
``_create_widget``; the template method :meth:`Element._build` orchestrates
creation, post configuration and event binding. State is fully encapsulated:
subclasses declare ``__slots__`` and expose behavior through properties and
methods instead of public attributes.

Every element also carries the shared layout hints (``pad``, ``expand_x``,
``expand_y``, ``justification``), an optional ``right_click_menu`` and free
form ``metadata``, handled by the base class itself.

Typing note: ``_widget``/``_window`` are ``None`` until :meth:`_build` runs
(finalization), but every accessor that needs them is only reachable through
a finalized element, so they are annotated as non-optional to keep the
thousands of downstream call sites narrow.
"""

from abc import ABCMeta, abstractmethod
from typing import Any, Optional, Tuple, Union

import tkinter as tk

from .. import constants as C
from .. import _theming as theme_mod
from ..settings import settings

# A user-visible element key (str or any hashable); None means "no key".
ElementKey = Optional[Any]
# Colors are Tk color strings ("#rrggbb", "red", ...).
Color = str
# Fonts are (family, size[, modifiers...]) tuples or tk font descriptions.
FontSpec = Union[Tuple[str, int], Tuple[str, int, str], str]
# Layout cells hold a single element or nested rows (validated at build time).
PadSpec = Union[int, float, Tuple[int, int], Tuple[Tuple[int, int], Tuple[int, int]]]
Justification = Optional[str]
MenuDefinition = "list"



class ElementBaseMeta(ABCMeta):
    """Metaclass that merges ``__slots__`` declarations down the hierarchy.

    Declaring ``__slots__`` on every subclass by hand is error prone; this
    metaclass auto-merges the parent slots so subclasses only declare their
    own additions.
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        declared = namespace.get("__slots__", ())
        inherited = []
        for base in bases:
            for klass in reversed(base.__mro__):
                for slot in getattr(klass, "__slots__", ()):
                    if slot not in declared and slot not in inherited:
                        inherited.append(slot)
        namespace["__slots__"] = tuple(inherited) + tuple(declared)
        cls = super().__new__(mcs, name, bases, namespace)
        # every concrete element gains a config= keyword without each of the
        # 40 constructors having to declare it: the metaclass wraps __init__
        # to expand an ElementOptions dataclass into the base keyword args
        original_init = cls.__init__

        def config_aware_init(self, *args, **kwargs):
            config = kwargs.pop("config", None)
            if config is not None:
                from ..config import ElementOptions

                if not isinstance(config, ElementOptions):
                    raise TypeError("config must be an ElementOptions instance")
                for option_name in (
                    "key", "size", "tooltip", "visible", "pad", "expand_x",
                    "expand_y", "justification", "right_click_menu", "metadata",
                ):
                    value = getattr(config, option_name)
                    if value is not None and kwargs.get(option_name) is None:
                        kwargs[option_name] = value
                if config.disabled and not kwargs.get("disabled"):
                    kwargs["disabled"] = True
            original_init(self, *args, **kwargs)

        config_aware_init.__doc__ = original_init.__doc__
        cls.__init__ = config_aware_init  # ty: ignore[invalid-assignment]
        return cls


class Element(metaclass=ElementBaseMeta):
    """Abstract base class for every TkSimpleGUI element."""

    __slots__ = (
        "_key",
        "_window",
        "_widget",
        "_visible",
        "_tooltip",
        "_size",
        "_pad",
        "_expand_x",
        "_expand_y",
        "_justification",
        "_right_click_menu",
        "_metadata",
        "_tooltip_binding",
        "_popup_menu",
    )

    # Typed views of the slots. Values are assigned in __init__/_build; the
    # class-level annotations below let type checkers see them as non-optional
    # inside method bodies (runtime stays __slots__-based).
    _key: ElementKey
    _window: "Any"  # Window; Any breaks the window→elements import cycle
    _widget: Any  # tk widget once _build has run
    _visible: bool
    _tooltip: Optional[str]
    _size: Tuple[Optional[int], Optional[int]]
    _pad: Optional[PadSpec]
    _expand_x: bool
    _expand_y: bool
    _justification: Justification
    _right_click_menu: Optional[list]
    _metadata: Any
    _tooltip_binding: Optional["Tooltip"]
    _popup_menu: Optional[tk.Menu]

    def __init__(
        self,
        key=None,
        size=(None, None),
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        self._key = key
        self._window = None
        self._widget = None
        self._visible = bool(visible)
        self._tooltip = tooltip
        self._size = size
        self._pad = pad
        self._expand_x = bool(expand_x)
        self._expand_y = bool(expand_y)
        self._justification = justification
        self._right_click_menu = right_click_menu
        self._metadata = metadata
        self._tooltip_binding = None
        self._popup_menu = None

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
        """The :class:`~TkSimpleGUI.window.Window` this element belongs to."""
        return self._window

    @property
    def size(self):
        return self._size

    @property
    def visible(self):
        return self._visible

    @property
    def pad(self):
        """The per element padding override (None = package default)."""
        return self._pad

    @property
    def expand_x(self):
        """True when the element stretches horizontally with its cell."""
        return self._expand_x

    @property
    def expand_y(self):
        """True when the element stretches vertically with its cell."""
        return self._expand_y

    @property
    def justification(self):
        """Cell alignment hint: "left", "right" or "center"."""
        return self._justification

    @property
    def metadata(self):
        """Free form user data attached to the element (any object)."""
        return self._metadata

    @property
    def right_click_menu(self):
        """The element's right-click menu definition (or None)."""
        return self._right_click_menu

    @right_click_menu.setter
    def right_click_menu(self, value):
        """Set (and attach) the menu; also usable after finalization."""
        self._right_click_menu = value
        if self._widget is not None and value is not None and self._popup_menu is None:
            self._attach_right_click_menu()

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
        if self._tooltip is not None:
            self._attach_tooltip()
        return self._widget

    @abstractmethod
    def _create_widget(self, master):
        """Create and return the tk widget (subclass responsibility)."""

    def _post_create(self):
        """Hook run right after widget creation (default: right-click menu)."""
        if self._right_click_menu is not None:
            self._attach_right_click_menu()

    def _bind_events(self):
        """Hook for event bindings (default: nothing)."""

    # --- grid integration ---------------------------------------------------------
    def _grid_into(self, master, row, column, default_pad, default_justification):
        """Grid the widget honoring pad/expand/justification hints.

        Called by :meth:`Window._build_layout`. Returns ``(expand_x, expand_y)``
        so the caller can configure matching row/column weights.
        """
        left, right, top, bottom = _parse_pad(
            self._pad if self._pad is not None else default_pad
        )
        if self._expand_x:
            sticky_x = "we"
        else:
            choice = self._justification or default_justification
            if choice is None or str(choice).lower() in ("l", "left"):
                sticky_x = "w"
            elif str(choice).lower() in ("r", "right"):
                sticky_x = "e"
            else:
                sticky_x = ""
        sticky = sticky_x + ("ns" if self._expand_y else "")
        self._widget.grid(
            row=row,
            column=column,
            padx=(left, right),
            pady=(top, bottom),
            sticky=sticky or None,
        )
        if not self._visible:
            self._widget.grid_remove()
        return self._expand_x, self._expand_y

    # --- right click menu ---------------------------------------------------------
    def _attach_right_click_menu(self):
        self._popup_menu = build_popup_menu(
            self, self._bind_target, self._right_click_menu
        )
        self._bind_target.bind("<Button-3>", self._show_popup_menu)

    def _show_popup_menu(self, event):
        if self._popup_menu is not None:
            try:
                self._popup_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._popup_menu.grab_release()
        return "break"

    # --- internals -------------------------------------------------------------
    def _post_event(self, key=None):
        """Push an event into the owning window's queue (and the global bus)."""
        if self._window is not None:
            self._window._post_event(key if key is not None else self._key)

    def _attach_tooltip(self):
        self._tooltip_binding = Tooltip(self._bind_target, self._tooltip)

    def _resolve_font(self, font):
        return font if font is not None else settings.font

    # --- user API ---------------------------------------------------------------
    def get(self) -> Any:
        """Return the element's current value (type depends on element)."""
        return None

    def update(self, *args: Any, **kwargs: Any) -> "Element":
        """Change the element's runtime state (element specific).

        Subclasses take over with their own named parameters; the base
        accepts anything so overrides stay Liskov-compatible.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support update()"
        )

    @property
    def _bind_target(self):
        """The widget that :meth:`bind` attaches to (composite elements may
        override this to point at the interactive inner widget)."""
        return self._widget

    def bind(self, event_pattern=None, callback=None, key=None, **kwargs):
        """Bind a tk event pattern (``"<Double-1>"``, ``"<Motion>"``…).

        ``callback(element, event)`` runs on the event, or ``key`` (or the
        element's own key when both are omitted) is posted into the window
        queue. Subclasses may reinterpret the first parameter (TTable binds
        data records instead); anything not understood should fall back to
        ``super().bind``. Returns self.
        """
        widget = self._bind_target
        if widget is None:
            raise RuntimeError("bind requires a finalized window")
        if callback is not None:
            widget.bind(
                event_pattern, lambda event: callback(self, event)
            )
        elif key is not None:
            widget.bind(event_pattern, lambda _event: self._post_event(key))
        else:
            widget.bind(event_pattern, lambda _event: self._post_event())
        return self

    def unbind(self, event_pattern):
        """Remove a binding added with :meth:`bind`. Returns self."""
        widget = self._bind_target
        if widget is not None:
            widget.unbind(event_pattern)
        return self

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

    def apply_theme(self):
        """Re-apply theme colors to this element's widget (live theme switch).

        The default implementation refreshes only ttk styles (a no-op for
        plain tk widgets); element classes that paint theme colors directly
        onto tk widgets (TText, TInput, TFrame, TColumn, TCanvas, TStatusBar…)
        override this to reconfigure their options. Elements that were
        created with explicit ``text_color`` / ``background_color`` keep
        those -- only theme-derived colors change. Returns self.
        """
        return self

    def refresh(self):
        """Process pending tk events for the owning window."""
        if self._window is not None:
            self._window.refresh()
        return self

    def __repr__(self):
        return f"<{self.__class__.__name__} key={self._key!r}>"


class Tooltip:
    """Minimal hover tooltip bound to a widget."""

    def __init__(self, widget, text, delay_ms=None):
        self._widget = widget
        self._text = text
        self._tip = None
        self._id = None
        delay = delay_ms if delay_ms is not None else settings.tooltip_time
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        self._delay = delay

    def _schedule(self, _event):
        if self._id is None:
            self._id = self._widget.after(self._delay, self._show)

    def _show(self):
        self._id = None
        if self._tip is not None:
            return None
        x = self._widget.winfo_rootx() + 10
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 10
        self._tip = tk_wrapper = self._make_tip_window(x, y)
        return tk_wrapper

    def _make_tip_window(self, x, y):
        import tkinter as tk

        tip = tk.Toplevel(self._widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        # themed windows get a themed tooltip; native keeps the classic look
        colors = theme_mod.theme_manager.tooltip_colors()
        label = tk.Label(
            tip,
            text=self._text,
            background=colors.get("background", "#ffffe0"),
            foreground=colors.get("foreground", "#000000"),
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

    __slots__ = ("_disabled",)

    def __init__(
        self,
        key=None,
        size=(None, None),
        tooltip=None,
        visible=True,
        disabled=False,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._disabled = bool(disabled)

    @property
    def disabled(self):
        """True when the element was disabled at construction."""
        return self._disabled

    def _apply_disabled(self, widget):
        """Apply the constructor ``disabled`` state to a freshly built widget."""
        if self._disabled:
            widget.configure(state="disabled")

    def get(self) -> Any:
        """Return the element's current value."""
        raise NotImplementedError

    def update(self, *args: Any, **kwargs: Any) -> "Element":
        raise NotImplementedError


class ContainerElement(Element):
    """Intermediate base for elements that own a nested layout.

    Subclasses hold ``_layout`` and let the window build it inside their
    widget once the widget exists.
    """

    __slots__ = ("_layout",)

    def __init__(
        self,
        layout,
        key=None,
        size=(None, None),
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._layout = _validate_layout(layout)

    @property
    def layout(self):
        """The nested layout rows owned by this container."""
        return self._layout

    def _post_create(self):
        super()._post_create()
        if self._layout:
            self._window._build_layout(self._layout, self._widget)

    def apply_theme(self):
        """Repaint the container surface so nested themed rows sit on it."""
        bg = theme_mod.theme_manager.effective_background()
        if bg is None:
            bg = theme_mod.native_widget_colors(
                tk.Frame, self._widget, ("background",)
            )["background"]
        self._widget.configure(background=bg)
        return self


def build_popup_menu(owner, master, definition):
    """Build a ``tk.Menu`` from a TkSimpleGUI menu definition.

    Selecting an item posts its (shortcut-stripped) label as an event on
    ``owner`` (any object with a ``_post_event(key)`` method, typically an
    element or a window). The definition is either one ``[title, [items]]``
    pair or a list of such pairs; nested ``[title, [items]]`` lists create
    submenus, ``"---"`` separators, a leading ``"!"`` disables the item.
    """
    if definition and isinstance(definition[0], (list, tuple)):
        cascades = definition
    else:
        cascades = [definition]
    menu = tk.Menu(master, tearoff=False)
    for entry in cascades:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            raise ValueError(
                f"menu definition entries must be (title, items) pairs: {entry!r}"
            )
        title = str(entry[0]).replace(C.MENU_SHORTCUT_CHARACTER, "")
        submenu = tk.Menu(menu, tearoff=False)
        _fill_popup_items(owner, submenu, entry[1])
        menu.add_cascade(label=title, menu=submenu)
    return menu


def _fill_popup_items(owner, menu, items):
    for item in items:
        if isinstance(item, (list, tuple)):
            if len(item) == 2 and isinstance(item[1], (list, tuple)):
                title = str(item[0]).replace(C.MENU_SHORTCUT_CHARACTER, "")
                submenu = tk.Menu(menu, tearoff=False)
                _fill_popup_items(owner, submenu, item[1])
                menu.add_cascade(label=title, menu=submenu)
            else:
                _fill_popup_items(owner, menu, item)
            continue
        if item == C.MENU_SEPARATOR_LINE:
            menu.add_separator()
            continue
        label = str(item).replace(C.MENU_SHORTCUT_CHARACTER, "")
        disabled = label.startswith(C.MENU_DISABLED_CHARACTER)
        if disabled:
            label = label[len(C.MENU_DISABLED_CHARACTER):]
        menu.add_command(
            label=label,
            state="disabled" if disabled else "normal",
            command=lambda text=label: owner._post_event(text),
        )


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
        rows.append(list(row) if isinstance(row, (list, tuple)) else [row])
    return rows


def _parse_pad(pad):
    """Normalize a pad spec (number, (x, y) or ((l, r), (t, b))) to 4 numbers."""
    if pad is None:
        return 0, 0, 0, 0
    if isinstance(pad, (int, float)):
        return pad, pad, pad, pad
    if len(pad) == 2 and isinstance(pad[0], (list, tuple)):
        return pad[0][0], pad[0][1], pad[1][0], pad[1][1]
    return pad[0], pad[0], pad[1], pad[1]


def theme_window_kwargs():
    """Window background kwargs for the current theme (empty when native)."""
    return theme_mod.theme_manager.window_kwargs()
