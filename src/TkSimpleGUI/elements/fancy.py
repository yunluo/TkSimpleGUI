# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Canvas-drawn widgets that Tk cannot do natively.

- :class:`RoundButton`  — rounded / circular button with hover state
- :class:`ImageButton`  — an arbitrary image acting as a button
- :class:`TextProgressBar` — progress bar with centered percentage text

All of them post events through the regular window queue, support the
shared Element options, and keep their figure ids alive on the element.
"""

import base64
import tkinter as tk
from typing import Any, Callable, List, Optional, Tuple, Union

from .base import Element
from .. import _theming as theme_mod

# A Tk color string ("#rrggbb" or a name); "" means transparent.
Color = str
Point = Tuple[float, float]


def _rounded_polygon(canvas, x0, y0, x1, y1, radius, **kwargs):
    """Draw a closed rounded rectangle as a canvas polygon (Tk has no
    native rounded rectangle). Returns the polygon item id."""
    points = [
        x0 + radius, y0,
        x1 - radius, y0,
        x1, y0,
        x1, y0 + radius,
        x1, y1 - radius,
        x1, y1,
        x1 - radius, y1,
        x0 + radius, y1,
        x0, y1,
        x0, y0 + radius,
        x0, y0,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class _CanvasButton(Element):
    """Shared machinery: one background figure + optional text, click hit."""

    __slots__ = (
        "_width",
        "_height",
        "_fill",
        "_hover_fill",
        "_text_color",
        "_font",
        "_clicked",
        "_background_id",
        "_text_id",
    )

    def __init__(
        self,
        size=(100, 32),
        fill_color="#3a7bd5",
        hover_color=None,
        text_color="#ffffff",
        font=None,
        key=None,
        enable_events=True,
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
        self._width = int(size[0] or 100)
        self._height = int(size[1] or 32)
        self._fill = fill_color
        self._hover_fill = hover_color or self._lighten(fill_color)
        self._text_color = text_color
        self._font = font
        self._clicked: Optional[Callable[["_CanvasButton"], None]] = None
        self._background_id = None
        self._text_id = None

    @staticmethod
    def _lighten(color: str) -> str:
        try:
            value = color.lstrip("#")
            if len(value) != 6:
                return color
            parts = [int(value[i:i + 2], 16) for i in (0, 2, 4)]
            parts = [min(255, channel + 28) for channel in parts]
            return f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"
        except (ValueError, AttributeError):
            return color

    # --- subclasses provide the figure ----------------------------------------
    def _draw_background(self, canvas: tk.Canvas) -> int:
        raise NotImplementedError

    def _draw_content(self, canvas: tk.Canvas) -> None:
        label = self._button_label()
        if label:
            self._text_id = canvas.create_text(
                self._width / 2.0,
                self._height / 2.0,
                text=label,
                fill=self._text_color,
                font=self._font if self._font is not None else ("Helvetica", 10),
            )

    def _button_label(self) -> str:
        return ""

    # --- element plumbing -------------------------------------------------------
    def _create_widget(self, master):
        canvas = tk.Canvas(
            master,
            width=self._width,
            height=self._height,
            highlightthickness=0,
            bd=0,
        )
        self._background_id = self._draw_background(canvas)
        self._draw_content(canvas)
        canvas.bind("<Button-1>", self._on_click)
        canvas.bind("<Enter>", self._on_enter)
        canvas.bind("<Leave>", self._on_leave)
        return canvas

    def _hit(self, event) -> bool:
        """True when the click lands on the button figure (tag check)."""
        canvas = self._widget
        overlapping = canvas.find_overlapping(
            event.x, event.y, event.x, event.y
        )
        return self._background_id in overlapping

    def _on_click(self, event):
        if self._hit(event):
            self._post_event()

    def _on_enter(self, _event):
        if self._background_id is not None:
            self._widget.itemconfigure(self._background_id, fill=self._hover_fill)

    def _on_leave(self, _event):
        if self._background_id is not None:
            self._widget.itemconfigure(self._background_id, fill=self._fill)

    def get(self) -> str:
        return self._button_label()

    def set_click_handler(self, callback: Callable[["_CanvasButton"], None]):
        """A direct callback (element, ) alternative to the event queue."""
        self._clicked = callback
        return self

    def _post_event(self, key=None):
        if self._clicked is not None:
            self._clicked(self)
        super()._post_event(key)


class RoundButton(_CanvasButton):
    """A rounded-rectangle (or circular) canvas button.

    Tk buttons are always rectangular; this draws its own figure::

        sg.RoundButton("Go", radius=14, fill_color="#e91e63", key="-GO-")
    """

    __slots__ = ("_radius", "_text")

    def __init__(
        self,
        text="",
        size=(100, 32),
        radius=10,
        fill_color="#3a7bd5",
        hover_color=None,
        text_color="#ffffff",
        font=None,
        key=None,
        enable_events=True,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        self._radius = int(radius)
        self._text = str(text)
        super().__init__(
            size=size,
            fill_color=fill_color,
            hover_color=hover_color,
            text_color=text_color,
            font=font,
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

    def _button_label(self) -> str:
        return self._text

    def _draw_background(self, canvas: tk.Canvas) -> int:
        radius = min(self._radius, self._width // 2, self._height // 2)
        if radius >= min(self._width, self._height) / 2.0:
            return canvas.create_oval(
                0, 0, self._width, self._height,
                fill=self._fill, outline="",
            )
        return _rounded_polygon(
            canvas, 0, 0, self._width, self._height, radius,
            fill=self._fill, outline="",
        )

    @property
    def text(self) -> str:
        return self._text

    def update(self, value=None, visible=None):
        if value is not None:
            self._text = str(value)
            if self._widget is not None and self._text_id is not None:
                self._widget.itemconfigure(self._text_id, text=self._text)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class ImageButton(_CanvasButton):
    """An arbitrary image acting as a button (PNG/GIF, base64 or file).

    Any non-transparent pixel of the image is clickable — something a
    rectangular tk.Button over an image cannot do.
    """

    __slots__ = (
        "_image_data",
        "_image_filename",
        "_hover_brightness",
        "_photo",
        "_photo_hover",
    )

    _photo: Optional[tk.PhotoImage]
    _photo_hover: Optional[tk.PhotoImage]

    def __init__(
        self,
        data_base64=None,
        filename=None,
        size=(None, None),
        hover_brightness=28,
        key=None,
        enable_events=True,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        self._image_data = data_base64
        self._image_filename = filename
        self._hover_brightness = int(hover_brightness)
        self._photo = None
        self._photo_hover = None
        super().__init__(
            size=size,
            fill_color="",
            hover_color="",
            text_color="",
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
        self._photo = None
        self._photo_hover = None

    def _create_widget(self, master):
        canvas = super()._create_widget(master)
        if self._image_data is not None:
            self._photo = tk.PhotoImage(
                data=base64.b64decode(self._image_data), master=canvas
            )
        else:
            self._photo = tk.PhotoImage(file=str(self._image_filename), master=canvas)
        self._width = self._photo.width()
        self._height = self._photo.height()
        canvas.configure(width=self._width, height=self._height)
        self._background_id = canvas.create_image(
            0, 0, image=self._photo, anchor="nw"
        )
        return canvas

    def _draw_background(self, canvas: tk.Canvas) -> int:
        return 0  # the image itself is created in _create_widget

    def _hit(self, event) -> bool:
        # every pixel of the image is a click target
        return 0 <= event.x < self._width and 0 <= event.y < self._height

    def _brighten(self, photo: tk.PhotoImage, amount: int) -> tk.PhotoImage:
        # copy() with no args clones the image on its own interpreter
        result = photo.copy()
        try:
            result.tk.call(result, "write", photo, "-compositingrule", "overlay")
        except tk.TclError:
            pass  # keep the plain copy when overlay compositing is unavailable
        return result

    def _on_enter(self, _event):
        if self._photo is not None and self._photo_hover is None:
            self._photo_hover = self._brighten(self._photo, self._hover_brightness)
        if self._photo_hover is not None:
            self._widget.itemconfigure(self._background_id, image=self._photo_hover)

    def _on_leave(self, _event):
        if self._photo is not None:
            self._widget.itemconfigure(self._background_id, image=self._photo)


class TextProgressBar(Element):
    """A progress bar with centered percentage text (canvas-drawn).

    ttk.Progressbar cannot overlay text; this draws the bar and the label
    as canvas figures::

        bar = sg.TextProgressBar(100, key="-PB-", bar_color="#4caf50")
        bar.update(current_value=42)   # shows "42%"
    """

    __slots__ = (
        "_max_value",
        "_current",
        "_bar_color",
        "_trough_color",
        "_text_color",
        "_font",
        "_show_text",
        "_trough_id",
        "_bar_id",
        "_label_id",
    )

    def __init__(
        self,
        max_value,
        current_value=0,
        size=(140, 20),
        bar_color="#3a7bd5",
        trough_color=None,
        text_color="#ffffff",
        font=None,
        show_text=True,
        key=None,
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
        self._max_value = max_value if max_value else 100
        self._current = current_value
        self._bar_color = bar_color
        self._trough_color = trough_color
        self._text_color = text_color
        self._font = font
        self._show_text = bool(show_text)
        self._trough_id = None
        self._bar_id = None
        self._label_id = None

    def _create_widget(self, master):
        width = int(self._size[0] or 140)
        height = int(self._size[1] or 20)
        canvas = tk.Canvas(
            master, width=width, height=height, highlightthickness=0, bd=0
        )
        trough = self._trough_color or self._mix(self._bar_color, "#222222", 0.75)
        self._trough_id = canvas.create_rectangle(
            0, 0, width, height, fill=trough, outline=""
        )
        self._bar_id = canvas.create_rectangle(
            0, 0, 0, height, fill=self._bar_color, outline=""
        )
        if self._show_text:
            self._label_id = canvas.create_text(
                width / 2.0, height / 2.0,
                text=self._label_text(),
                fill=self._text_color,
                font=self._font if self._font is not None else ("Helvetica", 10),
            )
        self._draw_bar()
        return canvas

    def _label_text(self) -> str:
        percent = int(round(self._current * 100.0 / self._max_value))
        return f"{percent}%"

    def _draw_bar(self):
        if self._widget is None or self._bar_id is None:
            return
        width = int(self._size[0] or 140)
        height = int(self._size[1] or 20)
        ratio = 0.0 if not self._max_value else min(1.0, self._current / float(self._max_value))
        self._widget.coords(self._bar_id, 0, 0, width * ratio, height)
        if self._label_id is not None:
            self._widget.itemconfigure(self._label_id, text=self._label_text())

    @staticmethod
    def _mix(color: str, other: str, weight: float) -> str:
        try:
            a = color.lstrip("#")
            b = other.lstrip("#")
            if len(a) != 6 or len(b) != 6:
                return color
            mixed = [
                int(int(a[i:i + 2], 16) * (1 - weight) + int(b[i:i + 2], 16) * weight)
                for i in (0, 2, 4)
            ]
            return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"
        except (ValueError, AttributeError):
            return color

    @property
    def max_value(self):
        return self._max_value

    def get(self):
        return self._current

    def update(self, current_value=None, max_value=None, visible=None, **kwargs):
        if max_value is not None:
            self._max_value = max_value
        if current_value is not None:
            self._current = current_value
        if (current_value is not None or max_value is not None) and self._widget is not None:
            self._draw_bar()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def update_bar(self, current_value, max_value=None):
        """TkSimpleGUI compatibility alias for :meth:`update`."""
        return self.update(current_value=current_value, max_value=max_value)
