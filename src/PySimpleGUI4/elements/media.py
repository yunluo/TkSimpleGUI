#!/usr/bin/env python3
"""Image, canvas and graph elements."""

import base64
import tkinter as tk
from typing import List, Optional, Tuple, Union

from .base import Element
from .. import _theming as theme_mod

# A drawing point in user/graph coordinates.
Point = Tuple[float, float]
# An image source: base64 bytes or a file path.
ImageSource = Union[bytes, str]



class Image(Element):
    """Displays a PNG/GIF image from a file or base64 data."""

    __slots__ = (
        "_filename",
        "_data_base64",
        "_photo",
        "_zoom",
        "_subsample",
        "_enable_animation",
        "_animation_job",
        "_frames",
        "_frame_index",
        "_frame_delay",
    )

    # the current frame's PhotoImage; None only before the source is set
    _photo: Optional[tk.PhotoImage]

    def __init__(
        self,
        source=None,
        filename=None,
        data_base64=None,
        key=None,
        size=(None, None),
        zoom=None,
        subsample=None,
        enable_animation=True,
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
        self._zoom = zoom
        self._subsample = subsample
        self._animation_job = None
        self._frames = []
        self._frame_index = 0
        self._frame_delay = 100
        self._enable_animation = bool(enable_animation)
        if source is not None and filename is None and data_base64 is None:
            self._filename = source

    def _create_widget(self, master):
        label = tk.Label(master, bd=0, highlightthickness=0)
        self._apply_image(label)
        return label

    def _load_photo(self, master):
        """PhotoImage from the source, honouring zoom/subsample scaling."""
        if self._data_base64 is not None:
            photo = tk.PhotoImage(data=base64.b64decode(self._data_base64), master=master)
        elif self._filename is not None:
            photo = tk.PhotoImage(file=self._filename, master=master)
        else:
            return None
        if self._zoom is not None and self._zoom != 1:
            zx, zy = self._zoom if isinstance(self._zoom, tuple) else (self._zoom, self._zoom)
            if zx != 1 or zy != 1:
                photo = photo.zoom(int(zx), int(zy))
        if self._subsample is not None and self._subsample != 1:
            sx, sy = self._subsample if isinstance(self._subsample, tuple) else (self._subsample, self._subsample)
            if sx != 1 or sy != 1:
                photo = photo.subsample(int(sx), int(sy))
        return photo

    def _apply_image(self, label):
        self._stop_animation()
        self._photo = self._load_photo(label)
        if self._photo is not None:
            label.configure(image=self._photo)
        if self._enable_animation:
            self._start_animation_if_gif(label)

    # --- GIF animation (PhotoImage format subimage frames) -----------------------
    def _photo_kwargs(self):
        """Source kwargs for constructing additional PhotoImage frames."""
        if self._data_base64 is not None:
            return {"data": base64.b64decode(self._data_base64)}
        return {"file": self._filename}

    def _gif_frame_count(self, label):
        """Return True when the source GIF has a second frame (animated)."""
        probe = tk.PhotoImage(
            format="gif -index 1", **self._photo_kwargs(), master=label
        )
        # Tk raises TclError when the index is out of range; success means
        # there are at least 2 frames
        del probe
        return True

    def _start_animation_if_gif(self, label):
        """Load every GIF frame and start an ``after`` loop when animated."""
        try:
            self._gif_frame_count(label)
        except tk.TclError:
            return  # single-frame GIF or a PNG (no "-index 1")
        frames = [self._photo]
        index = 2
        while True:
            try:
                frames.append(tk.PhotoImage(
                    format=f"gif -index {index}",
                    **self._photo_kwargs(),
                    master=label,
                ))
            except tk.TclError:
                break
            index += 1
        if len(frames) <= 1:
            return
        self._frames = frames
        self._frame_index = 0
        self._frame_delay = 100  # ~10 fps default; animation_control() retunes
        self._start_animation(label)

    def _animate(self, label):
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        label.configure(image=self._frames[self._frame_index])
        self._animation_job = label.after(self._frame_delay, lambda: self._animate(label))

    def _start_animation(self, label):
        if self._animation_job is None and len(self._frames) > 1:
            self._animation_job = label.after(self._frame_delay, lambda: self._animate(label))

    def _stop_animation(self):
        if self._animation_job is not None and self._widget is not None:
            try:
                self._widget.after_cancel(self._animation_job)
            except tk.TclError:
                pass
            self._animation_job = None

    def animation_control(self, start=True, delay=None):
        """Start or pause a GIF animation manually. Returns self."""
        if delay is not None:
            self._frame_delay = int(delay)
        if start:
            self._start_animation(self._widget)
        else:
            self._stop_animation()
        return self

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

    def _scroll_command(self):
        """The yview command a standalone :class:`Scrollbar` can drive."""
        return self._widget.yview

    def _on_click(self, event):
        self._post_event()

    def get(self):
        return (self._widget.winfo_width(), self._widget.winfo_height())


class Graph(Canvas):
    """Canvas with a user coordinate system and shape drawing.

    Every ``draw_*`` method returns the canvas figure id. Ids can be used
    with :meth:`delete_figure`, :meth:`move_figure`, :meth:`relocate_figure`,
    :meth:`bring_figure_to_front`, :meth:`send_figure_to_back` and
    :meth:`get_figures_at_location`. With ``enable_events`` a click on the
    canvas posts the graph's key; use ``get_figures_at_location`` inside the
    event loop to find what was clicked. Direct Tk item configuration stays
    available through ``graph.widget.itemconfigure(id, ...)``.
    """

    __slots__ = ("_bottom_left", "_top_right", "_x_scale", "_y_scale", "_images")

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
        super().__init__(
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
        self._images = []

    def _post_create(self):
        super()._post_create()
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

    def draw_oval(self, top_left, bottom_right, fill_color=None, line_color="black", line_width=1):
        """Draw an ellipse bounded by the two corners; returns the item id."""
        x1, y1 = self._to_canvas(top_left)
        x2, y2 = self._to_canvas(bottom_right)
        return self._widget.create_oval(
            x1, y1, x2, y2, fill=fill_color, outline=line_color, width=line_width
        )

    def draw_arc(self, top_left, bottom_right, start_angle=0, extent=90, style="arc", fill_color=None, line_color="black", line_width=1):
        """Draw an arc/pieslice/chord; ``style`` in ("arc", "chord", "pieslice")."""
        x1, y1 = self._to_canvas(top_left)
        x2, y2 = self._to_canvas(bottom_right)
        return self._widget.create_arc(
            x1, y1, x2, y2,
            start=start_angle, extent=extent, style=str(style).lower(),
            fill=fill_color, outline=line_color, width=line_width,
        )

    def draw_polygon(self, points, fill_color=None, line_color="black", line_width=1):
        """Draw a closed polygon from a list of (x, y) points; returns the id."""
        canvas_points = []
        for point in points:
            canvas_points.extend(self._to_canvas(point))
        return self._widget.create_polygon(
            *canvas_points,
            fill=fill_color, outline=line_color, width=line_width
        )

    def draw_image(self, location, filename=None, data_base64=None):
        """Draw a PNG/GIF with its top-left corner at ``location``.

        Returns the canvas item id. The photo is retained by the graph.
        """
        if data_base64 is not None:
            photo = tk.PhotoImage(data=base64.b64decode(data_base64), master=self._widget)
        else:
            photo = tk.PhotoImage(file=str(filename), master=self._widget)
        self._images.append(photo)
        x, y = self._to_canvas(location)
        return self._widget.create_image(x, y, image=photo, anchor="nw")

    def draw_text(self, text, location, color="black", font=None, angle=0):
        """Draw text; returns the canvas item id."""
        x, y = self._to_canvas(location)
        return self._widget.create_text(
            x, y, text=text, fill=color, font=font, angle=angle
        )

    def erase(self):
        """Remove every drawn item."""
        self._widget.delete("all")
        self._images = []
        return self

    # --- figure handles ---------------------------------------------------------
    def delete_figure(self, figure_id):
        """Delete one figure by its canvas id."""
        self._widget.delete(figure_id)
        return self

    def move_figure(self, figure_id, x_direction, y_direction):
        """Move one figure by an offset in graph coordinates."""
        dx = x_direction * self._x_scale
        dy = -y_direction * self._y_scale
        self._widget.move(figure_id, dx, dy)
        return self

    def relocate_figure(self, figure_id, point):
        """Move a figure so its top-left reference point sits at ``point``."""
        coords = self._widget.coords(figure_id)
        if not coords:
            return self
        target_x, target_y = self._to_canvas(point)
        self._widget.move(
            figure_id, target_x - coords[0], target_y - coords[1]
        )
        return self

    def bring_figure_to_front(self, figure_id):
        self._widget.tag_raise(figure_id)
        return self

    def send_figure_to_back(self, figure_id):
        self._widget.tag_lower(figure_id)
        return self

    def get_figures_at_location(self, point):
        """Ids of the figures overlapping ``point`` (topmost first)."""
        x, y = self._to_canvas(point)
        overlapping = self._widget.find_overlapping(x - 1, y - 1, x + 1, y + 1)
        return list(reversed(overlapping))

    def move(self, x_direction, y_direction):
        """Move all drawn items (in graph coordinates)."""
        dx = x_direction * self._x_scale
        dy = -y_direction * self._y_scale
        self._widget.move("all", dx, dy)
        return self


class Shape(Element):
    """Static decorative shape (Delphi TShape/TBevel equivalent).

    ``shape_type``: "rectangle", "oval", "triangle" or "line".
    """

    __slots__ = (
        "_shape_type",
        "_fill_color",
        "_line_color",
        "_line_width",
        "_enable_events",
    )

    _SHAPES = ("rectangle", "oval", "triangle", "line")

    def __init__(
        self,
        shape_type="rectangle",
        size=(40, 20),
        fill_color=None,
        line_color="black",
        line_width=1,
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
        shape_type = str(shape_type).lower()
        if shape_type not in self._SHAPES:
            raise ValueError(
                f"shape_type must be one of {self._SHAPES!r}"
            )
        self._shape_type = shape_type
        self._fill_color = fill_color
        self._line_color = line_color
        self._line_width = line_width
        self._enable_events = bool(enable_events)

    def _create_widget(self, master):
        kwargs = theme_mod.theme_manager.text_kwargs(background_color=None)
        canvas = tk.Canvas(
            master,
            width=self._size[0] or 40,
            height=self._size[1] or 20,
            highlightthickness=0,
            **kwargs
        )
        width = self._size[0] or 40
        height = self._size[1] or 20
        fill = self._fill_color or ""  # "" = transparent fill
        if self._shape_type == "rectangle":
            canvas.create_rectangle(
                0, 0, width, height,
                fill=fill, outline=self._line_color,
                width=self._line_width,
            )
        elif self._shape_type == "oval":
            canvas.create_oval(
                0, 0, width, height,
                fill=fill, outline=self._line_color,
                width=self._line_width,
            )
        elif self._shape_type == "triangle":
            canvas.create_polygon(
                width / 2.0, 0, width, height, 0, height,
                fill=fill, outline=self._line_color,
                width=self._line_width,
            )
        else:  # line
            canvas.create_line(
                0, height / 2.0, width, height / 2.0,
                fill=self._line_color, width=self._line_width,
            )
        return canvas

    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<Button-1>", lambda _e: self._post_event())

    def get(self):
        return self._shape_type

    def update(self, fill_color=None, line_color=None, visible=None):
        if fill_color is not None:
            self._fill_color = fill_color
            for item in self._widget.find_all():
                if self._widget.type(item) != "line":
                    self._widget.itemconfigure(item, fill=fill_color)
        if line_color is not None:
            self._line_color = line_color
            for item in self._widget.find_all():
                if self._widget.type(item) == "line":
                    self._widget.itemconfigure(item, fill=line_color)
                else:
                    self._widget.itemconfigure(item, outline=line_color)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self
