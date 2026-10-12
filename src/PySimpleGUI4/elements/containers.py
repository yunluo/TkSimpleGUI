#!/usr/bin/env python3
"""Container elements: Frame, Column, Tab, TabGroup and Menu."""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast

from .base import ContainerElement, Element, _validate_layout
from .widgets import Input, Text
from .. import constants as C
from .. import _theming as theme_mod



class Frame(ContainerElement):
    """A labelled frame holding a nested layout.

    ``label_anchor`` places the title ("nw", "n", "ne", "en", "e", "es",
    "se", "s", "sw", "wn", "w", "ws") — the native ttk.Labelframe option.
    """

    __slots__ = ("_title", "_label_anchor")

    def __init__(
        self,
        title,
        layout,
        key=None,
        size=(None, None),
        label_anchor="nw",
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
        self._label_anchor = label_anchor

    @property
    def title(self):
        return self._title

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.text_kwargs()
        width = self._size[0] if self._size else None
        if width is not None:
            kwargs["width"] = int(width)
        anchor = cast(
            Literal["nw", "n", "ne", "en", "e", "es", "se", "s", "sw", "wn", "w", "ws"],
            str(self._label_anchor).lower(),
        )
        frame = ttk.Labelframe(
            master, text=self._title, labelanchor=anchor, **kwargs
        )
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
        super().__init__(
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
        super().__init__(
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
    """Notebook of :class:`Tab` elements.

    With ``enable_events=True`` switching tabs posts the tab's title (or
    ``(key, title)`` when the group has a key). ``enable_traversal`` adds
    Ctrl+Tab keyboard navigation; individual tabs can be disabled or hidden
    through :meth:`update`. ``enable_close=True`` renders an "×" on every
    tab — ttk.Notebook has no native close button, so a click in the
    trailing hit-zone of a tab is detected manually and posted as
    ``(key, "tab_closed", title)`` (or ``("tab_closed", title)``).
    """

    _CLOSE_ZONE = 18  # px at the right edge of a tab treated as the ×

    __slots__ = (
        "_tabs",
        "_enable_events",
        "_enable_traversal",
        "_enable_close",
        "_closed_titles",
    )

    def __init__(
        self,
        layout,
        key=None,
        tab_location=C.Location.TOP,
        enable_events=True,
        enable_traversal=False,
        enable_close=False,
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
        rows = _validate_layout(layout)
        tabs = []
        for row in rows:
            for element in row:
                if not isinstance(element, Tab):
                    raise TypeError("TabGroup layout may only contain Tab elements")
                tabs.append(element)
        self._tabs = tabs
        self._enable_events = bool(enable_events)
        self._enable_traversal = bool(enable_traversal)
        self._enable_close = bool(enable_close)
        self._closed_titles: List[str] = []

    @property
    def tabs(self):
        return list(self._tabs)

    def _create_widget(self, master):
        kwargs = {}
        notebook = ttk.Notebook(master, **kwargs)
        for tab in self._tabs:
            widget = tab._build(notebook, self._window)
            label = tab.title if not self._enable_close else f"{tab.title} ×"
            notebook.add(widget, text=label)
        if self._enable_traversal:
            notebook.enable_traversal()
        return notebook

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind(
                "<<NotebookTabChanged>>", self._on_tab_changed
            )
        if self._enable_close:
            self._widget.bind("<Button-1>", self._on_tab_click, add="+")

    def _on_tab_click(self, event):
        """Detect clicks in the trailing × hit-zone of a tab header."""
        try:
            index = self._widget.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
        if index is None or not 0 <= index < len(self._tabs):
            return
        bbox = self._widget.bbox(index)
        if not bbox:
            return
        tab_x, _tab_y, tab_width, _tab_height = bbox
        if event.x >= tab_x + tab_width - self._CLOSE_ZONE:
            title = self._tabs[index].title
            self.close_tab(title)

    def close_tab(self, title):
        """Remove the tab titled ``title`` and post the close event."""
        index = next(
            (i for i, tab in enumerate(self._tabs) if tab.title == title), None
        )
        if index is None:
            return self
        self._tabs.pop(index)
        self._closed_titles.append(title)
        self._widget.forget(index)
        if self._key is not None:
            self._post_event((self._key, "tab_closed", title))
        else:
            self._post_event(("tab_closed", title))
        return self

    @property
    def closed_tabs(self):
        """Titles of the tabs closed through the × button."""
        return list(self._closed_titles)

    def _on_tab_changed(self, _event):
        try:
            index = self._widget.index("current")
        except tk.TclError:
            return
        if 0 <= index < len(self._tabs):
            title = self._tabs[index].title
            if self._key is not None:
                self._post_event((self._key, title))
            else:
                self._post_event(title)

    @property
    def current_tab(self):
        """The title of the currently selected tab."""
        index = self._widget.index("current")
        return self._tabs[index].title if 0 <= index < len(self._tabs) else None

    def select_tab(self, title_or_index):
        """Programmatically select a tab by title or index."""
        if isinstance(title_or_index, int):
            index = title_or_index
        else:
            index = next(
                (i for i, tab in enumerate(self._tabs) if tab.title == title_or_index),
                None,
            )
            if index is None:
                raise ValueError(f"no tab titled {title_or_index!r}")
        self._widget.select(index)
        return self

    def update(self, visible=None, tab=None, tab_state=None):
        """Show/hide the group, or set one tab's state ("normal"/"disabled"/"hidden").

        ``tab`` identifies the target tab by title or index.
        """
        if tab is not None and tab_state is not None:
            if isinstance(tab, int):
                index = tab
            else:
                index = next(
                    (i for i, item in enumerate(self._tabs) if item.title == tab),
                    None,
                )
            if index is not None:
                self._widget.tab(index, state=tab_state)
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
        super().__init__(
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
        super().__init__(
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
        kwargs: Dict[str, Any] = {"sashwidth": int(self._handle_size or 8)}
        bg = self._background_color or theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        paned = tk.PanedWindow(master, orient=orient, **kwargs)
        for layout in self._layouts:
            self._pane_frames.append(tk.Frame(paned))
        return paned

    def _post_create(self):
        super()._post_create()
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

    # created together in _create_widget
    _canvas: tk.Canvas
    _inner_frame: tk.Frame

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
        super().__init__(
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
        self._canvas = None  # ty: ignore[invalid-assignment]
        self._inner_frame = None  # ty: ignore[invalid-assignment]

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
        # NOTE: skip ContainerElement._post_create — it would build the
        # layout into the outer frame; the content belongs in the inner
        # frame that lives inside the canvas
        Element._post_create(self)
        if self._layout:
            self._window._build_layout(self._layout, self._inner_frame)

    # --- mouse wheel -----------------------------------------------------------
    def _scroll_command(self):
        """The yview command a standalone :class:`Scrollbar` can drive."""
        return self._canvas.yview

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


class Toolbar(Element):
    """Row of uniform buttons (Delphi TToolBar equivalent).

    ``tools`` items:

    - ``"Text"`` — a button that posts its text as the event
    - ``("Text", "-KEY-")`` — a button with an explicit key
    - ``("Text", "-KEY-", ["item", "---", "item2"])`` — dropdown button;
      selecting an item posts the item label as the event
    - ``"---"`` — a vertical separator
    """

    __slots__ = ("_tools", "_background_color", "_button_color", "_font", "_buttons")

    def __init__(
        self,
        tools,
        key=None,
        background_color=None,
        button_color=None,
        font=None,
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
        self._tools = list(tools)
        self._background_color = background_color
        self._button_color = button_color
        self._font = font
        self._buttons = {}

    def _create_widget(self, master):
        kwargs = {}
        bg = self._background_color or theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        frame = tk.Frame(master, **kwargs)
        column = 0
        for tool in self._tools:
            if tool == C.MENU_SEPARATOR_LINE:
                separator = ttk.Separator(frame, orient="vertical")
                separator.grid(row=0, column=column, padx=3, sticky="ns")
                column += 1
                continue
            text, tool_key, items = self._parse_tool(tool)
            if items:
                button = self._make_dropdown(frame, text, tool_key, items)
            else:
                button = self._make_button(frame, text, tool_key)
            button.grid(row=0, column=column, padx=1, pady=1)
            column += 1
        return frame

    @staticmethod
    def _parse_tool(tool):
        if isinstance(tool, (list, tuple)):
            text = str(tool[0])
            tool_key = tool[1] if len(tool) > 1 else text
            items = tool[2] if len(tool) > 2 else None
        else:
            text = str(tool)
            tool_key = text
            items = None
        return text, tool_key, items

    def _make_button(self, frame, text, tool_key):
        style_name = theme_mod.theme_manager.ttk_widget_style(
            frame, "TButton", font=self._font
        )
        button = ttk.Button(
            frame,
            text=text,
            style=style_name,
            command=lambda k=tool_key: self._post_event(k),
        )
        self._buttons[tool_key] = button
        return button

    def _make_dropdown(self, frame, text, tool_key, items):
        menu = tk.Menu(frame, tearoff=False)
        for item in items:
            if item == C.MENU_SEPARATOR_LINE:
                menu.add_separator()
                continue
            label = str(item).replace(C.MENU_SHORTCUT_CHARACTER, "")
            menu.add_command(label=label, command=lambda t=label: self._post_event(t))
        button = ttk.Menubutton(frame, text=text + " \u25be", direction="below")
        button.configure(menu=menu)
        self._buttons[tool_key] = button
        return button

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class LabeledEdit(ContainerElement):
    """Label plus input in one element (Delphi TLabeledEdit).

    The key belongs to the :class:`~PySimpleGUI4.elements.widgets.Input`;
    ``window[key]`` and ``values[key]`` behave like a plain Input.
    """

    __slots__ = ("_label", "_label_element", "_input")

    def __init__(
        self,
        label,
        default_text="",
        key=None,
        label_position="above",
        label_size=(None, None),
        input_size=(None, None),
        input_text_color=None,
        input_background_color=None,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        self._label = str(label)
        self._label_element = Text(self._label, size=label_size)
        self._input = Input(
            default_text,
            key=key,
            size=input_size,
            text_color=input_text_color,
            background_color=input_background_color,
        )
        if str(label_position).lower() in ("left", "l"):
            layout = [[self._label_element, self._input]]
        else:
            layout = [[self._label_element], [self._input]]
        super().__init__(
            layout=layout,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )

    @property
    def label(self):
        return self._label

    @property
    def input(self):
        """The embedded :class:`Input` element."""
        return self._input

    def _create_widget(self, master):
        kwargs = {}
        bg = theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        return tk.Frame(master, **kwargs)

    def get(self):
        return self._input.get()

    def update(self, value=None, label=None, visible=None):
        if value is not None:
            self._input.update(value=value)
        if label is not None:
            self._label = str(label)
            self._label_element.update(value=self._label)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class KeyValueEditor(ContainerElement):
    """Editable key/value rows (Delphi TValueListEditor equivalent).

    ``pairs`` is a list of ``(label, value)`` pairs (or a dict).
    ``get()`` returns a ``{label: current_value}`` dict; the container's
    key carries it into ``window.read()`` values.
    """

    __slots__ = ("_labels", "_inputs")

    def __init__(
        self,
        pairs,
        key=None,
        label_size=(None, None),
        value_size=(None, None),
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        if isinstance(pairs, dict):
            pairs = list(pairs.items())
        self._labels = []
        self._inputs = []
        rows = []
        for label, value in pairs:
            label = str(label)
            input_element = Input(
                "" if value is None else str(value), size=value_size
            )
            self._labels.append(label)
            self._inputs.append(input_element)
            rows.append([Text(label, size=label_size), input_element])
        super().__init__(
            layout=rows,
            key=key,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )

    def get(self):
        """``{label: current_value}`` for every row."""
        return dict(
            (label, element.get()) for label, element in zip(self._labels, self._inputs)
        )

    def _create_widget(self, master):
        kwargs = {}
        bg = theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        return tk.Frame(master, **kwargs)

    def update(self, values=None, visible=None):
        if values is not None:
            for label, element in zip(self._labels, self._inputs):
                if label in values:
                    element.update(value=values[label])
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class FlowPanel(Element):
    """Children that flow left-to-right and wrap (Delphi TFlowPanel).

    ``elements`` is a flat list of elements (not rows). Placement is
    recomputed on every resize using tk ``place``; hidden elements are
    skipped. Children manage their own geometry afterwards — don't grid
    them manually.
    """

    __slots__ = (
        "_children",
        "_hpadding",
        "_vpadding",
        "_background_color",
        "_wrap_width",
    )

    def __init__(
        self,
        elements,
        horizontal_padding=5,
        vertical_padding=5,
        wrap_width=600,
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
        self._children = list(elements)
        self._hpadding = horizontal_padding
        self._vpadding = vertical_padding
        self._background_color = background_color
        self._wrap_width = int(wrap_width)

    def _create_widget(self, master):
        kwargs = {}
        bg = self._background_color or theme_mod.theme_manager.background_color
        if bg is not None:
            kwargs["background"] = bg
        return tk.Frame(master, **kwargs)

    def _post_create(self):
        super()._post_create()
        for element in self._children:
            self._window._register_element(element)
            element._build(self._widget, self._window)
        self._widget.bind("<Configure>", self._reflow)
        self._reflow()

    def _reflow(self, _event=None):
        width = self._widget.winfo_width()
        if width <= 1:
            # not mapped yet — lay out against the fallback width and size
            # the frame so its grid cell requests a sensible area
            width = self._wrap_width
            self._widget.configure(width=width)
        x = self._hpadding
        y = self._vpadding
        row_height = 0
        for element in self._children:
            widget = element.widget
            if widget is None:
                continue
            if not element.visible:
                widget.place_forget()
                continue
            child_width = widget.winfo_reqwidth()
            child_height = widget.winfo_reqheight()
            if x + child_width > width and x > self._hpadding:
                x = self._hpadding
                y += row_height + self._vpadding
                row_height = 0
            widget.place(x=x, y=y)
            x += child_width + self._hpadding
            row_height = max(row_height, child_height)
        if self._children:
            self._widget.configure(height=y + row_height + self._vpadding)

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
            if visible:
                self._reflow()
        return self
