#!/usr/bin/env python3
"""Image, canvas and graph elements."""

import tkinter as tk

from .base import Element
from .. import _theming as theme_mod

try:
    from typing import Any, Optional, Tuple
except ImportError:
    Any = Optional = Tuple = None


class Image(Element):
    """Displays a PNG/GIF image from a file or base64 data."""

    __slots__ = ("_filename", "_data_base64", "_photo")

    def __init__(
        self,
        source=None,
        filename=None,
        data_base64=None,
        key=None,
        size=(None, None),
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        super(Image, self).__init__(
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
        self._filename = filename
        self._data_base64 = data_base64
        self._photo = None
        if source is not None and filename is None and data_base64 is None:
            self._filename = source

    def _create_widget(self, master):
        label = tk.Label(master, bd=0, highlightthickness=0)
        self._apply_image(label)
        return label

    def _apply_image(self, label):
        self._photo = None
        if self._data_base64 is not None:
            import base64

            self._photo = tk.PhotoImage(
                data=base64.b64decode(self._data_base64), master=label
            )
        elif self._filename is not None:
            self._photo = tk.PhotoImage(file=self._filename, master=label)
        if self._photo is not None:
            label.configure(image=self._photo)

    def update(self, source=None, filename=None, data_base64=None, visible=None):
        if filename is not None:
            self._filename = filename
        if data_base64 is not None:
            self._data_base64 = data_base64
        if source is not None and filename is None and data_base64 is None:
            self._filename = source
        if filename is not None or data_base64 is not None or source is not None:
            self._apply_image(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def get(self):
        return self._filename


class Canvas(Element):
    """A plain drawing canvas."""

    __slots__ = ("_background_color", "_canvas_size")

    def __init__(
        self,
        size=(300, 300),
        background_color=None,
        key=None,
        enable_events=False,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        super(Canvas, self).__init__(
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
        self._canvas_size = size

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.text_kwargs(background_color=self._background_color)
        canvas = tk.Canvas(
            master,
            width=self._canvas_size[0],
            height=self._canvas_size[1],
            highlightthickness=0,
            **kwargs
        )
        return canvas

    def _bind_events(self):
        self._widget.bind("<Button-1>", self._on_click)

    def _on_click(self, event):
        self._post_event()

    def get(self):
        return (self._widget.winfo_width(), self._widget.winfo_height())


class Graph(Canvas):
    """Canvas with a user coordinate system and shape drawing."""

    __slots__ = ("_bottom_left", "_top_right", "_x_scale", "_y_scale")

    def __init__(
        self,
        canvas_size=(300, 300),
        graph_bottom_left=(0, 0),
        graph_top_right=(100, 100),
        background_color=None,
        key=None,
        enable_events=False,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        super(Graph, self).__init__(
            size=canvas_size,
            background_color=background_color,
            key=key,
            enable_events=enable_events,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._bottom_left = graph_bottom_left
        self._top_right = graph_top_right
        self._x_scale = 1.0
        self._y_scale = 1.0

    def _post_create(self):
        super(Graph, self)._post_create()
        self._compute_scale()

    def _compute_scale(self):
        width = float(self._canvas_size[0])
        height = float(self._canvas_size[1])
        graph_width = float(self._top_right[0] - self._bottom_left[0]) or 1.0
        graph_height = float(self._top_right[1] - self._bottom_left[1]) or 1.0
        self._x_scale = width / graph_width
        self._y_scale = height / graph_height

    def _to_canvas(self, point):
        """Convert a graph coordinate pair to canvas pixel coordinates."""
        x = (point[0] - self._bottom_left[0]) * self._x_scale
        y = self._canvas_size[1] - (point[1] - self._bottom_left[1]) * self._y_scale
        return (x, y)

    # --- drawing API -----------------------------------------------------------
    def draw_circle(self, center_location, radius, fill_color=None, line_color="black", line_width=1):
        """Draw a circle; returns the canvas item id."""
        cx, cy = self._to_canvas(center_location)
        r = radius * self._x_scale
        return self._widget.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=fill_color, outline=line_color, width=line_width,
        )

    def draw_line(self, point_from, point_to, color="black", width=1):
        """Draw a line; returns the canvas item id."""
        x1, y1 = self._to_canvas(point_from)
        x2, y2 = self._to_canvas(point_to)
        return self._widget.create_line(x1, y1, x2, y2, fill=color, width=width)

    def draw_point(self, point, size=2, color="black"):
        """Draw a single point; returns the canvas item id."""
        x, y = self._to_canvas(point)
        r = size / 2.0
        return self._widget.create_oval(
            x - r, y - r, x + r, y + r, fill=color, outline=color
        )

    def draw_rectangle(self, top_left, bottom_right, fill_color=None, line_color="black", line_width=1):
        """Draw a rectangle; returns the canvas item id."""
        x1, y1 = self._to_canvas(top_left)
        x2, y2 = self._to_canvas(bottom_right)
        return self._widget.create_rectangle(
            x1, y1, x2, y2, fill=fill_color, outline=line_color, width=line_width
        )

    def draw_text(self, text, location, color="black", font=None, angle=0):
        """Draw text; returns the canvas item id."""
        x, y = self._to_canvas(location)
        return self._widget.create_text(
            x, y, text=text, fill=color, font=font, angle=angle
        )

    def erase(self):
        """Remove every drawn item."""
        self._widget.delete("all")
        return self

    def move(self, x_direction, y_direction):
        """Move all drawn items (in graph coordinates)."""
        dx = x_direction * self._x_scale
        dy = -y_direction * self._y_scale
        self._widget.move("all", dx, dy)
        return self
