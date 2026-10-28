#!/usr/bin/env python3
"""Standard input and display widgets for TkSimpleGUI."""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Iterable, Optional, Sequence, TYPE_CHECKING, Tuple, cast
from .._typing_compat import Literal

from .base import (
    Color,
    Element,
    ElementKey,
    FontSpec,
    InputElement,
    Justification,
    MenuDefinition,
    PadSpec,
    Size,
)
from .. import constants as C
from .. import enums as E
from .. import _theming as theme_mod
import contextlib

if TYPE_CHECKING:  # the logger imports this module's TMultiline lazily
    from ..logger import Logger



# TListbox selectmode accepts tk constants SINGLE/BROWSE/MULTIPLE/EXTENDED.
# Bare strings ("single" / "browse" / ...) are accepted alongside the enum
# so callers can pass either.
_LISTBOX_SELECT_MODE_MAP = {
    E.SelectMode.SINGLE: tk.SINGLE,
    E.SelectMode.BROWSE: tk.BROWSE,
    E.SelectMode.MULTIPLE: tk.MULTIPLE,
    E.SelectMode.EXTENDED: tk.EXTENDED,
    "single": tk.SINGLE,
    "browse": tk.BROWSE,
    "multiple": tk.MULTIPLE,
    "extended": tk.EXTENDED,
}


def _char_width(size: Size):
    """Width in characters from a (width, height) size pair."""
    if size is None:
        return None
    width = size[0]
    return None if width is None else int(width)


def _char_height(size: Size):
    if size is None:
        return None
    height = size[1]
    return None if height is None else int(height)


# --- built-in input validators (validate_command callables) -------------------
def validate_integer(text: str):
    """Validator: allow only integers (empty text allowed while editing)."""
    if text in ("", "-"):
        return True
    try:
        int(text)
        return True
    except ValueError:
        return False


def validate_float(text: str):
    """Validator: allow only floats (empty text allowed while editing)."""
    if text in ("", "-", ".", "-."):
        return True
    try:
        float(text)
        return True
    except ValueError:
        return False


def validate_regex(pattern: str, flags: int = 0):
    """Validator factory: allow only text fully matching ``pattern``.

    Returns a ``validate_command`` callable; empty text always passes so
    deleting stays possible::

        TInput(validate="key", validate_command=validate_regex(r"\\d{1,3}"))
    """
    import re

    compiled = re.compile(pattern, flags)

    def validator(text: str):
        if text == "":
            return True
        return compiled.fullmatch(text) is not None

    return validator


class TText(Element):
    """A static label (optionally with an inline image and text wrapping)."""

    __slots__ = (
        "_text",
        "_text_color",
        "_background_color",
        "_font",
        "_enable_events",
        "_image_data",
        "_image_filename",
        "_photo",
        "_wrap_length",
    )

    def __init__(
        self,
        text: str = "",
        key: Optional[ElementKey] = None,
        size: Size = (None, None),
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        justification: Optional[Justification] = None,
        enable_events: bool = False,
        image_data: Optional[bytes] = None,
        image_filename: Optional[str] = None,
        wrap_length: Optional[int] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
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
        self._text = "" if text is None else str(text)
        self._text_color = text_color
        self._background_color = background_color
        self._justification = justification or "left"
        self._font = font
        self._enable_events = enable_events
        self._image_data = image_data
        self._image_filename = image_filename
        self._photo = None
        self._wrap_length = wrap_length

    @property
    def text(self):
        return self._text

    def _create_widget(self, master: tk.Misc):
        kwargs = theme_mod.theme_manager.text_kwargs(
            color=self._text_color, background_color=self._background_color
        )
        kwargs["text"] = self._text
        kwargs["justify"] = self._justification
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        if self._font is not None:
            kwargs["font"] = self._font
        if self._wrap_length is not None:
            kwargs["wraplength"] = int(self._wrap_length)
        label = ttk.Label(master, **kwargs)
        if self._image_data is not None or self._image_filename is not None:
            try:
                if self._image_data is not None:
                    self._photo = tk.PhotoImage(
                        data=self._image_data, master=label
                    )
                else:
                    self._photo = tk.PhotoImage(
                        file=str(self._image_filename), master=label
                    )
                label.configure(image=self._photo, compound="left")
            except tk.TclError:
                self._photo = None
        return label

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<Button-1>", lambda _e: self._post_event())

    def apply_theme(self):
        if self._text_color is None and self._background_color is None:
            # theme-derived colors only: repaint, or clear when the theme
            # went back to the native look ("" restores the platform color)
            kwargs = theme_mod.theme_manager.text_kwargs()
            if not kwargs:
                kwargs = {"background": "", "foreground": ""}
            self._widget.configure(**kwargs)
        return self

    def get(self):
        """The displayed text."""
        return self._text

    def update(
        self,
        value: Any = None,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        visible: Optional[bool] = None):
        if value is not None:
            self._text = str(value)
            self._widget.configure(text=self._text)
        if text_color is not None:
            self._text_color = text_color
            self._widget.configure(foreground=text_color)
        if background_color is not None:
            self._background_color = background_color
            self._widget.configure(background=background_color)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TStatusBar(Element):
    """Sunken label typically placed at the bottom of a window."""

    __slots__ = ("_text", "_text_color", "_background_color", "_font")

    def __init__(
        self,
        text: str = "",
        key: Optional[ElementKey] = None,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        justification: Optional[Justification] = None,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = text
        self._text_color = text_color
        self._background_color = background_color
        self._font = font

    def _create_widget(self, master: tk.Misc):
        kwargs = theme_mod.theme_manager.text_kwargs(
            color=self._text_color, background_color=self._background_color
        )
        kwargs.setdefault("relief", tk.SUNKEN)
        kwargs.setdefault("anchor", "w")
        if self._font is not None:
            kwargs["font"] = self._font
        return tk.Label(master, text=self._text, **kwargs)

    def get(self):
        return self._text

    def apply_theme(self):
        if self._text_color is None and self._background_color is None:
            kwargs = theme_mod.theme_manager.text_kwargs()
            if not kwargs:
                # classic tk.Label: sample the platform defaults ("" is
                # only accepted by ttk widgets)
                kwargs = theme_mod.native_widget_colors(
                    tk.Label, self._widget, ("background", "foreground")
                )
            kwargs.setdefault("relief", tk.SUNKEN)
            kwargs.setdefault("anchor", "w")
            self._widget.configure(**kwargs)
        return self

    def update(self, value: Any = None, visible: Optional[bool] = None):
        if value is not None:
            self._text = str(value)
            self._widget.configure(text=self._text)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TInput(InputElement):
    """Single line text entry (ttk based for a native look)."""

    __slots__ = (
        "_default_text",
        "_enable_events",
        "_password_char",
        "_textvariable",
        "_text_color",
        "_background_color",
        "_font",
        "_validate",
        "_validate_command",
        "_invalid_command",
        "_justify",
    )

    # created in _create_widget before any accessor runs
    _textvariable: tk.StringVar

    def __init__(
        self,
        default_text: str = "",
        key: Optional[ElementKey] = None,
        size: Size = (None, None),
        enable_events: bool = False,
        password_char: str = "",
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        validate: Any = None,
        validate_command: Any = None,
        invalid_command: Any = None,
        justify: Justification = "left",
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._default_text = "" if default_text is None else str(default_text)
        self._enable_events = enable_events
        self._password_char = password_char
        self._textvariable = None  # ty: ignore[invalid-assignment]
        self._text_color = text_color
        self._background_color = background_color
        self._font = font
        self._validate = validate
        self._validate_command = validate_command
        self._invalid_command = invalid_command
        # str-enum values compare equal to their Tk strings, so both
        # ts.Justify.RIGHT and "right" land here the same way
        # str-enum values compare equal to their Tk strings, so both
        # ts.Justify.RIGHT and "right" land here the same way
        self._justify = str(justify).lower() if str(justify).lower() in ("left", "center",
                "right") else "left"
        if validate is not None and validate_command is not None:
            if not callable(validate_command):
                raise TypeError("validate_command must be a callable(text) -> bool")
            if invalid_command is not None and not callable(invalid_command):
                raise TypeError("invalid_command must be a callable(text)")

    def _create_widget(self, master: tk.Misc):
        self._textvariable = tk.StringVar(value=self._default_text)
        style_name = theme_mod.theme_manager.ttk_widget_style(
            master,
            "TEntry",
            foreground=self._text_color,
            fieldbackground=self._background_color,
            font=self._font,
        )
        kwargs: Dict[str, Any] = {
            "style": style_name,
            "justify": cast(Literal["left", "center", "right"], self._justify),
        }
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        if self._password_char:
            kwargs["show"] = self._password_char
        if self._validate is not None and self._validate_command is not None:
            # native tk.Entry validation; "%P" passes the text after the edit
            validator = self._validate_command
            kwargs["validate"] = self._validate
            kwargs["validatecommand"] = (
                master.register(lambda new_text: bool(validator(new_text))),
                "%P",
            )
            if self._invalid_command is not None:
                invalid = self._invalid_command
                kwargs["invalidcommand"] = (
                    master.register(invalid),
                    "%P",
                )
        entry = ttk.Entry(master, textvariable=self._textvariable, **kwargs)
        self._apply_disabled(entry)
        return entry

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<KeyRelease>", lambda _e: self._post_event())
        self._widget.bind("<Return>", lambda _e: self._post_event())

    def apply_theme(self):
        # recompute the derived TEntry style from the new palette
        self._widget.configure(
            style=theme_mod.theme_manager.ttk_widget_style(
                self._widget.nametowidget(self._widget.winfo_parent()),
                "TEntry",
                foreground=self._text_color,
                fieldbackground=self._background_color,
                font=self._font,
            )
        )
        return self

    @property
    def default_text(self):
        return self._default_text

    def get(self):
        """Current text."""
        return self._textvariable.get()

    def update(
        self,
        value: Any = None,
        disabled: Optional[bool] = None,
        select: Any = None,
        visible: Optional[bool] = None):
        if value is not None:
            state = str(self._widget.cget("state"))
            if state == "disabled":
                self._widget.configure(state="normal")
            self._textvariable.set(str(value))
            if state == "disabled":
                self._widget.configure(state="disabled")
        if disabled is not None:
            self._disabled = bool(disabled)
            self._widget.configure(state="disabled" if disabled else "normal")
        if select:
            self._widget.select_range(0, "end")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def set_password_char(self, char: Any):
        """Show ``char`` instead of the typed characters (masking)."""
        self._password_char = char
        self._widget.configure(show=char)
        return self

    # --- native tk.Entry API passthrough ---------------------------------------
    def set(self, value: Any):
        """Replace the text (native ``StringVar.set``)."""
        self._textvariable.set("" if value is None else str(value))
        return self

    def insert(self, index: int, text: str):
        """Insert ``text`` at character ``index`` (native ``Entry.insert``)."""
        self._widget.insert(int(index), str(text))
        return self

    def delete(self, first: Any, last: Any = None):
        """Delete characters ``first``..``last`` (native ``Entry.delete``)."""
        self._widget.delete(int(first), None if last is None else int(last))
        return self

    def get_position(self):
        """The insertion cursor's character index."""
        return self._widget.index("insert")

    def set_position(self, index: int):
        """Move the insertion cursor to character ``index``."""
        self._widget.icursor(int(index))
        return self

    def select_range(self, first: int = 0, last: Any = None):
        """Select a character range (``last=None`` means end)."""
        self._widget.select_range(int(first), "end" if last is None else int(last))
        return self

    def clear_selection(self):
        """Deselect any selected text."""
        self._widget.select_clear()
        return self


class TCombo(InputElement):
    """Dropdown combo box (ttk.Combobox)."""

    __slots__ = (
        "_values",
        "_default_value",
        "_enable_events",
        "_readonly",
        "_variable",
        "_text_color",
        "_background_color",
        "_font",
    )

    _variable: tk.StringVar

    def __init__(
        self,
        values: Iterable[Any] = (),
        default_value: Any = None,
        key: Optional[ElementKey] = None,
        size: Size = (None, None),
        enable_events: bool = False,
        readonly: bool = True,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._values = list(values)
        self._default_value = default_value
        self._enable_events = enable_events
        self._readonly = readonly
        self._variable = None  # ty: ignore[invalid-assignment]
        self._text_color = text_color
        self._background_color = background_color
        self._font = font

    def _create_widget(self, master: tk.Misc):
        self._variable = tk.StringVar(
            value="" if self._default_value is None else str(self._default_value)
        )
        style_name = theme_mod.theme_manager.ttk_widget_style(
            master,
            "TCombobox",
            foreground=self._text_color,
            fieldbackground=self._background_color,
            font=self._font,
        )
        kwargs = {"style": style_name}
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        state = "disabled" if self._disabled else ("readonly" if self._readonly else "normal")
        return ttk.Combobox(
            master,
            textvariable=self._variable,
            values=[str(v) for v in self._values],
            state=state,
            **kwargs
        )

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<ComboboxSelected>>", lambda _e: self._post_event())

    @property
    def values(self):
        return list(self._values)

    def get(self):
        """Currently selected/entered text."""
        return self._variable.get()

    def set(self, value: Any):
        """Set the text (native ``StringVar.set``)."""
        self._variable.set("" if value is None else str(value))
        return self

    def current(self, index: Optional[int] = None):
        """Get or set the selected index (native ``Combobox.current``)."""
        if index is None:
            return self._widget.current()
        self._widget.current(int(index))
        return self

    def update(
        self,
        value: Any = None,
        values: Optional[Iterable[Any]] = None,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if values is not None:
            self._values = list(values)
            self._widget.configure(values=[str(v) for v in self._values])
        if value is not None:
            self._variable.set(str(value))
        if disabled is not None:
            self._disabled = bool(disabled)
            state = "disabled" if disabled else ("readonly" if self._readonly else "normal")
            self._widget.configure(state=state)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TOptionMenu(TCombo):
    """Compatibility alias of :class:`TCombo` with a non-readonly default."""

    __slots__ = ()

    def __init__(
        self,
        values: Iterable[Any] = (),
        default_value: Any = None,
        key: Optional[ElementKey] = None,
        **kwargs: Any):
        kwargs.setdefault("readonly", False)
        super().__init__(
            values=values, default_value=default_value, key=key, **kwargs
        )


class TListbox(InputElement):
    """Multi item selection list."""

    __slots__ = ("_values", "_select_mode", "_enable_events",
            "_text_color", "_background_color", "_font")

    def __init__(
        self,
        values: Iterable[Any] = (),
        key: Optional[ElementKey] = None,
        size: Size = C.DEFAULT_LISTBOX_SIZE,
        select_mode: Optional[str] = E.SelectMode.BROWSE,
        enable_events: bool = False,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._values = list(values)
        self._select_mode = select_mode
        self._enable_events = enable_events
        self._text_color = text_color
        self._background_color = background_color
        self._font = font

    def _create_widget(self, master: tk.Misc):
        kwargs = theme_mod.theme_manager.input_kwargs(
            text_color=self._text_color,
            background_color=self._background_color,
            include_caret=False,  # tk.Listbox has no text caret
        )
        kwargs["exportselection"] = False
        width = _char_width(self._size)
        height = _char_height(self._size)
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if self._font is not None:
            kwargs["font"] = self._font
        mode = _LISTBOX_SELECT_MODE_MAP.get(str(self._select_mode or ""), tk.BROWSE)
        listbox = tk.Listbox(master, selectmode=mode, **kwargs)
        for value in self._values:
            listbox.insert("end", str(value))
        self._apply_disabled(listbox)
        return listbox

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<ListboxSelect>>", lambda _e: self._post_event())

    def _scroll_command(self):
        """The yview command a standalone :class:`TScrollbar` can drive."""
        return self._widget.yview

    def apply_theme(self):
        kwargs = theme_mod.theme_manager.input_kwargs(
            text_color=self._text_color,
            background_color=self._background_color,
            include_caret=False,
        )
        if not kwargs:
            kwargs = theme_mod.native_widget_colors(
                tk.Listbox, self._widget, ("background", "foreground")
            )
        self._widget.configure(**kwargs)
        return self

    @property
    def values(self):
        return list(self._values)

    def get(self):
        """List of currently selected values."""
        indices = self._widget.curselection()
        return [self._widget.get(index) for index in indices]

    @property
    def selected_indices(self):
        return list(self._widget.curselection())

    def see(self, index: int):
        """Scroll so ``index`` is visible (native Listbox.see)."""
        self._widget.see(int(index))
        return self

    def size(self):
        """The number of items (native Listbox.size)."""
        return self._widget.size()

    def update(
        self,
        values: Optional[Iterable[Any]] = None,
        set_to_index: Optional[int] = None,
        select_rows: Any = None,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if values is not None:
            self._values = list(values)
            self._widget.delete(0, "end")
            for value in self._values:
                self._widget.insert("end", str(value))
        if set_to_index is not None:
            self._widget.selection_clear(0, "end")
            self._widget.selection_set(set_to_index)
            self._widget.see(set_to_index)
        if select_rows is not None:
            self._widget.selection_clear(0, "end")
            for row in select_rows or ():
                self._widget.selection_set(row)
        if disabled is not None:
            self._disabled = bool(disabled)
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TSpin(InputElement):
    """Spinbox with a fixed set of values — or a numeric range.

    Pass ``values=[...]`` for a fixed list, or ``range_=(lo, hi)`` with
    ``increment`` for a native numeric spinbox (with ``wrap`` rollover)::
        ts.TSpin(range_=(0, 100), increment=5, initial_value=10)
    """

    __slots__ = (
        "_values",
        "_initial_value",
        "_enable_events",
        "_variable",
        "_text_color",
        "_background_color",
        "_font",
        "_range_",
        "_increment",
        "_wrap",
    )

    _variable: tk.StringVar

    def __init__(
        self,
        values: Iterable[Any] = (),
        initial_value: Any = None,
        key: Optional[ElementKey] = None,
        size: Size = (None, None),
        enable_events: bool = False,
        range_: Any = None,
        increment: int = 1,
        wrap: bool = False,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        if range_ is not None and values:
            raise ValueError("give either values= or range_=, not both")
        if range_ is not None:
            low, high = int(range_[0]), int(range_[1])
            step = max(1, int(increment))
            self._values = list(range(low, high + 1, step))
        else:
            self._values = list(values)
        self._initial_value = initial_value if initial_value is not None else (
            self._values[0] if self._values else ""
        )
        self._enable_events = enable_events
        self._variable = None  # ty: ignore[invalid-assignment]
        self._text_color = text_color
        self._background_color = background_color
        self._font = font
        self._range_ = range_
        self._increment = increment
        self._wrap = bool(wrap)

    def _create_widget(self, master: tk.Misc):
        self._variable = tk.StringVar(value=str(self._initial_value))
        style_name = theme_mod.theme_manager.ttk_widget_style(
            master,
            "TSpinbox",
            foreground=self._text_color,
            fieldbackground=self._background_color,
            font=self._font,
        )
        kwargs = {"style": style_name}
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        state = "disabled" if self._disabled else "readonly"
        if self._range_ is not None:
            # native numeric mode: from/to/increment/wrap
            low = int(self._range_[0])
            high = int(self._range_[1])
            spin = ttk.Spinbox(
                master,
                from_=low,
                to=high,
                increment=max(1, int(self._increment)),
                wrap=self._wrap,
                textvariable=self._variable,
                state=state,
                **kwargs
            )
            self._variable.set(str(self._initial_value))
            return spin
        spin = ttk.Spinbox(
            master,
            values=[str(v) for v in self._values],
            textvariable=self._variable,
            state=state,
            **kwargs
        )
        # a Spinbox with values= snaps its variable to values[0]; re-apply
        self._variable.set(str(self._initial_value))
        return spin

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<Increment>>", lambda _e: self._post_event())
            self._widget.bind("<<Decrement>>", lambda _e: self._post_event())
            self._widget.bind("<Return>", lambda _e: self._post_event())

    def get(self):
        return self._variable.get()

    @property
    def values(self):
        return list(self._values)

    def set(self, value: Any):
        """Set the value (native ``StringVar.set``)."""
        self._variable.set("" if value is None else str(value))
        return self

    def update(
        self,
        value: Any = None,
        values: Optional[Iterable[Any]] = None,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if values is not None:
            self._values = list(values)
            self._widget.configure(values=[str(v) for v in self._values])
        if value is not None:
            self._variable.set(str(value))
        if disabled is not None:
            self._disabled = bool(disabled)
            self._widget.configure(state="disabled" if disabled else "readonly")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TCheckbox(InputElement):
    """TCheckbox with a boolean value."""

    __slots__ = ("_text", "_default", "_enable_events", "_variable",
            "_text_color", "_background_color", "_font")

    _variable: tk.BooleanVar

    def __init__(
        self,
        text: str,
        default: Any = False,
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = text
        self._default = bool(default)
        self._enable_events = enable_events
        self._variable = None  # ty: ignore[invalid-assignment]
        self._text_color = text_color
        self._background_color = background_color
        self._font = font

    def _create_widget(self, master: tk.Misc):
        self._variable = tk.BooleanVar(value=self._default)
        style_name = theme_mod.theme_manager.ttk_widget_style(
            master,
            "TCheckbutton",
            foreground=self._text_color,
            background=self._background_color,
            font=self._font,
        )
        checkbox = ttk.Checkbutton(
            master, text=self._text, variable=self._variable, style=style_name
        )
        self._apply_disabled(checkbox)
        return checkbox

    def _bind_events(self):
        if self._enable_events:
            self._widget.configure(command=self._post_event)

    @property
    def text(self):
        return self._text

    def get(self):
        """True when checked."""
        return self._variable.get()

    def update(
        self,
        value: Any = None,
        text: Optional[str] = None,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if value is not None:
            self._variable.set(bool(value))
        if text is not None:
            self._text = text
            self._widget.configure(text=text)
        if disabled is not None:
            self._disabled = bool(disabled)
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def toggle(self):
        """Flip the checked state (native BooleanVar flip)."""
        self._variable.set(not self._variable.get())
        return self

    def select(self):
        """Check the box."""
        self._variable.set(True)
        return self

    def deselect(self):
        """Uncheck the box."""
        self._variable.set(False)
        return self


class TRadio(InputElement):
    """TRadio button sharing a value with every radio of the same group."""

    __slots__ = ("_text", "_group_id", "_default", "_enable_events",
            "_text_color", "_background_color", "_font")

    def __init__(
        self,
        text: str,
        group_id: Any,
        default: Any = False,
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = text
        self._group_id = group_id
        self._default = bool(default)
        self._enable_events = enable_events
        self._text_color = text_color
        self._background_color = background_color
        self._font = font

    @property
    def group_id(self):
        return self._group_id

    def _create_widget(self, master: tk.Misc):
        group_variable = self._window.radio_group_variable(self._group_id)
        style_name = theme_mod.theme_manager.ttk_widget_style(
            master,
            "TRadiobutton",
            foreground=self._text_color,
            background=self._background_color,
            font=self._font,
        )
        radio = ttk.Radiobutton(
            master,
            text=self._text,
            value=self._text,
            variable=group_variable,
            style=style_name,
        )
        if self._default:
            group_variable.set(self._text)
        self._apply_disabled(radio)
        return radio

    def _bind_events(self):
        if self._enable_events:
            self._widget.configure(command=self._post_event)

    def get(self):
        """True when this radio is the selected one in its group."""
        return self._window.radio_group_variable(self._group_id).get() == self._text

    def update(
        self,
        value: Any = None,
        text: Optional[str] = None,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if value:
            self._window.radio_group_variable(self._group_id).set(self._text)
        if text is not None:
            self._text = text
            self._widget.configure(text=text)
        if disabled is not None:
            self._disabled = bool(disabled)
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def select(self):
        """Make this radio the selected one in its group."""
        self._window.radio_group_variable(self._group_id).set(self._text)
        return self

    def deselect(self):
        """Clear the group selection (no radio selected)."""
        self._window.radio_group_variable(self._group_id).set("")
        return self

    def group_value(self):
        """The raw shared group value (the selected radio's text, or "")."""
        return self._window.radio_group_variable(self._group_id).get()


class TSlider(InputElement):
    """Horizontal or vertical slider (ttk.Scale for a native look).

    With ``show_value=True`` a small value bubble appears above (or beside)
    the slider while it is dragged — something ttk.Scale cannot do natively.
    """

    __slots__ = (
        "_range",
        "_default_value",
        "_orientation",
        "_enable_events",
        "_resolution",
        "_show_value",
        "_bubble",
        "_bubble_job",
    )

    def __init__(
        self,
        range_: Tuple[int, int] = (1, 10),
        default_value: Any = None,
        orientation: Optional[str] = "h",
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        resolution: Any = None,
        size: Size = (20, 15),
        show_value: bool = False,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._range = range_
        self._default_value = (
            default_value if default_value is not None else range_[0]
        )
        self._orientation = orientation
        self._enable_events = enable_events
        self._resolution = resolution
        self._show_value = bool(show_value)
        self._bubble: Optional[tk.Toplevel] = None
        self._bubble_job = None

    def _create_widget(self, master: tk.Misc):
        orient = (
            "horizontal"
            if str(self._orientation).lower() in ("h", "horizontal")
            else "vertical"
        )
        style_name = (
            "Horizontal.TScale" if orient == "horizontal" else "Vertical.TScale"
        )
        scale = ttk.Scale(
            master,
            orient=orient,
            style=style_name,
            from_=self._range[0],
            to=self._range[1],
        )
        scale.set(self._default_value)
        self._apply_disabled(scale)
        return scale

    def _bind_events(self):
        if self._enable_events:
            self._widget.configure(command=self._on_scale_command)
        if self._show_value:
            self._widget.bind("<B1-Motion>", self._show_bubble, add="+")
            self._widget.bind("<ButtonPress-1>", self._show_bubble, add="+")
            self._widget.bind("<ButtonRelease-1>", self._hide_bubble, add="+")

    def _on_scale_command(self, value: Any):
        if self._show_value and self._bubble is not None:
            self._update_bubble_text(value)
        self._post_event()

    # --- value bubble (Toplevel following the slider handle) ----------------------
    def _show_bubble(self, _event: tk.Event):
        if self._bubble is None:
            self._bubble = tk.Toplevel(self._widget)
            self._bubble.wm_overrideredirect(True)
            self._bubble.attributes("-topmost", True)
            tk.Label(
                self._bubble,
                text="",
                background="#333333",
                foreground="#ffffff",
                font=("Helvetica", 9),
                padx=6,
                pady=2,
            ).pack()
        self._update_bubble_position()
        self._update_bubble_text(self._widget.get())
        if self._bubble_job is not None:
            self._widget.after_cancel(self._bubble_job)

    def _update_bubble_position(self):
        if self._bubble is None:
            return
        horizontal = str(self._orientation).lower() in ("h", "horizontal")
        value = float(self._widget.get())
        low, high = float(self._range[0]), float(self._range[1])
        span = (high - low) or 1.0
        ratio = max(0.0, min(1.0, (value - low) / span))
        if horizontal:
            x = self._widget.winfo_rootx() + int(
                ratio * max(1, self._widget.winfo_width() - 24)
            ) + 4
            y = self._widget.winfo_rooty() - 30
        else:
            x = self._widget.winfo_rootx() + self._widget.winfo_width() + 6
            y = self._widget.winfo_rooty() + int(
                (1.0 - ratio) * max(1, self._widget.winfo_height() - 24)
            ) + 4
        self._bubble.wm_geometry(f"+{x}+{y}")

    def _update_bubble_text(self, value: Any):
        if self._bubble is None:
            return
        if self._resolution == 1:
            text = str(int(round(float(value))))
        else:
            text = f"{float(value):.2f}".rstrip("0").rstrip(".")
        # the bubble holds exactly one Label, created in _show_bubble
        label = cast(tk.Label, self._bubble.winfo_children()[0])
        label.configure(text=text)

    def _hide_bubble(self, _event: tk.Event):
        if self._bubble is not None:
            def destroy():
                if self._bubble is not None:
                    self._bubble.destroy()
                    self._bubble = None
            # small delay so the release click does not race the popup
            self._bubble_job = self._widget.after(250, destroy)

    def get(self):
        """Current value as float (int when resolution is 1)."""
        value = self._widget.get()
        if self._resolution == 1:
            return int(round(float(value)))
        return float(value)

    def update(
        self,
        value: Any = None,
        range_: Optional[Tuple[int, int]] = None,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if range_ is not None:
            self._range = range_
            self._widget.configure(from_=range_[0], to=range_[1])
        if value is not None:
            self._widget.set(value)
        if disabled is not None:
            self._disabled = bool(disabled)
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TMultiline(InputElement):
    """Multi line text area."""

    __slots__ = (
        "_default_text",
        "_enable_events",
        "_text_color",
        "_background_color",
        "_font",
        "_wrap",
        "_scroll_y",
        "_text",
        "_logger",
    )

    # the inner tk.Text of the composite (container + optional scrollbar)
    _text: tk.Text
    _logger: Optional["Logger"]

    def __init__(
        self,
        default_text: str = "",
        key: Optional[ElementKey] = None,
        size: Size = (40, 5),
        enable_events: bool = False,
        enter_submits: bool = False,
        wrap: str = "word",
        scroll_y: bool = False,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            disabled=disabled,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._default_text = "" if default_text is None else str(default_text)
        self._enable_events = enable_events
        self._text_color = text_color
        self._background_color = background_color
        self._font = font
        # str-enum WrapMode values compare equal to the tk strings
        self._wrap = str(wrap) if str(wrap) in ("word", "char", "none") else "word"
        self._scroll_y = bool(scroll_y)
        self._text = None  # ty: ignore[invalid-assignment]
        self._logger = None

    def _create_widget(self, master: tk.Misc):
        kwargs = theme_mod.theme_manager.input_kwargs(
            text_color=self._text_color, background_color=self._background_color
        )
        width = _char_width(self._size)
        height = _char_height(self._size)
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if self._font is not None:
            kwargs["font"] = self._font
        kwargs["undo"] = True  # native tk.Text undo/redo stack
        kwargs["wrap"] = self._wrap
        container = tk.Frame(master)
        text = tk.Text(container, **kwargs)
        text.insert("1.0", self._default_text)
        self._apply_disabled(text)
        text.grid(row=0, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        if self._scroll_y:
            scrollbar = tk.Scrollbar(
                container, orient="vertical", command=text.yview
            )
            text.configure(yscrollcommand=scrollbar.set)
            scrollbar.grid(row=0, column=1, sticky="ns")
        self._text = text
        return container

    @property
    def _bind_target(self):
        return self._text

    def _scroll_command(self):
        """The yview command a standalone :class:`TScrollbar` can drive."""
        return self._text.yview

    def _bind_events(self):
        if self._enable_events:
            self._text.bind("<KeyRelease>", lambda _e: self._post_event())
        self._text.bind("<Return>", self._on_return)

    def apply_theme(self):
        kwargs = theme_mod.theme_manager.input_kwargs(
            text_color=self._text_color, background_color=self._background_color
        )
        if not kwargs:
            kwargs = theme_mod.native_widget_colors(
                tk.Text, self._text,
                ("background", "foreground", "insertbackground"),
            )
        self._text.configure(**kwargs)
        return self

    def _on_return(self, event: tk.Event):
        if self._enable_events:
            self._post_event()
        return event

    def get(self):
        """Full contents (without the trailing newline)."""
        return self._text.get("1.0", "end-1c")

    def _end_state(self):
        """State a freshly written widget should be left in."""
        return "disabled" if self._disabled else "normal"

    def write(self, *args: Any, **kwargs: Any):
        """Append text; ``text_color`` colors the line.

        Colors use a native tk.Text tag, so mixed-color output works::

            multiline.write("ok", text_color="#00aa00")
            multiline.write("failed", text_color="#cc0000")
        """
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        text_color = kwargs.get("text_color")
        self._text.configure(state="normal")
        text = sep.join(str(a) for a in args) + end
        if text_color is not None:
            tag = f"tc_{str(text_color).lstrip('#')}"
            self._text.tag_configure(tag, foreground=text_color)
            self._text.insert("end", text, tag)
        else:
            self._text.insert("end", text)
        self._text.see("end")
        self._text.configure(state=self._end_state())
        return self

    @property
    def line_count(self) -> int:
        """TText lines currently held (0 while empty).

        The trailing newline every :meth:`write` leaves behind does not
        count as a line of its own, so the number matches what the user
        sees — and what the log ring buffer trims against.
        """
        if self._text is None:
            return 0
        content = self._text.get("1.0", "end-1c")
        if not content:
            return 0
        lines = content.count("\n") + 1
        if content.endswith("\n"):
            # the newline every write leaves behind terminates the last
            # line, it does not open a line of its own
            lines -= 1
        return lines

    def logger(self, **options: Any) -> "Logger":
        """This element's :class:`~TkSimpleGUI.Logger`, created on first use.

        ``options`` configure it at creation time (``timestamp``,
        ``max_lines``, ``min_level``, ``colors``, ``mirror``); calls after
        the first one return the same logger and ignore them::

            out.logger(max_lines=500, mirror="run.log").info("started")
        """
        if self._logger is None:
            from ..logger import Logger

            self._logger = Logger(self, **options)
        return self._logger

    def log(self, *args: Any, **kwargs: Any):
        """Append one log line: timestamp, level label and level color.

        ``level`` picks the semantic color (debug / info / success /
        warning / error / critical), ``color`` overrides it for this line,
        ``timestamp`` overrides the stamp format::

            out.log("connected")
            out.log("sync failed", level="error")
        """
        kwargs.setdefault("level", "info")
        self.logger().write(*args, **kwargs)
        return self

    def link(
        self,
        text: str,
        key: Optional[ElementKey] = None,
        text_color: Optional[Color] = "#0563c1",
        underline: bool = True,
    ):
        """Append clickable text that posts ``key`` (or the text itself).

        The native tk.Text ``tag_bind`` mechanism turns the word into a
        hyperlink; style it like one by default.
        """
        tag = f"link_{id(text)}"
        self._text.configure(state="normal")
        self._text.tag_configure(
            tag, foreground=text_color,  # ty: ignore[invalid-argument-type]  tkinter drops None
            underline=bool(underline),
        )
        start = self._text.index("end-1c")
        self._text.insert("end", str(text), tag)
        self._text.tag_bind(
            tag, "<Button-1>", lambda _e: self._post_event(key if key is not None else str(text))
        )
        self._text.tag_bind(tag, "<Enter>", lambda _e: self._text.configure(cursor="hand2"))
        self._text.tag_bind(tag, "<Leave>", lambda _e: self._text.configure(cursor=""))
        self._text.see("end")
        self._text.mark_set("insert", start)
        self._text.configure(state=self._end_state())
        return self

    def search_all(self, needle: str, case_sensitive: bool = False, background: str = "#ffe08a"):
        """Highlight every occurrence of ``needle``; returns the match count.

        Matches are tagged with a native tk.Text tag until
        :meth:`clear_highlights` is called.
        """
        needle = str(needle)
        self._text.tag_delete("search_all")
        if not needle:
            return 0
        self._text.tag_configure("search_all", background=background)
        count = 0
        start = "1.0"
        while True:
            pos = self._text.search(
                needle, start, stopindex="end", nocase=not case_sensitive
            )
            if not pos:
                break
            self._text.tag_add("search_all", pos, f"{pos}+{len(needle)}c")
            count += 1
            start = f"{pos}+{len(needle)}c"
        return count

    def clear_highlights(self):
        """Remove tags added by :meth:`search_all`."""
        self._text.tag_delete("search_all")
        return self

    def clear(self):
        """Remove all text."""
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state=self._end_state())
        return self

    def undo(self):
        """Undo the last edit (native tk.Text undo stack)."""
        with contextlib.suppress(tk.TclError):
            self._text.edit_undo()
        return self

    def redo(self):
        """Re-apply the last undone edit (native tk.Text undo stack)."""
        with contextlib.suppress(tk.TclError):
            self._text.edit_redo()
        return self

    # --- native tk.Text API passthrough -----------------------------------------
    def insert(self, index: int, text: str, tags: Any = None):
        """Insert at a tk.Text index ("1.0", "end", ...) — native passthrough."""
        self._text.configure(state="normal")
        self._text.insert(str(index), str(text), tags or ())
        self._text.configure(state=self._end_state())
        return self

    def delete(self, first: str = "1.0", last: Any = None):
        """Delete a range ("1.0".."end") — native passthrough."""
        self._text.configure(state="normal")
        self._text.delete(str(first), "end" if last is None else str(last))
        self._text.configure(state=self._end_state())
        return self

    def see(self, index: int):
        """Scroll so ``index`` ("end", "1.0", ...) is visible — native passthrough."""
        self._text.see(str(index))
        return self

    def update(
        self,
        value: Any = None,
        append: bool = False,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if value is not None:
            self._text.configure(state="normal")
            if append:
                self._text.insert("end", str(value))
                self._text.see("end")
            else:
                self._text.delete("1.0", "end")
                self._text.insert("1.0", str(value))
            self._text.configure(state=self._end_state())
        if disabled is not None:
            self._disabled = bool(disabled)
            self._text.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TOutput(TMultiline):
    """Read only multi line area that other code can print into."""

    __slots__ = ()

    def _create_widget(self, master: tk.Misc):
        container = super()._create_widget(master)
        self._text.configure(state="disabled")
        return container

    def _end_state(self):
        """Always lock again after a write.

        The base implementation only reflects the ``disabled`` constructor
        flag, so a plain TOutput would turn editable as soon as something
        printed into it; an TOutput is read-only by definition and all
        programmatic writes re-enable the widget for their own duration.
        """
        return "disabled"


class TProgressBar(Element):
    """Progress bar (ttk native), determinate or indeterminate.

    ``start_indeterminate()`` runs the native marquee animation until
    ``stop_indeterminate()`` — the ttk "indeterminate" mode that a plain
    value-driven bar cannot show.
    """

    __slots__ = ("_max_value", "_orientation", "_current", "_indeterminate_job")

    def __init__(
        self,
        max_value: float,
        orientation: Optional[str] = "h",
        key: Optional[ElementKey] = None,
        size: Size = C.DEFAULT_PROGRESS_BAR_SIZE,
        current_value: float = 0,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=size,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._max_value = max_value
        self._orientation = orientation
        self._current = current_value
        self._indeterminate_job = None

    def _create_widget(self, master: tk.Misc):
        orient = (
            "horizontal"
            if str(self._orientation).lower() in ("h", "horizontal")
            else "vertical"
        )
        return ttk.Progressbar(
            master, orient=orient, maximum=self._max_value, value=self._current
        )
        return bar

    # --- indeterminate (marquee) mode ---------------------------------------------
    def start_indeterminate(self, interval_ms: int = 50):
        """Run the native marquee animation (stop with stop_indeterminate)."""
        if self._indeterminate_job is not None:
            return self
        self._widget.configure(mode="indeterminate")
        self._widget.start(int(interval_ms))
        return self

    def stop_indeterminate(self):
        """Stop the marquee and return to determinate mode."""
        if self._indeterminate_job is None:
            pass  # stop is idempotent regardless
        self._widget.stop()
        self._widget.configure(mode="determinate")
        return self

    @property
    def max_value(self):
        return self._max_value

    def get(self):
        return self._current

    def update(
        self,
        current_value: Optional[float] = None,
        max_value: Optional[float] = None,
        visible: Optional[bool] = None,
        **kwargs: Any):
        if max_value is not None:
            self._max_value = max_value
            self._widget.configure(maximum=max_value)
        if current_value is not None:
            self._current = current_value
            self._widget.configure(value=current_value)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

class TCheckList(Element):
    """Vertical list of checkboxes (Delphi TCheckListBox equivalent).

    ``get()`` returns the list of currently checked values; clicking an item
    posts the element's key when ``enable_events`` is on::

        ts.TCheckList(["a", "b", "c"], default_checked=["b"], key="-CHECKS-")
    """

    __slots__ = (
        "_values",
        "_default_checked",
        "_checked_vars",
        "_enable_events",
        "_text_color",
        "_background_color",
        "_font",
    )

    def __init__(
        self,
        values: Iterable[Any] = (),
        default_checked: Sequence[Any] = (),
        key: Optional[ElementKey] = None,
        enable_events: bool = True,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._values = [str(value) for value in values]
        self._default_checked = {str(value) for value in default_checked}
        self._checked_vars = {}
        self._enable_events = enable_events
        self._text_color = text_color
        self._background_color = background_color
        self._font = font

    def _create_widget(self, master: tk.Misc):
        kwargs = {}
        bg = theme_mod.theme_manager.effective_background(self._background_color)
        if bg is not None:
            kwargs["background"] = bg
        frame = tk.Frame(master, **kwargs)
        self._build_items(frame)
        return frame

    def _item_style(self, master: tk.Misc):
        """Derived TCheckbutton style for the items (base style when unstyled)."""
        return theme_mod.theme_manager.ttk_widget_style(
            master, "TCheckbutton",
            foreground=self._text_color,
            background=self._background_color,
            font=self._font,
        )

    def _build_items(self, frame: Any):
        for child in frame.winfo_children():
            child.destroy()
        self._checked_vars = {}
        checked = self._default_checked
        style_name = self._item_style(frame)
        for value in self._values:
            variable = tk.BooleanVar(value=value in checked, master=frame)
            button = ttk.Checkbutton(
                frame,
                text=value,
                variable=variable,
                style=style_name,
                command=self._on_change,
            )
            button.pack(fill="x")
            self._checked_vars[value] = variable

    def apply_theme(self):
        bg = theme_mod.theme_manager.effective_background(self._background_color)
        if bg is None:
            bg = theme_mod.native_widget_colors(
                tk.Frame, self._widget, ("background",)
            )["background"]
        self._widget.configure(background=bg)
        style_name = self._item_style(self._widget)
        for button in self._widget.winfo_children():
            button.configure(style=style_name)
        return self

    def _on_change(self):
        if self._enable_events:
            self._post_event()

    @property
    def values(self):
        return list(self._values)

    def get(self):
        """List of the currently checked values (in list order)."""
        return [
            value
            for value, variable in self._checked_vars.items()
            if variable.get()
        ]

    def update(
        self,
        values: Optional[Iterable[Any]] = None,
        checked: Optional[Sequence[Any]] = None,
        visible: Optional[bool] = None):
        if values is not None:
            self._values = [str(value) for value in values]
            self._default_checked = {
                str(value) for value in (checked or ())
            }
            self._build_items(self._widget)
        elif checked is not None:
            wanted = {str(value) for value in checked}
            for value, variable in self._checked_vars.items():
                variable.set(value in wanted)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def check_all(self):
        """Check every item."""
        for variable in self._checked_vars.values():
            variable.set(True)
        return self

    def uncheck_all(self):
        """Uncheck every item."""
        for variable in self._checked_vars.values():
            variable.set(False)
        return self
