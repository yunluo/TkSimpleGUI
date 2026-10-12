# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Miscellaneous elements: status bar, separators, sizegrip, menubutton, scrollbar."""

import tkinter as tk
from tkinter import ttk
from typing import cast
from .._typing_compat import Literal

from .base import Element
from .. import _theming as theme_mod
from .. import constants as C



class StatusBar(Element):
    """Sunken label typically placed at the bottom of a window."""

    __slots__ = ("_text", "_text_color", "_background_color", "_font")

    def __init__(
        self,
        text="",
        key=None,
        text_color=None,
        background_color=None,
        font=None,
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

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.text_kwargs(
            color=self._text_color, background_color=self._background_color
        )
        kwargs.setdefault("relief", tk.SUNKEN)
        kwargs.setdefault("anchor", "w")
        if self._font is not None:
            kwargs["font"] = self._font
        label = tk.Label(master, text=self._text, **kwargs)
        return label

    def get(self):
        return self._text

    def update(self, value=None, visible=None):
        if value is not None:
            self._text = str(value)
            self._widget.configure(text=self._text)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class VerticalSeparator(Element):
    """A thin vertical line."""

    __slots__ = ("_padding",)

    def __init__(self, padding=1, key=None, visible=True, pad=None, metadata=None):
        super().__init__(
            key=key, visible=visible, pad=pad, metadata=metadata
        )
        self._padding = padding

    def _create_widget(self, master):
        return ttk.Separator(master, orient="vertical")


class HorizontalSeparator(Element):
    """A thin horizontal line."""

    __slots__ = ("_padding",)

    def __init__(self, padding=1, key=None, visible=True, pad=None, metadata=None):
        super().__init__(
            key=key, visible=visible, pad=pad, metadata=metadata
        )
        self._padding = padding

    def _create_widget(self, master):
        return ttk.Separator(master, orient="horizontal")


class Sizegrip(Element):
    """The small triangle that allows resizing a borderless window."""

    __slots__ = ()

    def __init__(self, key=None, visible=True, pad=None, metadata=None):
        super().__init__(key=key, visible=visible, pad=pad, metadata=metadata)

    def _create_widget(self, master):
        return ttk.Sizegrip(master)


class Menubutton(Element):
    """A standalone ttk dropdown button (Toolbar uses these internally).

    Selecting a menu item posts the item's label into the window queue.
    """

    __slots__ = ("_text", "_items", "_menu", "_direction")

    _menu: tk.Menu

    def __init__(
        self,
        text,
        items,
        key=None,
        direction="below",
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
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
        self._text = str(text)
        self._items = list(items)
        self._menu = None  # ty: ignore[invalid-assignment]
        self._direction = direction

    def _create_widget(self, master):
        self._menu = tk.Menu(master, tearoff=False)
        for item in self._items:
            if item == C.MENU_SEPARATOR_LINE:
                self._menu.add_separator()
                continue
            label = str(item).replace(C.MENU_SHORTCUT_CHARACTER, "")
            self._menu.add_command(
                label=label, command=lambda t=label: self._post_event(t)
            )
        # narrow the direction to the literal set ttk.Menubutton accepts
        direction = cast(
            Literal["above", "below", "left", "right", "flush"],
            self._direction if self._direction in ("above", "below",
                    "left", "right", "flush") else "below",
        )
        button = ttk.Menubutton(
            master, text=self._text, direction=direction, menu=self._menu
        )
        return button

    @property
    def items(self):
        return list(self._items)

    def update(self, text=None, items=None, visible=None):
        if text is not None:
            self._text = str(text)
            self._widget.configure(text=self._text)
        if items is not None:
            self._items = list(items)
            self._menu.delete(0, "end")
            for item in self._items:
                if item == C.MENU_SEPARATOR_LINE:
                    self._menu.add_separator()
                    continue
                label = str(item).replace(C.MENU_SHORTCUT_CHARACTER, "")
                self._menu.add_command(
                    label=label, command=lambda t=label: self._post_event(t)
                )
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Scrollbar(Element):
    """A standalone scrollbar wired to another element's widget.

    ``target`` is the scrollable element (Multiline, ScrollableColumn,
    Listbox, Canvas…) whose y-view this scrollbar drives.
    """

    __slots__ = ("_target", "_orientation")

    _orientation: str  # always "horizontal" or "vertical"

    def __init__(
        self,
        target,
        orientation="v",
        key=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        metadata=None,
    ):
        super().__init__(
            key=key,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            metadata=metadata,
        )
        self._target = target
        # narrow to the two literals tk.Scrollbar accepts
        self._orientation = (
            "vertical"
            if str(orientation).lower() in ("v", "vertical")
            else "horizontal"
        )

    def _create_widget(self, master):
        widget = tk.Scrollbar(
            master,
            orient=cast(Literal["horizontal", "vertical"], self._orientation),
        )
        command = getattr(self._target, "_scroll_command", None)
        if command is None:
            raise TypeError(
                f"{type(self._target).__name__} cannot be scrolled by a "
                "Scrollbar (missing _scroll_command)"
            )
        widget.configure(command=command())
        return widget

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self
