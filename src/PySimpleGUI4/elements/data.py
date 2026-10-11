#!/usr/bin/env python3
"""Tabular data elements: Table and Tree (both ttk.Treeview based)."""

import tkinter as tk
from tkinter import ttk

from .base import Element
from .. import constants as C
from .. import _theming as theme_mod

try:
    from typing import Any, List, Optional, Tuple
except ImportError:
    Any = List = Optional = Tuple = None


_SELECT_MODE_MAP = {
    C.SelectMode.BROWSE: tk.BROWSE,
    C.SelectMode.EXTENDED: tk.EXTENDED,
    C.SelectMode.MULTIPLE: tk.MULTIPLE,
    C.SelectMode.SINGLE: tk.NONE,
    "browse": tk.BROWSE,
    "extended": tk.EXTENDED,
    "multiple": tk.MULTIPLE,
    "none": tk.NONE,
}


class Table(Element):
    """Rows and columns shown with a ttk.Treeview in headings mode."""

    __slots__ = (
        "_values",
        "_headings",
        "_select_mode",
        "_enable_events",
        "_num_rows",
        "_col_widths",
        "_auto_size_columns",
    )

    def __init__(
        self,
        values=(),
        headings=(),
        key=None,
        select_mode=C.SelectMode.EXTENDED,
        num_rows=C.DEFAULT_TABLE_NUM_ROWS,
        col_widths=None,
        enable_events=True,
        size=(None, None),
        auto_size_columns=True,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(Table, self).__init__(
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
        self._values = [list(row) for row in values]
        self._headings = list(headings)
        self._select_mode = select_mode
        if size is not None and len(size) > 1 and size[1]:
            self._num_rows = int(size[1])
        else:
            self._num_rows = int(num_rows)
        self._enable_events = enable_events
        if col_widths is not None:
            self._col_widths = list(col_widths)
        else:
            self._col_widths = None
        self._auto_size_columns = auto_size_columns

    def _create_widget(self, master):
        kwargs = {}
        mode = _SELECT_MODE_MAP.get(self._select_mode, tk.EXTENDED)
        columns = ["col{}".format(i) for i in range(len(self._headings))]
        tree = ttk.Treeview(
            master,
            columns=columns,
            show="headings",
            selectmode=mode,
            height=self._num_rows,
            **kwargs
        )
        for index, heading in enumerate(self._headings):
            column_id = "col{}".format(index)
            tree.heading(column_id, text=str(heading))
            width = None
            if self._col_widths is not None and index < len(self._col_widths):
                width = self._col_widths[index]
            if width is not None:
                tree.column(column_id, width=int(width))
            elif not self._auto_size_columns:
                tree.column(column_id, stretch=False)
        for row in self._values:
            tree.insert("", "end", values=[str(cell) for cell in row])
        return tree

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<TreeviewSelect>>", lambda _e: self._post_event())

    @property
    def headings(self):
        return list(self._headings)

    @property
    def values(self):
        return [list(row) for row in self._values]

    def get(self):
        """List of the selected rows' values."""
        selection = self._widget.selection()
        result = []
        for item_id in selection:
            result.append([str(v) for v in self._widget.item(item_id, "values")])
        return result

    @property
    def selected_indices(self):
        return list(self._widget.selection())

    def update(self, values=None, select_rows=None, visible=None):
        if values is not None:
            self._values = [list(row) for row in values]
            self._widget.delete(*self._widget.get_children())
            for row in self._values:
                self._widget.insert("", "end", values=[str(cell) for cell in row])
        if select_rows is not None:
            children = self._widget.get_children()
            self._widget.selection_set(
                [children[i] for i in select_rows if 0 <= i < len(children)]
            )
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class Tree(Element):
    """Hierarchical data shown with a ttk.Treeview in tree mode."""

    __slots__ = ("_headings", "_enable_events", "_show_headings", "_num_rows", "_auto_size_columns")

    def __init__(
        self,
        headings=(),
        key=None,
        num_rows=C.DEFAULT_TABLE_NUM_ROWS,
        enable_events=True,
        show_headings=False,
        auto_size_columns=True,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(Tree, self).__init__(
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
        self._headings = list(headings)
        self._num_rows = int(num_rows)
        self._enable_events = enable_events
        self._show_headings = show_headings
        self._auto_size_columns = auto_size_columns

    def _create_widget(self, master):
        columns = ["col{}".format(i) for i in range(len(self._headings))]
        show = "tree headings" if self._show_headings and self._headings else "tree"
        tree = ttk.Treeview(
            master,
            columns=columns,
            show=show,
            height=self._num_rows,
        )
        tree.heading("#0", text="Tree")
        for index, heading in enumerate(self._headings):
            column_id = "col{}".format(index)
            tree.heading(column_id, text=str(heading))
            tree.column(column_id, width=80)
        return tree

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<TreeviewSelect>>", lambda _e: self._post_event())

    def insert(self, parent, key, display_text=None, values=None):
        """Insert an item; ``parent`` is "" for roots. Returns the item id."""
        item_id = self._widget.insert(
            parent,
            "end",
            iid=str(key),
            text="" if display_text is None else str(display_text),
            values=[str(v) for v in (values or ())],
        )
        return item_id

    def delete(self, key):
        """Delete the item with the given key."""
        self._widget.delete(str(key))
        return self

    def update(self, visible=None):
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def get(self):
        selection = self._widget.selection()
        return list(selection)
