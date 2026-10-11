#!/usr/bin/env python3
"""Miscellaneous elements: status bar, separators and sizegrip."""

import tkinter as tk
from tkinter import ttk

from .base import Element
from .. import _theming as theme_mod

try:
    from typing import Any, Optional, Tuple
except ImportError:
    Any = Optional = Tuple = None


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
        super(StatusBar, self).__init__(
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
        super(VerticalSeparator, self).__init__(
            key=key, visible=visible, pad=pad, metadata=metadata
        )
        self._padding = padding

    def _create_widget(self, master):
        return ttk.Separator(master, orient="vertical")


class HorizontalSeparator(Element):
    """A thin horizontal line."""

    __slots__ = ("_padding",)

    def __init__(self, padding=1, key=None, visible=True, pad=None, metadata=None):
        super(HorizontalSeparator, self).__init__(
            key=key, visible=visible, pad=pad, metadata=metadata
        )
        self._padding = padding

    def _create_widget(self, master):
        return ttk.Separator(master, orient="horizontal")


class Sizegrip(Element):
    """The small triangle that allows resizing a borderless window."""

    __slots__ = ()

    def __init__(self, key=None, visible=True, pad=None, metadata=None):
        super(Sizegrip, self).__init__(key=key, visible=visible, pad=pad, metadata=metadata)

    def _create_widget(self, master):
        return ttk.Sizegrip(master)
