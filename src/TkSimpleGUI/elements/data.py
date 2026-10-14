#!/usr/bin/env python3
"""Tabular data elements: Table and Tree (both ttk.Treeview based)."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, cast
from .._typing_compat import Literal

from .base import Element
from .. import constants as C
from .. import enums as E
import contextlib



# ttk.Treeview's ``selectmode`` only accepts three string values:
# ``"browse"``, ``"extended"`` and ``"none"`` (Tk 8.6+). MULTIPLE is
# mapped to ``"extended"`` because Ctrl/Shift-click multi-selection is
# the closest semantic match; SINGLE has no Treeview equivalent and is
# mapped to ``"none"`` (no selection allowed).
_TREEVIEW_SELECT_MODE_MAP = {
    E.SelectMode.BROWSE: "browse",
    E.SelectMode.EXTENDED: "extended",
    E.SelectMode.MULTIPLE: "extended",
    E.SelectMode.SINGLE: "none",
    "browse": "browse",
    "extended": "extended",
    "multiple": "extended",
    "single": "none",
}


class Table(Element):
    """Rows and columns shown with a ttk.Treeview in headings mode.

    Clicking a heading sorts the rows by that column (click again to flip
    the direction); the same behaviour is available programmatically through
    :meth:`sort_by`. With ``enable_edit=True`` double-clicking a cell opens
    an inline editor; committing posts a ``(key, row, col, new_value)``
    tuple event. ``row_icons`` assigns one icon per row (bytes = base64
    data, str = filename). ``col_widths`` are column widths in characters.
    """

    __slots__ = (
        "_values",
        "_headings",
        "_select_mode",
        "_enable_events",
        "_num_rows",
        "_col_widths",
        "_auto_size_columns",
        "_sort_column",
        "_sort_ascending",
        "_row_icons",
        "_images",
        "_enable_edit",
        "_editor",
        "_records",
    )

    # inline cell editor Entry; None when no edit is in progress
    _editor: Optional[tk.Entry]

    def __init__(
        self,
        values=(),
        headings=(),
        key=None,
        select_mode=E.SelectMode.EXTENDED,
        num_rows=C.DEFAULT_TABLE_NUM_ROWS,
        col_widths=None,
        enable_events=True,
        size=(None, None),
        auto_size_columns=True,
        enable_edit=False,
        row_icons=None,
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
        self._sort_column = None
        self._sort_ascending = True
        self._row_icons = list(row_icons) if row_icons is not None else None
        self._images = []
        self._enable_edit = bool(enable_edit)
        self._editor = None
        self._records = []

    def _create_widget(self, master):
        kwargs = {}
        # the stub narrows selectmode to these three literals
        mode = cast(
            Literal["extended", "browse", "none"],
            _TREEVIEW_SELECT_MODE_MAP.get(self._select_mode, "extended"),
        )
        columns = [f"col{i}" for i in range(len(self._headings))]
        # item images render in the #0 tree column, which "headings" mode
        # hides — include a narrow #0 column when row icons are wanted
        show = "tree headings" if self._row_icons else "headings"
        tree = ttk.Treeview(
            master,
            columns=columns,
            show=show,
            selectmode=mode,
            height=self._num_rows,
            **kwargs
        )
        if self._row_icons:
            tree.column("#0", width=26, stretch=False)
            tree.heading("#0", text="")
        for index, heading in enumerate(self._headings):
            column_id = f"col{index}"
            tree.heading(
                column_id,
                text=str(heading),
                command=lambda idx=index: self._on_heading_click(idx),
            )
            width = None
            if self._col_widths is not None and index < len(self._col_widths):
                width = self._col_widths[index]
            if width is not None:
                tree.column(column_id, width=int(width) * 10)  # chars → pixels
            elif not self._auto_size_columns:
                tree.column(column_id, stretch=False)
        for row_index, row in enumerate(self._values):
            item_id = tree.insert("", "end", values=[str(cell) for cell in row])
            self._apply_row_icon(tree, item_id, row_index)
        if self._enable_edit:
            tree.bind("<Double-1>", self._on_double_click)
        return tree

    # --- row icons ------------------------------------------------------------------
    def _load_image_spec(self, spec):
        """PhotoImage from a row icon spec (bytes = base64, str = filename)."""
        import base64

        if isinstance(spec, bytes):
            photo = tk.PhotoImage(data=base64.b64decode(spec), master=self._widget)
        else:
            photo = tk.PhotoImage(file=spec, master=self._widget)
        self._images.append(photo)
        return photo

    def _apply_row_icon(self, tree, item_id, row_index):
        if self._row_icons is None or row_index >= len(self._row_icons):
            return
        spec = self._row_icons[row_index]
        if spec is None:
            return
        with contextlib.suppress(tk.TclError):
            tree.item(item_id, image=self._load_image_spec(spec))

    # --- data binding (lightweight TDataSource) ---------------------------------------
    def set_records(self, records, headings=None):
        """Replace the table contents with a list of records (dicts or
        attribute-bearing objects).

        Columns come from ``headings`` (explicit order) or from the union
        of record keys in first-appearance order. The original records stay
        available through :attr:`selected_records` and stay in sync with
        cell edits. Preferred name; ``bind(records)`` remains as a
        TkSimpleGUI-compatibility alias.
        """
        self._records = list(records)
        if headings is not None:
            columns = [str(heading) for heading in headings]
        else:
            columns = []
            for record in self._records:
                keys = record.keys() if isinstance(record, dict) else []
                for key in keys:
                    if key not in columns:
                        columns.append(key)
        self._headings = columns
        rows = []
        for record in self._records:
            if isinstance(record, dict):
                rows.append([_record_value(record, column) for column in columns])
            else:
                rows.append([_record_value(record, index) for index, _ in enumerate(columns)])
        self._values = rows
        if self._widget is not None:
            self._rebuild_widget()
        return self

    def bind(self, records=None, **kwargs):  # ty: ignore[invalid-method-override]
        """TkSimpleGUI-compat alias for :meth:`set_records` (or for
        :meth:`Element.bind` if ``records`` is not a sequence)."""
        if not isinstance(records, (list, tuple)):
            return super().bind(records, **kwargs)
        return self.set_records(records)

    def _rebuild_widget(self):
        columns = [f"col{i}" for i in range(len(self._headings))]
        self._widget.configure(columns=columns)
        for index, heading in enumerate(self._headings):
            column_id = f"col{index}"
            self._widget.heading(
                column_id,
                text=str(heading),
                command=lambda idx=index: self._on_heading_click(idx),
            )
        self._widget.delete(*self._widget.get_children())
        for row_index, row in enumerate(self._values):
            item_id = self._widget.insert(
                "", "end", values=[str(cell) for cell in row]
            )
            self._apply_row_icon(self._widget, item_id, row_index)

    @property
    def records(self):
        """The records bound by :meth:`bind` (empty when not bound)."""
        return list(self._records)

    @property
    def selected_records(self):
        """The original records of the currently selected rows."""
        if not self._records:
            return []
        children = self._widget.get_children()
        result = []
        for item_id in self._widget.selection():
            index = children.index(item_id) if item_id in children else None
            if index is not None and index < len(self._records):
                result.append(self._records[index])
        return result

    # --- sorting -------------------------------------------------------------------
    def _on_heading_click(self, column_index):
        self.sort_by(column_index)

    def sort_by(self, column_index, ascending=None):
        """Sort the rows by ``column_index`` (toggles direction by default).

        Rows compare numerically when every cell in the column parses as a
        number, otherwise lexicographically. ``values`` stays in sync.
        """
        if not 0 <= column_index < max(1, len(self._headings)):
            raise IndexError(f"column index out of range: {column_index!r}")
        if ascending is None:
            ascending = not (
                self._sort_column == column_index and self._sort_ascending
            )
        self._sort_column = column_index
        self._sort_ascending = bool(ascending)

        def sort_key(row):
            value = row[column_index] if column_index < len(row) else ""
            try:
                return (0, float(value), "")
            except (TypeError, ValueError):
                return (1, 0.0, str(value))

        order = sorted(
            range(len(self._values)),
            key=lambda index: sort_key(self._values[index]),
            reverse=not ascending,
        )
        self._values = [self._values[index] for index in order]
        if self._records:
            self._records = [
                self._records[index]
                for index in order
                if index < len(self._records)
            ]
        if self._widget is not None:
            self._widget.delete(*self._widget.get_children())
            for row in self._values:
                self._widget.insert("", "end", values=[str(cell) for cell in row])
        return self

    @property
    def sort_column(self):
        """The column currently sorted by (None before the first sort)."""
        return self._sort_column

    @property
    def sort_ascending(self):
        return self._sort_ascending

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<TreeviewSelect>>", lambda _e: self._post_event())
        # Treeview has no native column-resize virtual event; synthesize one
        # from the header separator ButtonRelease
        self._widget.bind("<ButtonRelease-1>", self._on_header_release, add="+")

    def _on_header_release(self, event):
        region = self._widget.identify("region", event.x, event.y)
        if region != "separator":
            return
        column = self._widget.identify_column(event.x)
        try:
            index = int(column.lstrip("#")) - 1
        except ValueError:
            return
        if 0 <= index < len(self._headings):
            width = self._widget.column(f"col{index}", "width")
            self._post_event((self._key, "column_resized", index, width))

    def column_width(self, index):
        """Current pixel width of column ``index``."""
        return self._widget.column(f"col{index}", "width")

    def set_column_width(self, index, width):
        """Set column ``index`` to ``width`` pixels programmatically."""
        self._widget.column(f"col{index}", width=int(width))
        return self

    def see(self, row_index):
        """Scroll so row ``row_index`` is visible (native Treeview.see)."""
        children = self._widget.get_children()
        if 0 <= row_index < len(children):
            self._widget.see(children[row_index])
        return self

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

    def update(self, values=None, select_rows=None, row_icons=None, visible=None):
        if values is not None:
            self._values = [list(row) for row in values]
            self._widget.delete(*self._widget.get_children())
            for row_index, row in enumerate(self._values):
                item_id = self._widget.insert(
                    "", "end", values=[str(cell) for cell in row]
                )
                self._apply_row_icon(self._widget, item_id, row_index)
        if row_icons is not None:
            self._row_icons = list(row_icons)
        if select_rows is not None:
            children = self._widget.get_children()
            self._widget.selection_set(
                [children[i] for i in select_rows if 0 <= i < len(children)]
            )
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    # --- cell editing (double click) --------------------------------------------------
    def _on_double_click(self, event):
        item = self._widget.identify_row(event.y)
        column = self._widget.identify_column(event.x)
        if item and column.startswith("#"):
            self._begin_cell_edit(item, column)

    def _begin_cell_edit(self, item, column):
        """Open an inline editor over ``item``/``column`` ("#1" style)."""
        bbox = self._widget.bbox(item, column)
        if not bbox:
            self._widget.update_idletasks()
            bbox = self._widget.bbox(item, column)
        if not bbox:
            return
        try:
            col_index = int(column.lstrip("#")) - 1
        except ValueError:
            return
        row_index = self._widget.index(item)
        if row_index >= len(self._values) or col_index >= len(
            self._values[row_index]
        ):
            return
        row = self._values[row_index]
        x, y, width, height = bbox
        editor = tk.Entry(self._widget, justify="left", borderwidth=1)
        editor.place(x=x, y=y, width=max(width, 40), height=height)
        editor.insert(0, str(row[col_index]))
        editor.selection_range(0, "end")
        editor.focus_set()
        self._editor = editor
        editor.bind(
            "<Return>",
            lambda _e: self._finish_cell_edit(editor, item, row, row_index, col_index),
        )
        editor.bind(
            "<FocusOut>",
            lambda _e: self._finish_cell_edit(editor, item, row, row_index, col_index),
        )
        editor.bind("<Escape>", lambda _e: self._cancel_cell_edit(editor))

    def _finish_cell_edit(self, editor, item, row, row_index, col_index):
        if self._editor is not editor:
            return
        value = editor.get()
        editor.destroy()
        self._editor = None
        if value != row[col_index]:
            row[col_index] = value
            if self._records and row_index < len(self._records):
                record = self._records[row_index]
                if isinstance(record, dict) and col_index < len(self._headings):
                    record[self._headings[col_index]] = value
            self._widget.item(item, values=[str(cell) for cell in row])
            self._post_event((self._key, row_index, col_index, value))

    def _cancel_cell_edit(self, editor):
        if self._editor is editor:
            editor.destroy()
            self._editor = None


def _record_value(record, key):
    """Cell text from a dict record (key) or object (attribute/index)."""
    if isinstance(record, dict):
        value = record.get(key, "")
    else:
        try:
            value = getattr(record, str(key))
        except AttributeError:
            value = ""
    return "" if value is None else str(value)


class Tree(Element):
    """Hierarchical data shown with a ttk.Treeview in tree mode.

    :meth:`insert` accepts ``image_data`` (base64 bytes) or
    ``image_filename`` to give each item its own icon; the photos are kept
    alive by the tree.
    """

    __slots__ = (
        "_headings",
        "_enable_events",
        "_show_headings",
        "_num_rows",
        "_auto_size_columns",
        "_images",
    )

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
        self._headings = list(headings)
        self._num_rows = int(num_rows)
        self._enable_events = enable_events
        self._show_headings = show_headings
        self._auto_size_columns = auto_size_columns
        self._images = []

    def _create_widget(self, master):
        columns = [f"col{i}" for i in range(len(self._headings))]
        show = "tree headings" if self._show_headings and self._headings else "tree"
        tree = ttk.Treeview(
            master,
            columns=columns,
            show=show,
            height=self._num_rows,
        )
        tree.heading("#0", text="Tree")
        # group-tag styles: bold group rows, muted summary rows (Treeview
        # item tags map to per-row ttk styles — native, but undocumented)
        tree.tag_configure("group", font=("Helvetica", 9, "bold"))
        tree.tag_configure("summary", foreground="#777777")
        for index, heading in enumerate(self._headings):
            column_id = f"col{index}"
            tree.heading(column_id, text=str(heading))
            tree.column(column_id, width=80)
        return tree

    def insert_group(self, parent, key, display_text=None, values=None, open=True):
        """Insert a bold group row (a section header that can be collapsed).

        Children inserted with ``parent=key`` collapse together with it.
        """
        return self._widget.insert(
            parent,
            "end",
            iid=str(key),
            text="" if display_text is None else str(display_text),
            values=[str(v) for v in (values or ())],
            tags=("group",),
            open=bool(open),
        )

    def insert_summary(self, parent, key, display_text=None, values=None):
        """Insert a muted summary row (e.g. a totals line under a group)."""
        return self._widget.insert(
            parent,
            "end",
            iid=str(key),
            text="" if display_text is None else str(display_text),
            values=[str(v) for v in (values or ())],
            tags=("summary",),
        )

    def collapse(self, key):
        """Collapse the subtree under ``key``. Returns self."""
        self._widget.item(str(key), open=False)
        return self

    def expand(self, key):
        """Expand the subtree under ``key``. Returns self."""
        self._widget.item(str(key), open=True)
        return self

    def toggle(self, key):
        """Toggle the open state of the subtree under ``key``."""
        item = str(key)
        self._widget.item(item, open=not self._widget.item(item, "open"))
        return self

    def see(self, key):
        """Scroll so item ``key`` is visible (native Treeview.see)."""
        self._widget.see(str(key))
        return self

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<<TreeviewSelect>>", lambda _e: self._post_event())

    def insert(self, parent, key, display_text=None, values=None,
            image_data=None, image_filename=None):
        """Insert an item; ``parent`` is "" for roots. Returns the item id."""
        kwargs = {}
        if image_data is not None or image_filename is not None:
            import base64

            if image_data is not None:
                photo = tk.PhotoImage(
                    data=base64.b64decode(image_data), master=self._widget
                )
            else:
                photo = tk.PhotoImage(
                    file=str(image_filename), master=self._widget
                )
            self._images.append(photo)
            kwargs["image"] = photo
        self._widget.insert(
            parent,
            "end",
            iid=str(key),
            text="" if display_text is None else str(display_text),
            values=[str(v) for v in (values or ())],
            **kwargs
        )

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
