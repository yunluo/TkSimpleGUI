#!/usr/bin/env python3
"""Standard input and display widgets for PySimpleGUI4."""

import tkinter as tk
from tkinter import ttk

from .base import Element, InputElement
from .. import constants as C
from .. import _theming as theme_mod
from .. import settings as settings_mod

try:
    from typing import Any, Dict, List, Optional, Tuple
except ImportError:
    Any = Dict = List = Optional = Tuple = None


_SELECT_MODE_MAP = {
    C.SelectMode.SINGLE: tk.SINGLE,
    C.SelectMode.BROWSE: tk.BROWSE,
    C.SelectMode.MULTIPLE: tk.MULTIPLE,
    C.SelectMode.EXTENDED: tk.EXTENDED,
    "single": tk.SINGLE,
    "browse": tk.BROWSE,
    "multiple": tk.MULTIPLE,
    "extended": tk.EXTENDED,
}


def _char_width(size):
    """Width in characters from a (width, height) size pair."""
    if size is None:
        return None
    width = size[0]
    return None if width is None else int(width)


def _char_height(size):
    if size is None:
        return None
    height = size[1]
    return None if height is None else int(height)


class Text(Element):
    """A static label."""

    __slots__ = ("_text", "_text_color", "_background_color", "_justification", "_font", "_enable_events")

    def __init__(
        self,
        text="",
        key=None,
        size=(None, None),
        text_color=None,
        background_color=None,
        font=None,
        justification=None,
        enable_events=False,
        tooltip=None,
        visible=True,
    ):
        super(Text, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._text = "" if text is None else str(text)
        self._text_color = text_color
        self._background_color = background_color
        self._justification = justification or "left"
        self._font = font
        self._enable_events = enable_events

    @property
    def text(self):
        return self._text

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.text_kwargs(
            color=self._text_color, background_color=self._background_color
        )
        kwargs["text"] = self._text
        kwargs["justify"] = self._justification
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        if self._font is not None:
            kwargs["font"] = self._resolve_font(self._font)
        label = ttk.Label(master, **kwargs)
        return label

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<Button-1>", lambda _e: self._post_event())

    def get(self):
        """The displayed text."""
        return self._text

    def update(self, value=None, text_color=None, background_color=None, visible=None):
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
            if visible:
                self.unhide()
            else:
                self.hide()
        return self


class Input(InputElement):
    """Single line text entry (ttk based for a native look)."""

    __slots__ = ("_default_text", "_enable_events", "_password_char", "_textvariable")

    def __init__(
        self,
        default_text="",
        key=None,
        size=(None, None),
        enable_events=False,
        password_char="",
        tooltip=None,
        visible=True,
    ):
        super(Input, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._default_text = "" if default_text is None else str(default_text)
        self._enable_events = enable_events
        self._password_char = password_char
        self._textvariable = None

    def _create_widget(self, master):
        self._textvariable = tk.StringVar(value=self._default_text)
        kwargs = theme_mod.theme_manager.input_kwargs()
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        if self._password_char:
            kwargs["show"] = self._password_char
        entry = ttk.Entry(master, textvariable=self._textvariable, **kwargs)
        return entry

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<KeyRelease>", lambda _e: self._post_event())
        self._widget.bind("<Return>", lambda _e: self._post_event())

    @property
    def default_text(self):
        return self._default_text

    def get(self):
        """Current text."""
        return self._textvariable.get()

    def update(self, value=None, disabled=None, select=None, visible=None):
        if value is not None:
            state = self._widget.cget("state")
            if state == "disabled":
                self._widget.configure(state="normal")
            self._textvariable.set(str(value))
            if state == "disabled":
                self._widget.configure(state="disabled")
        if disabled is not None:
            self._widget.configure(state="disabled" if disabled else "normal")
        if select:
            self._widget.select_range(0, "end")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def set_password_char(self, char):
        """Show ``char`` instead of the typed characters (masking)."""
        self._password_char = char
        self._widget.configure(show=char)
        return self


InputText = Input


class Combo(InputElement):
    """Dropdown combo box (ttk.Combobox)."""

    __slots__ = ("_values", "_default_value", "_enable_events", "_readonly", "_variable")

    def __init__(
        self,
        values=(),
        default_value=None,
        key=None,
        size=(None, None),
        enable_events=False,
        readonly=True,
        tooltip=None,
        visible=True,
    ):
        super(Combo, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._values = list(values)
        self._default_value = default_value
        self._enable_events = enable_events
        self._readonly = readonly
        self._variable = None

    def _create_widget(self, master):
        self._variable = tk.StringVar(
            value="" if self._default_value is None else str(self._default_value)
        )
        kwargs = theme_mod.theme_manager.input_kwargs()
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        combo = ttk.Combobox(
            master,
            textvariable=self._variable,
            values=[str(v) for v in self._values],
            state="readonly" if self._readonly else "normal",
            **kwargs
        )
        return combo

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<ComboboxSelected>>", lambda _e: self._post_event())

    @property
    def values(self):
        return list(self._values)

    def get(self):
        """Currently selected/entered text."""
        return self._variable.get()

    def update(self, value=None, values=None, disabled=None, visible=None):
        if values is not None:
            self._values = list(values)
            self._widget.configure(values=[str(v) for v in self._values])
        if value is not None:
            self._variable.set(str(value))
        if disabled is not None:
            state = "disabled" if disabled else ("readonly" if self._readonly else "normal")
            self._widget.configure(state=state)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class OptionMenu(Combo):
    """Compatibility alias of :class:`Combo` with a non-readonly default."""

    __slots__ = ()

    def __init__(self, values=(), default_value=None, key=None, **kwargs):
        kwargs.setdefault("readonly", False)
        super(OptionMenu, self).__init__(
            values=values, default_value=default_value, key=key, **kwargs
        )


class Listbox(InputElement):
    """Multi item selection list."""

    __slots__ = ("_values", "_select_mode", "_enable_events")

    def __init__(
        self,
        values=(),
        key=None,
        size=C.DEFAULT_LISTBOX_SIZE,
        select_mode=C.SelectMode.BROWSE,
        enable_events=False,
        tooltip=None,
        visible=True,
    ):
        super(Listbox, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._values = list(values)
        self._select_mode = select_mode
        self._enable_events = enable_events

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.input_kwargs()
        kwargs["exportselection"] = False
        width = _char_width(self._size)
        height = _char_height(self._size)
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        mode = _SELECT_MODE_MAP.get(self._select_mode, tk.BROWSE)
        listbox = tk.Listbox(master, selectmode=mode, **kwargs)
        for value in self._values:
            listbox.insert("end", str(value))
        return listbox

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<ListboxSelect>>", lambda _e: self._post_event())

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

    def update(self, values=None, set_to_index=None, select_rows=None, visible=None):
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
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Spin(InputElement):
    """Spinbox with a fixed set of values."""

    __slots__ = ("_values", "_initial_value", "_enable_events", "_variable")

    def __init__(
        self,
        values=(),
        initial_value=None,
        key=None,
        size=(None, None),
        enable_events=False,
        tooltip=None,
        visible=True,
    ):
        super(Spin, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._values = list(values)
        self._initial_value = (
            initial_value if initial_value is not None else (values[0] if values else "")
        )
        self._enable_events = enable_events
        self._variable = None

    def _create_widget(self, master):
        self._variable = tk.StringVar(value=str(self._initial_value))
        kwargs = theme_mod.theme_manager.input_kwargs()
        width = _char_width(self._size)
        if width is not None:
            kwargs["width"] = width
        spin = tk.Spinbox(
            master,
            values=[str(v) for v in self._values],
            textvariable=self._variable,
            state="readonly",
            **kwargs
        )
        return spin

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<Increment>>", lambda _e: self._post_event())
            self._widget.bind("<<Decrement>>", lambda _e: self._post_event())
            self._widget.bind("<Return>", lambda _e: self._post_event())

    def get(self):
        return self._variable.get()

    def update(self, value=None, values=None, visible=None):
        if values is not None:
            self._values = list(values)
            self._widget.configure(values=[str(v) for v in self._values])
        if value is not None:
            self._variable.set(str(value))
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Checkbox(InputElement):
    """Checkbox with a boolean value."""

    __slots__ = ("_text", "_default", "_enable_events", "_variable")

    def __init__(
        self,
        text,
        default=False,
        key=None,
        enable_events=False,
        tooltip=None,
        visible=True,
    ):
        super(Checkbox, self).__init__(key=key, tooltip=tooltip, visible=visible)
        self._text = text
        self._default = bool(default)
        self._enable_events = enable_events
        self._variable = None

    def _create_widget(self, master):
        self._variable = tk.BooleanVar(value=self._default)
        kwargs = theme_mod.theme_manager.text_kwargs()
        checkbox = ttk.Checkbutton(master, text=self._text, variable=self._variable, **kwargs)
        return checkbox

    def _bind_events(self):
        if self._enable_events:
            self._widget.configure(command=lambda: self._post_event())

    @property
    def text(self):
        return self._text

    def get(self):
        """True when checked."""
        return self._variable.get()

    def update(self, value=None, text=None, disabled=None, visible=None):
        if value is not None:
            self._variable.set(bool(value))
        if text is not None:
            self._text = text
            self._widget.configure(text=text)
        if disabled is not None:
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Radio(InputElement):
    """Radio button sharing a value with every radio of the same group."""

    __slots__ = ("_text", "_group_id", "_default", "_enable_events")

    def __init__(
        self,
        text,
        group_id,
        default=False,
        key=None,
        enable_events=False,
        tooltip=None,
        visible=True,
    ):
        super(Radio, self).__init__(key=key, tooltip=tooltip, visible=visible)
        self._text = text
        self._group_id = group_id
        self._default = bool(default)
        self._enable_events = enable_events

    @property
    def group_id(self):
        return self._group_id

    def _create_widget(self, master):
        group_variable = self._window.radio_group_variable(self._group_id)
        kwargs = theme_mod.theme_manager.text_kwargs()
        radio = ttk.Radiobutton(
            master,
            text=self._text,
            value=self._text,
            variable=group_variable,
            **kwargs
        )
        if self._default:
            group_variable.set(self._text)
        return radio

    def _bind_events(self):
        if self._enable_events:
            self._widget.configure(command=lambda: self._post_event())

    def get(self):
        """True when this radio is the selected one in its group."""
        return self._window.radio_group_variable(self._group_id).get() == self._text

    def update(self, value=None, text=None, disabled=None, visible=None):
        if value:
            self._window.radio_group_variable(self._group_id).set(self._text)
        if text is not None:
            self._text = text
            self._widget.configure(text=text)
        if disabled is not None:
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Slider(InputElement):
    """Horizontal or vertical slider (ttk.Scale for a native look)."""

    __slots__ = ("_range", "_default_value", "_orientation", "_enable_events", "_resolution")

    def __init__(
        self,
        range=(1, 10),
        default_value=None,
        orientation="h",
        key=None,
        enable_events=False,
        resolution=None,
        size=(20, 15),
        tooltip=None,
        visible=True,
    ):
        super(Slider, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._range = range
        self._default_value = (
            default_value if default_value is not None else range[0]
        )
        self._orientation = orientation
        self._enable_events = enable_events
        self._resolution = resolution

    def _create_widget(self, master):
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
        return scale

    def _bind_events(self):
        if self._enable_events:
            self._widget.configure(command=lambda _value: self._post_event())

    def get(self):
        """Current value as float (int when resolution is 1)."""
        value = self._widget.get()
        if self._resolution == 1:
            return int(round(float(value)))
        return float(value)

    def update(self, value=None, range=None, disabled=None, visible=None):
        if range is not None:
            self._range = range
            self._widget.configure(from_=range[0], to=range[1])
        if value is not None:
            self._widget.set(value)
        if disabled is not None:
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Multiline(InputElement):
    """Multi line text area."""

    __slots__ = ("_default_text", "_enable_events")

    def __init__(
        self,
        default_text="",
        key=None,
        size=(40, 5),
        enable_events=False,
        enter_submits=False,
        tooltip=None,
        visible=True,
    ):
        super(Multiline, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._default_text = "" if default_text is None else str(default_text)
        self._enable_events = enable_events

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.input_kwargs()
        width = _char_width(self._size)
        height = _char_height(self._size)
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        text = tk.Text(master, **kwargs)
        text.insert("1.0", self._default_text)
        return text

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<KeyRelease>", lambda _e: self._post_event())
        self._widget.bind("<Return>", self._on_return)

    def _on_return(self, event):
        if self._enable_events:
            self._post_event()
        return event

    def get(self):
        """Full contents (without the trailing newline)."""
        return self._widget.get("1.0", "end-1c")

    def print(self, *args, **kwargs):
        """Append text (``print`` style)."""
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        self._widget.configure(state="normal")
        self._widget.insert("end", sep.join(str(a) for a in args) + end)
        self._widget.see("end")
        self._widget.configure(state="disabled")
        return self

    def update(self, value=None, append=False, disabled=None, visible=None):
        if value is not None:
            self._widget.configure(state="normal")
            if append:
                self._widget.insert("end", str(value))
                self._widget.see("end")
            else:
                self._widget.delete("1.0", "end")
                self._widget.insert("1.0", str(value))
            self._widget.configure(state="disabled")
        if disabled is not None:
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Output(Multiline):
    """Read only multi line area that other code can print into."""

    __slots__ = ()

    def _create_widget(self, master):
        widget = super(Output, self)._create_widget(master)
        widget.configure(state="disabled")
        return widget


class ProgressBar(Element):
    """Progress bar (ttk native)."""

    __slots__ = ("_max_value", "_orientation", "_current")

    def __init__(
        self,
        max_value,
        orientation="h",
        key=None,
        size=C.DEFAULT_PROGRESS_BAR_SIZE,
        current_value=0,
        tooltip=None,
        visible=True,
    ):
        super(ProgressBar, self).__init__(key=key, size=size, tooltip=tooltip, visible=visible)
        self._max_value = max_value
        self._orientation = orientation
        self._current = current_value

    def _create_widget(self, master):
        orient = (
            "horizontal"
            if str(self._orientation).lower() in ("h", "horizontal")
            else "vertical"
        )
        bar = ttk.Progressbar(
            master, orient=orient, maximum=self._max_value, value=self._current
        )
        return bar

    @property
    def max_value(self):
        return self._max_value

    def get(self):
        return self._current

    def update(self, current_value=None, max_value=None, visible=None, **kwargs):
        if max_value is not None:
            self._max_value = max_value
            self._widget.configure(maximum=max_value)
        if current_value is not None:
            self._current = current_value
            self._widget.configure(value=current_value)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def update_bar(self, current_value, max_value=None):
        """PySimpleGUI compatibility alias for :meth:`update`."""
        return self.update(current_value=current_value, max_value=max_value)
