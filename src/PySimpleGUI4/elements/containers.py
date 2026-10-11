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
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(Frame, self).__init__(
            layout=layout,
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
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(Column, self).__init__(
            layout=layout,
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

    def __init__(
        self,
        title,
        layout,
        key=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(Tab, self).__init__(
            layout=layout,
            key=key,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
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

    def __init__(
        self,
        layout,
        key=None,
        tab_location=C.Location.TOP,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(TabGroup, self).__init__(
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

    def __init__(
        self,
        menu_definition,
        key=None,
        tearoff=False,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(Menu, self).__init__(
            key=key,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            justification=justification,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
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


class Splitter(ContainerElement):
    """Paned container: draggable splitters between nested layouts.

    ``layouts`` is a list of layouts (each a normal list of rows); every
    layout becomes one pane. ``orientation`` "h" stacks panes side by side,
    "v" on top of each other. Delphi's TSplitter / Qt's QSplitter equivalent::

        sg.Splitter([[sg.Text("left")], [sg.Input()]], [[sg.Text("right")]])
    """

    __slots__ = (
        "_layouts",
        "_orientation",
        "_handle_size",
        "_background_color",
        "_pane_frames",
    )

    def __init__(
        self,
        layouts,
        orientation="h",
        handle_size=8,
        key=None,
        background_color=None,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        super(Splitter, self).__init__(
            layout=None,
            key=key,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        if not isinstance(layouts, (list, tuple)) or len(layouts) < 2:
            raise TypeError("Splitter needs a list of at least two layouts")
        self._layouts = [_validate_layout(layout) for layout in layouts]
        self._orientation = orientation
        self._handle_size = handle_size
        self._background_color = background_color
        self._pane_frames = []

    def _create_widget(self, master):
        orient = (
            "horizontal"
            if str(self._orientation).lower() in ("h", "horizontal")
            else "vertical"
        )
        kwargs = {"sashwidth": int(self._handle_size or 8), "sashrelief": "flat"}
        bg = self._background_color or theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        paned = tk.PanedWindow(master, orient=orient, **kwargs)
        for layout in self._layouts:
            self._pane_frames.append(tk.Frame(paned))
        return paned

    def _post_create(self):
        super(Splitter, self)._post_create()
        for frame, layout in zip(self._pane_frames, self._layouts):
            self._widget.add(frame, minsize=20, stretch="always", padx=1, pady=1)
            if layout:
                self._window._build_layout(layout, frame)

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class ScrollableColumn(ContainerElement):
    """A vertically (and optionally horizontally) scrollable container.

    Delphi's TScrollBox equivalent: nested layout content larger than the
    element scrolls with the mouse wheel or scrollbars::

        sg.ScrollableColumn(long_layout, size=(300, 200))
    """

    __slots__ = (
        "_background_color",
        "_scroll_y",
        "_scroll_x",
        "_canvas",
        "_inner_frame",
    )

    def __init__(
        self,
        layout,
        key=None,
        size=(300, 200),
        background_color=None,
        scroll_y=True,
        scroll_x=False,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        super(ScrollableColumn, self).__init__(
            layout=layout,
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
        self._background_color = background_color
        self._scroll_y = bool(scroll_y)
        self._scroll_x = bool(scroll_x)
        self._canvas = None
        self._inner_frame = None

    def _create_widget(self, master):
        kwargs = {}
        bg = self._background_color or theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        outer = tk.Frame(master)
        canvas = tk.Canvas(
            outer,
            width=_width_of(self._size),
            height=_height_of(self._size),
            highlightthickness=0,
            **kwargs
        )
        self._canvas = canvas
        canvas.grid(row=0, column=0, sticky="nsew")
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        if self._scroll_y:
            vbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=vbar.set)
            vbar.grid(row=0, column=1, sticky="ns")
        if self._scroll_x:
            hbar = tk.Scrollbar(outer, orient="horizontal", command=canvas.xview)
            canvas.configure(xscrollcommand=hbar.set)
            hbar.grid(row=1, column=0, sticky="ew")
        self._inner_frame = tk.Frame(canvas, **kwargs)
        canvas.create_window((0, 0), window=self._inner_frame, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind("<Enter>", self._bind_wheel)
        canvas.bind("<Leave>", self._unbind_wheel)
        return outer

    def _post_create(self):
        super(ScrollableColumn, self)._post_create()
        if self._layout:
            self._window._build_layout(self._layout, self._inner_frame)

    # --- mouse wheel -----------------------------------------------------------
    def _bind_wheel(self, _event):
        self._canvas.bind_all("<MouseWheel>", self._on_wheel)
        self._canvas.bind_all("<Button-4>", self._on_wheel)
        self._canvas.bind_all("<Button-5>", self._on_wheel)

    def _unbind_wheel(self, _event):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_wheel(self, event):
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -int(event.delta) // 120
        if self._scroll_y and delta:
            self._canvas.yview_scroll(delta, "units")
        elif self._scroll_x and not self._scroll_y:
            self._canvas.xview_scroll(delta, "units")

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


def _width_of(size):
    return size[0] if size and size[0] else 300


def _height_of(size):
    return size[1] if size and size[1] else 200
