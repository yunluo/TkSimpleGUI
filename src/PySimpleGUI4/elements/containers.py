#!/usr/bin/env python3
"""Container elements: Frame, Column, Tab, TabGroup and Menu."""

import tkinter as tk
from tkinter import ttk

from .base import ContainerElement, Element, _validate_layout
from .. import constants as C
from .. import _theming as theme_mod

try:
    from typing import Any, List, Optional, Tuple
except ImportError:
    Any = List = Optional = Tuple = None


class Frame(ContainerElement):
    """A labelled frame holding a nested layout."""

    __slots__ = ("_title",)

    def __init__(
        self,
        title,
        layout,
        key=None,
        size=(None, None),
        tooltip=None,
        visible=True,
    ):
        super(Frame, self).__init__(layout=layout, key=key, size=size, tooltip=tooltip, visible=visible)
        self._title = title

    @property
    def title(self):
        return self._title

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.text_kwargs()
        width = self._size[0] if self._size else None
        if width is not None:
            kwargs["width"] = int(width)
        frame = ttk.Labelframe(master, text=self._title, **kwargs)
        return frame

    def update(self, value=None, visible=None):
        if value is not None:
            self._title = value
            self._widget.configure(text=value)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Column(ContainerElement):
    """An invisible container holding a nested layout."""

    __slots__ = ("_background_color", "_vertical_alignment")

    def __init__(
        self,
        layout,
        key=None,
        size=(None, None),
        background_color=None,
        vertical_alignment=None,
        tooltip=None,
        visible=True,
    ):
        super(Column, self).__init__(layout=layout, key=key, size=size, tooltip=tooltip, visible=visible)
        self._background_color = background_color
        self._vertical_alignment = vertical_alignment

    def _create_widget(self, master):
        kwargs = {}
        bg = self._background_color or theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["style"] = "Custom.TFrame"
            kwargs["background"] = bg
        frame = tk.Frame(master, **kwargs)
        return frame

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Tab(ContainerElement):
    """A single tab page; must live inside a :class:`TabGroup`."""

    __slots__ = ("_title",)

    def __init__(self, title, layout, key=None, visible=True):
        super(Tab, self).__init__(layout=layout, key=key, visible=visible)
        self._title = title

    @property
    def title(self):
        return self._title

    def _create_widget(self, master):
        kwargs = {}
        bg = theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        frame = ttk.Frame(master, **kwargs)
        return frame

    def update(self, title=None, visible=None):
        if title is not None:
            self._title = title
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TabGroup(Element):
    """Notebook of :class:`Tab` elements."""

    __slots__ = ("_tabs",)

    def __init__(self, layout, key=None, tab_location=C.Location.TOP, tooltip=None, visible=True):
        super(TabGroup, self).__init__(key=key, tooltip=tooltip, visible=visible)
        rows = _validate_layout(layout)
        tabs = []
        for row in rows:
            for element in row:
                if not isinstance(element, Tab):
                    raise TypeError("TabGroup layout may only contain Tab elements")
                tabs.append(element)
        self._tabs = tabs

    @property
    def tabs(self):
        return list(self._tabs)

    def _create_widget(self, master):
        kwargs = {}
        notebook = ttk.Notebook(master, **kwargs)
        for tab in self._tabs:
            widget = tab._build(notebook, self._window)
            notebook.add(widget, text=tab.title)
        return notebook

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Menu(Element):
    """Menu bar built from a PySimpleGUI menu definition.

    The definition is a list of entries: ``["Label", ["Item", "Item2"]]``.
    Items starting with the disable character are disabled; the separator
    line ``"---"`` inserts a separator.
    """

    __slots__ = ("_menu_definition", "_tearoff")

    def __init__(self, menu_definition, key=None, tearoff=False, visible=True):
        super(Menu, self).__init__(key=key, visible=visible)
        self._menu_definition = menu_definition
        self._tearoff = tearoff

    @property
    def menu_definition(self):
        return self._menu_definition

    def _create_widget(self, master):
        menubar = tk.Menu(master.winfo_toplevel(), tearoff=self._tearoff)
        for entry in self._menu_definition:
            self._add_top_level(menubar, entry)
        return menubar

    def _post_create(self):
        window_root = self._window.tk_root
        window_root.configure(menu=self._widget)

    def _add_top_level(self, menubar, entry):
        label, items = entry[0], entry[1]
        label = self._strip_shortcut(label)
        cascade = tk.Menu(menubar, tearoff=self._tearoff)
        self._fill_items(cascade, items)
        menubar.add_cascade(label=label, menu=cascade)

    def _fill_items(self, menu, items):
        for item in items:
            if isinstance(item, list):  # nested submenu
                self._fill_items(menu, item)
                continue
            if item == C.MENU_SEPARATOR_LINE:
                menu.add_separator()
                continue
            disabled = item.startswith(C.MENU_DISABLED_CHARACTER)
            label = self._strip_shortcut(item)
            menu.add_command(label=label, state="disabled" if disabled else "normal")

    @staticmethod
    def _strip_shortcut(label):
        return label.replace(C.MENU_SHORTCUT_CHARACTER, "")

    def update(self, menu_definition=None, visible=None):
        if menu_definition is not None:
            self._menu_definition = menu_definition
            self._widget.delete(0, "end")
            for entry in self._menu_definition:
                self._add_top_level(self._widget, entry)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self
