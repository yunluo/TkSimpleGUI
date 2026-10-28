#!/usr/bin/env python3
"""Display widgets: tags, badges, avatars, statistics and status views.

- :class:`TTag`       -- a pill shaped label with an optional close button
- :class:`TBadge`     -- a count or status dot badge
- :class:`TAvatar`    -- a circular image / initials avatar
- :class:`TStatistic` -- a labelled big number with an optional trend arrow
- :class:`TEmpty`     -- the "no data" placeholder with a document icon
- :class:`TResult`    -- a centered status circle, title and subtitle
- :class:`TSkeleton`  -- an animated loading placeholder
- :class:`TAlert`     -- an inline, theme colored message bar
- :class:`TWatermark` -- tiled diagonal text over a blank surface

The canvas widgets share one idiom: :meth:`_draw` erases the canvas and
paints everything from a palette resolved at that moment, so a theme switch
only needs a redraw (``apply_theme``) to follow it. Colors the caller
passed explicitly always win over the derived ones.
"""

import base64
import io
import tkinter as tk
from typing import Any, Dict, Optional, Tuple

from . import _paint
from .base import Color, Element, ElementKey, FontSpec, MenuDefinition, PadSpec, Size
from .. import _theming as theme_mod

# status glyph families, shared by the TResult circle and the TAlert icon
_GLYPH_CHECK = "check"
_GLYPH_CROSS = "cross"
_GLYPH_BANG = "bang"
_GLYPH_INFO = "info"


def _as_pair(size: Any) -> Tuple[Optional[int], Optional[int]]:
    """A ``size`` argument as an ``(width, height)`` pair.

    Accepts ``None`` (both entries unknown), a single int (square) or a
    two item sequence; every present entry is normalised to ``int``.
    """
    if size is None:
        return (None, None)
    if isinstance(size, int):
        return (size, size)
    width = None if size[0] is None else int(size[0])
    height = None if size[1] is None else int(size[1])
    return (width, height)


def _status_glyph(status: str) -> str:
    """The glyph family drawn inside a status circle for ``status``."""
    key = str(status or "info").lower()
    if key in ("success", "check"):
        return _GLYPH_CHECK
    if key in ("error", "danger", "cross"):
        return _GLYPH_CROSS
    if key in ("warning", "warn"):
        return _GLYPH_BANG
    return _GLYPH_INFO


def _font_size(font: Optional[FontSpec]) -> int:
    """The pixel size of a font spec (Pillow works in pixels, Tk in points)."""
    if isinstance(font, (tuple, list)) and len(font) > 1:
        try:
            return max(6, int(font[1]))
        except (TypeError, ValueError):
            return 16
    return 16


def _font_family(font: Optional[FontSpec]):
    """The family name of a font spec, when it names one."""
    if isinstance(font, (tuple, list)) and font:
        return font[0]
    return None


def _resample(image_mod: Any, name: str):
    """A Pillow resampling filter looked up across Pillow versions."""
    try:
        return getattr(image_mod.Resampling, name)
    except AttributeError:  # Pillow < 9.1
        return getattr(image_mod, name)


def _ppm_bytes(image: Any) -> bytes:
    """An RGB Pillow image as P6 PPM bytes (``tk.PhotoImage`` reads PPM)."""
    header = f"P6\n{image.width} {image.height}\n255\n".encode("ascii")
    return header + image.tobytes()


def _pil_font(font_file: Any, size: int):
    """A Pillow font object for a font file (None when it cannot load).

    ``ImageFont`` is imported here because ``_paint.pil_modules`` only
    caches ``(Image, ImageDraw)`` -- Pillow keeps text in a third module.
    """
    try:
        from PIL import ImageFont

        return ImageFont.truetype(font_file, size)
    except Exception:
        return None


def _photo_from_image(image: Any, master: tk.Misc) -> tk.PhotoImage:
    """A tk photo of an RGB Pillow image without needing ImageTk."""
    return tk.PhotoImage(data=_ppm_bytes(image), master=master)


class TTag(Element):
    """A pill shaped label, optionally closable.

    ``effect`` picks the look: ``"light"`` (soft wash, the default),
    ``"dark"`` (solid color) or ``"plain"`` (outline only). Clicking the
    body posts the key when ``enable_events`` is set; clicking the "x"
    hides the tag and posts ``(key, "close")``::

        tag = ts.TTag("New", closable=True, key="-TAG-")
        tag.update(tag_color="#67c23a")

    On a desktop the chip-as-detached-widget is a niche — a tag is more
    often the *content* of a richer row (a listbox cell, a tree row).
    The implementation therefore stays minimal: a canvas pill plus, when
    ``closable=True``, a real ``tk.Button`` placed on top of the "x"
    glyph so the close click goes through tk's native event dispatch
    (no more "did I land on the thin diagonal?" pixel-hunting).
    """

    __slots__ = (
        "_text",
        "_tag_color",
        "_text_color",
        "_effect",
        "_closable",
        "_font",
        "_enable_events",
        "_width",
        "_height",
        "_body_id",
        "_text_id",
        "_close_button",
        "_close_window",
    )

    _body_id: Optional[int]
    _text_id: Optional[int]
    _close_button: Optional[tk.Button]
    _close_window: Optional[int]

    _CLOSE_ZONE = 18  # right-hand strip reserved for the "x", in pixels

    def __init__(
        self,
        text: str = "",
        size: Optional[Size] = None,
        tag_color: Optional[Color] = None,
        text_color: Optional[Color] = None,
        effect: str = "light",
        closable: bool = False,
        font: Optional[FontSpec] = None,
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = "" if text is None else str(text)
        self._tag_color = tag_color
        self._text_color = text_color
        self._effect = str(effect or "light").lower()
        self._closable = bool(closable)
        self._font = font
        self._enable_events = bool(enable_events)
        self._width = 0
        self._height = 0
        self._body_id = None
        self._text_id = None
        self._close_button = None
        self._close_window = None

    # --- geometry -------------------------------------------------------------
    def _font_spec(self):
        return self._font if self._font is not None else ("TkDefaultFont", 10)

    def _geometry(self, widget: Optional[tk.Misc] = None):
        """(width, height): sized to the text plus 10px padding per side."""
        height = self._size[1] or 22
        target = widget if widget is not None else self._widget
        text_width = _paint.measure_text(target, self._text, self._font_spec())
        reserve = self._CLOSE_ZONE if self._closable else 0
        width = self._size[0] or max(40, text_width + 20 + reserve)
        return (int(width), int(height))

    def _style(self, colors: Dict[str, str]) -> Tuple[str, str, str, int]:
        """(fill, text, outline, inset) for the active effect."""
        color = self._tag_color or colors["accent"]
        if self._effect == "dark":
            return (color, theme_mod.contrast_on(color), "", 0)
        if self._effect == "plain":
            return (
                colors["surface"],
                _paint.shade(color, colors, 0.30),
                _paint.tint(color, colors, 0.55),
                1,
            )
        return (
            _paint.tint(color, colors, 0.88),
            _paint.shade(color, colors, 0.30),
            "",
            0,
        )

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        width, height = self._geometry(master)
        self._width = int(width)
        self._height = int(height)
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        if self._closable:
            # embed a real TButton inside the canvas via create_window — it
            # still shows up as a canvas item (so the existing widget
            # contract holds) but the click goes through tk's native event
            # dispatch instead of pixel-hunting on a thin diagonal.
            self._close_button = tk.Button(
                canvas,
                text="\u2715",  # multiplication sign
                relief="flat",
                borderwidth=0,
                padx=0, pady=0,
                background=colors["surface"],
                activebackground=colors["surface"],
                foreground=_paint.shade(
                    self._tag_color or colors["accent"], colors, 0.30
                ),
                font=("TkDefaultFont", 9),
                cursor="hand2",
            )
            # bind on the button itself so the click never bubbles up to
            # the canvas's <Button-1> (which would otherwise suppress the
            # body post but also swallow the close trigger)
            self._close_button.bind("<Button-1>", self._on_close_event, add="+")
            self._close_window = canvas.create_window(
                self._width - self._CLOSE_ZONE, 0,
                window=self._close_button,
                width=self._CLOSE_ZONE, height=self._height,
                anchor="nw",
            )
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        self._body_id = None
        self._text_id = None
        fill, ink, outline, inset = self._style(colors)
        if self._text_color is not None:
            ink = self._text_color
        self._body_id = _paint.capsule(
            canvas,
            inset,
            inset,
            self._width - inset,
            self._height - inset,
            fill=fill,
            outline=outline,
            width=1,
        )
        reserve = self._CLOSE_ZONE if self._closable else 0
        self._text_id = canvas.create_text(
            (self._width - reserve) / 2.0,
            self._height / 2.0,
            text=self._text,
            fill=ink,
            font=self._font_spec(),
        )
        # still draw the × glyph on the canvas so the visual matches even
        # when the click is routed to the button (the button is a flat
        # blank tile over the glyph, so users see the cross)
        if self._closable:
            _paint.cross(
                canvas,
                self._width - 9,
                self._height / 2.0,
                8,
                fill=ink,
                width=1.5,
            )

    def _refresh(self):
        """Re-measure the pill for the current text and redraw it."""
        if self._widget is None:
            return
        width, height = self._geometry(self._widget)
        self._width = int(width)
        self._height = int(height)
        self._widget.configure(width=self._width, height=self._height)
        self._draw(self._widget)
        if self._closable and self._close_button is not None and self._close_window is not None:
            self._widget.coords(self._close_window, self._width - self._CLOSE_ZONE, 0)
            self._widget.itemconfigure(
                self._close_window, width=self._CLOSE_ZONE, height=self._height
            )

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
            if self._closable and self._close_button is not None:
                colors = _paint.palette(self._widget)
                self._close_button.configure(
                    background=colors["surface"],
                    activebackground=colors["surface"],
                    foreground=_paint.shade(
                        self._tag_color or colors["accent"], colors, 0.30
                    ),
                )
        return self

    def _on_close_event(self, _event: tk.Event):
        """Close-button press handler (tk <Button-1> event signature)."""
        return self._perform_close()

    def _perform_close(self):
        """Shared body for both the close button and the canvas hit zone."""
        self.hide()
        if self._key is not None:
            self._post_event((self._key, "close"))
        return "break"

    # --- interaction ------------------------------------------------------------
    def _bind_events(self):
        # the body still posts clicks on the canvas; the embedded close
        # button doubles up: real mouse clicks land on it (tk dispatch),
        # synthesised events (event_generate on the canvas) fall through
        # to _on_click which detects the close zone by pixel x.
        self._widget.bind("<Button-1>", self._on_click)
        if self._closable and self._close_button is not None:
            # let the real button command fire on real clicks (so the
            # event is delivered even if the canvas somehow misses it)
            self._close_button.configure(command=self._perform_close)

    def _on_click(self, event: tk.Event):
        if self._closable and event.x >= self._width - self._CLOSE_ZONE:
            self._perform_close()
            return "break"
        if self._enable_events:
            self._post_event()
        return None

    # --- state ----------------------------------------------------------------
    @property
    def text(self) -> str:
        return self._text

    def get(self) -> str:
        """The tag text (still the last text after the tag was closed)."""
        return self._text

    def update(
        self,
        value: Any = None,
        tag_color: Optional[Color] = None,
        text_color: Optional[Color] = None,
        visible: Optional[bool] = None):
        """Change the text / colors; a new text also re-shows a closed tag."""
        redraw = False
        if value is not None:
            self._text = str(value)
            redraw = True
            self.unhide()
        if tag_color is not None:
            self._tag_color = tag_color
            redraw = True
        if text_color is not None:
            self._text_color = text_color
            redraw = True
        if redraw:
            self._refresh()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TBadge(Element):
    """A count or status dot badge.

    ``value=120, max_value=99`` renders "99+", ``is_dot=True`` renders a
    plain colored dot and ``value=None`` leaves the badge empty (its canvas
    keeps the reserved space in the layout)::

        ts.TBadge(120, max_value=99, key="-BADGE-")
        ts.TBadge(is_dot=True, badge_color="#67c23a")
    """

    __slots__ = (
        "_value",
        "_max_value",
        "_is_dot",
        "_badge_color",
        "_text_color",
        "_font",
        "_enable_events",
        "_width",
        "_height",
    )

    def __init__(
        self,
        value: Any = None,
        max_value: float = 99,
        is_dot: bool = False,
        badge_color: Optional[Color] = None,
        text_color: Optional[Color] = None,
        size: Optional[Size] = None,
        font: Optional[FontSpec] = None,
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._value = value
        self._max_value = max_value
        self._is_dot = bool(is_dot)
        self._badge_color = badge_color
        self._text_color = text_color
        self._font = font
        self._enable_events = bool(enable_events)
        self._width = 0
        self._height = 0

    # --- geometry -------------------------------------------------------------
    def _font_spec(self):
        return self._font if self._font is not None else ("TkDefaultFont", 8, "bold")

    def _label(self) -> str:
        """The badge caption: "99+" past ``max_value``, "" when empty."""
        if self._value is None or self._is_dot:
            return ""
        try:
            number = int(self._value)
        except (TypeError, ValueError):
            return str(self._value)
        if self._max_value is not None and number > self._max_value:
            return f"{self._max_value}+"
        return str(number)

    def _geometry(self, widget: Optional[tk.Misc] = None):
        """(width, height): a dot is square, a count is a pill around the text."""
        if self._value is None and not self._is_dot:
            return (int(self._size[0] or 1), int(self._size[1] or 1))
        if self._is_dot:
            diameter = int(self._size[1] or 10)
            return (diameter, diameter)
        height = int(self._size[1] or 18)
        target = widget if widget is not None else self._widget
        text_width = _paint.measure_text(target, self._label(), self._font_spec())
        width = max(height, text_width + 10, int(self._size[0] or 0))
        return (width, height)

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        width, height = self._geometry(master)
        self._width = int(width)
        self._height = int(height)
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        if self._value is None and not self._is_dot:
            return
        fill = self._badge_color or _paint.DANGER
        if self._is_dot:
            canvas.create_oval(0, 0, self._width, self._height, fill=fill, outline="")
            return
        _paint.capsule(
            canvas, 0, 0, self._width, self._height, fill=fill, outline=""
        )
        canvas.create_text(
            self._width / 2.0,
            self._height / 2.0,
            text=self._label(),
            fill=self._text_color or theme_mod.contrast_on(fill),
            font=self._font_spec(),
        )

    def _refresh(self):
        """Re-measure the badge and redraw it."""
        if self._widget is None:
            return
        width, height = self._geometry(self._widget)
        self._width = int(width)
        self._height = int(height)
        self._widget.configure(width=self._width, height=self._height)
        self._draw(self._widget)

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
        return self

    # --- interaction ------------------------------------------------------------
    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<Button-1>", lambda _event: self._post_event())

    # --- state ----------------------------------------------------------------
    @property
    def value(self):
        return self._value

    @property
    def max_value(self):
        return self._max_value

    def get(self):
        """The badge value (as passed in, never the formatted caption)."""
        return self._value

    def clear(self):
        """TEmpty the badge (``value=None``) and repaint."""
        self._value = None
        self._refresh()
        return self

    def update(
        self,
        value: Any = None,
        is_dot: Optional[bool] = None,
        visible: Optional[bool] = None):
        """Set the value / dot mode; ``None`` leaves an argument unchanged."""
        redraw = False
        if value is not None:
            self._value = value
            redraw = True
        if is_dot is not None:
            self._is_dot = bool(is_dot)
            redraw = True
        if redraw:
            self._refresh()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TAvatar(Element):
    """A circular or rounded avatar, from an image or from text initials.

    An image (``filename`` / ``data_base64``) is cropped to a circle when
    Pillow and ImageTk are available; otherwise the photo is centered as is
    with an outline showing the shape. Without an image the first two
    characters of ``text`` are drawn on a colored circle (or rounded
    square)::

        ts.TAvatar("AZ", background_color="#3a7bd5")
        ts.TAvatar(filename="me.png", size=(56, 56), shape="square")
    """

    __slots__ = (
        "_text",
        "_initials",
        "_filename",
        "_data_base64",
        "_shape",
        "_background_color",
        "_text_color",
        "_font",
        "_enable_events",
        "_width",
        "_height",
        "_photo",
    )

    _photo: Optional[tk.PhotoImage]
    _initials: str

    def __init__(
        self,
        text: Optional[str] = None,
        initials: Any = None,
        filename: Any = None,
        data_base64: Any = None,
        size: int = 40,
        shape: str = "circle",
        background_color: Optional[Color] = None,
        text_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        width, height = _as_pair(size)
        super().__init__(
            key=key,
            size=(width or 40, height or 40),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = "" if text is None else str(text)
        # explicit initials override the default "first 2 chars of text"
        # slice; the default slice is fine for an English name like
        # "Yun Luo" -> "Yu", but the user can spell out exactly what should
        # appear (CJK name: ts.TAvatar("云落", initials="云"))
        self._initials = (
            str(text)[:2] if initials is None else str(initials)
        )
        self._filename = filename
        self._data_base64 = data_base64
        self._shape = str(shape or "circle").lower()
        self._background_color = background_color
        self._text_color = text_color
        self._font = font
        self._enable_events = bool(enable_events)
        self._width = int(self._size[0] or 40)
        self._height = int(self._size[1] or 40)
        self._photo = None

    # --- geometry / fonts ---------------------------------------------------------
    def _geometry(self):
        return (self._width, self._height)

    def _font_spec(self):
        if self._font is not None:
            return self._font
        return ("TkDefaultFont", max(1, int(min(self._width, self._height) * 0.40)), "bold")

    def _initials_text(self) -> str:
        return self._initials

    # --- images -------------------------------------------------------------------
    def _has_image(self) -> bool:
        return self._filename is not None or self._data_base64 is not None

    def _image_source(self):
        """A Pillow-openable source: a file path or a base64 image buffer."""
        if self._filename is not None:
            return str(self._filename)
        if self._data_base64 is not None:
            return io.BytesIO(base64.b64decode(self._data_base64))
        return None

    def _load_photo(self, master: tk.Misc):
        """The plain tk photo of the source image (None when unreadable)."""
        try:
            if self._data_base64 is not None:
                return tk.PhotoImage(data=self._data_base64, master=master)
            return tk.PhotoImage(file=str(self._filename), master=master)
        except Exception:
            return None

    def _circular_photo(self, master: tk.Misc):
        """A true circular crop of the image, or None without Pillow/ImageTk."""
        modules = _paint.pil_modules()
        if not modules:
            return None
        image_mod, draw_mod = modules
        try:
            from PIL import ImageTk
        except Exception:
            return None
        try:
            image = image_mod.open(self._image_source())
            image = image.convert("RGBA")
            image = image.resize(
                (self._width, self._height), _resample(image_mod, "LANCZOS")
            )
            if self._shape != "square":
                mask = image_mod.new("L", (self._width, self._height), 0)
                draw_mod.Draw(mask).ellipse(
                    (0, 0, self._width - 1, self._height - 1), fill=255
                )
                image.putalpha(mask)
            photo = ImageTk.PhotoImage(image, master=master)
        except Exception:
            return None
        return photo

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        self._photo = None
        if self._has_image() and self._draw_photo(canvas, colors):
            return
        fill = self._background_color or colors["accent"]
        self._draw_shape(canvas, fill, "")
        initials = self._initials
        if initials:
            canvas.create_text(
                self._width / 2.0,
                self._height / 2.0,
                text=initials,
                fill=self._text_color or theme_mod.contrast_on(fill),
                font=self._font_spec(),
            )

    def _draw_photo(self, canvas: tk.Canvas, colors: _paint.ColorMap) -> bool:
        """Draw the image path; False falls back to the initials path."""
        photo = self._circular_photo(canvas)
        if photo is not None:
            self._photo = photo
            canvas.create_image(0, 0, anchor="nw", image=photo)
            return True
        photo = self._load_photo(canvas)
        if photo is None:
            return False
        self._photo = photo
        canvas.create_image(
            self._width / 2.0, self._height / 2.0, anchor="center", image=photo
        )
        self._draw_shape(canvas, "", colors["border"], 2)
        return True

    def _draw_shape(self, canvas: tk.Canvas, fill: Any, outline: Any, width: int = 1):
        """The avatar figure: an oval or a rounded square."""
        radius = min(self._width, self._height) * 0.12
        if self._shape == "square":
            _paint.rounded_polygon(
                canvas, 1, 1, self._width - 1, self._height - 1, radius,
                fill=fill, outline=outline, width=width,
            )
        else:
            canvas.create_oval(
                1, 1, self._width - 1, self._height - 1,
                fill=fill, outline=outline, width=width,
            )

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
        return self

    # --- interaction ------------------------------------------------------------
    def _bind_events(self):
        if self._enable_events:
            self._widget.bind("<Button-1>", lambda _event: self._post_event())

    # --- state ----------------------------------------------------------------
    @property
    def text(self) -> str:
        return self._text

    def get(self) -> str:
        """The avatar text (the initials source, even when an image shows)."""
        return self._text

    def update(
        self,
        text: Optional[str] = None,
        filename: Any = None,
        data_base64: Any = None,
        visible: Optional[bool] = None):
        """Swap the text or the image source; ``None`` leaves it unchanged."""
        redraw = False
        if text is not None:
            self._text = str(text)
            redraw = True
        if filename is not None:
            self._filename = filename
            self._data_base64 = None
            redraw = True
        if data_base64 is not None:
            self._data_base64 = data_base64
            self._filename = None
            redraw = True
        if redraw and self._widget is not None:
            self._draw(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TStatistic(Element):
    """A labelled statistic: small caption, big number, optional trend.

    ``precision`` fixes the decimals (``None`` drops the ".0" of whole
    numbers and uses ``{:g}`` otherwise); ``trend`` takes ``"up"``,
    ``"down"`` or a number (positive is up, negative is down) and draws an
    arrow, with the percentage when a number was given::

        ts.TStatistic("Revenue", value=1234.5, prefix="$", trend=12.5)
    """

    __slots__ = (
        "_label",
        "_value",
        "_prefix",
        "_suffix",
        "_precision",
        "_trend",
        "_trend_color",
        "_font",
        "_label_font",
        "_label_color",
        "_value_color",
        "_width",
        "_height",
    )

    _VALUE_FONT = ("TkDefaultFont", 22, "bold")
    _AFFIX_FONT = ("TkDefaultFont", 12)
    _LABEL_FONT = ("TkDefaultFont", 9)
    _BASELINE_MARGIN = 10  # px between the number baseline and the bottom

    def __init__(
        self,
        label: str,
        value: Any = 0,
        prefix: Optional[str] = "",
        suffix: Optional[str] = "",
        precision: Optional[int] = None,
        trend: Any = None,
        trend_color: Optional[Color] = None,
        size: Size = (170, 70),
        font: Optional[FontSpec] = None,
        label_font: Optional[FontSpec] = None,
        label_color: Optional[Color] = None,
        value_color: Optional[Color] = None,
        key: Optional[ElementKey] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._label = "" if label is None else str(label)
        self._value = value
        self._prefix = "" if prefix is None else str(prefix)
        self._suffix = "" if suffix is None else str(suffix)
        self._precision = None if precision is None else max(0, int(precision))
        self._trend = trend
        self._trend_color = trend_color
        self._font = font
        self._label_font = label_font
        self._label_color = label_color
        self._value_color = value_color
        self._width = int(self._size[0] or 170)
        self._height = int(self._size[1] or 70)

    # --- geometry / text ----------------------------------------------------------
    def _geometry(self):
        return (self._width, self._height)

    def _content_width(self, widget: tk.Misc) -> int:
        """Pixel width the value line needs: prefix, number, suffix, trend.

        A big number with a prefix and a trend can outgrow the configured
        ``size``; the canvas grows instead of clipping the text.
        """
        value_font = self._font or self._VALUE_FONT
        width = 0.0
        if self._prefix:
            width += _paint.measure_text(widget, self._prefix, self._AFFIX_FONT)
        width += _paint.measure_text(widget, self._value_text(), value_font)
        if self._suffix:
            width += _paint.measure_text(widget, self._suffix, self._AFFIX_FONT)
        if self._trend:
            width += 12.0 + 8.0 + _paint.measure_text(
                widget, self._trend_label(), self._LABEL_FONT
            )
        label_width = _paint.measure_text(
            widget, self._label, self._label_font or self._LABEL_FONT
        )
        return int(max(width, label_width)) + 4

    def _refit(self, widget: Optional[tk.Misc] = None):
        """Widen the canvas when the content needs more room than ``size``."""
        target = widget if widget is not None else self._widget
        if target is None:
            return
        needed = self._content_width(target)
        if needed > self._width:
            self._width = needed
            if self._widget is not None:
                self._widget.configure(width=self._width)

    def _value_text(self) -> str:
        """The number formatted for the value font (no prefix/suffix)."""
        try:
            number = float(self._value)
        except (TypeError, ValueError):
            return str(self._value)
        if self._precision is not None:
            return "{:.{}f}".format(number, self._precision)
        if number.is_integer():
            return str(int(number))
        return f"{number:g}"

    def _trend_direction(self) -> bool:
        """True when the trend arrow points up."""
        trend = self._trend
        if isinstance(trend, bool):
            return bool(trend)
        if isinstance(trend, (int, float)):
            return float(trend) >= 0
        return str(trend).lower() in ("up", "rise", "increase")

    def _trend_label(self) -> str:
        """The percentage next to the arrow ("" for the symbolic trends)."""
        trend = self._trend
        if isinstance(trend, bool) or not isinstance(trend, (int, float)):
            return ""
        return f"{abs(float(trend)):g}%"

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        self._refit(master)
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        baseline = self._height - self._BASELINE_MARGIN
        ink = self._value_color or colors["ink"]
        x = self._affix(canvas, 0.0, self._prefix, ink, baseline) if self._prefix else 0.0
        value_id = canvas.create_text(
            x, baseline, anchor="sw", text=self._value_text(), fill=ink,
            font=self._font or self._VALUE_FONT,
        )
        box = canvas.bbox(value_id)
        right = box[2] if box is not None else x
        if self._suffix:
            right = self._affix(canvas, right, self._suffix, ink, baseline)
        canvas.create_text(
            0, 4, anchor="w", text=self._label,
            fill=self._label_color or colors["muted"],
            font=self._label_font or self._LABEL_FONT,
        )
        if self._trend:
            self._draw_trend(canvas, box, right, colors)

    def _affix(
        self,
        canvas: tk.Canvas,
        x: float,
        text: str,
        color: Optional[Color],
        baseline: Any) -> float:
        """Draw a prefix/suffix in the small font; return the new right edge."""
        item = canvas.create_text(
            x, baseline, anchor="sw", text=text,
            fill=color,  # ty: ignore[invalid-argument-type]  tkinter drops None
            font=self._AFFIX_FONT
        )
        box = canvas.bbox(item)
        return float(box[2]) if box is not None else float(x)

    def _draw_trend(self, canvas: tk.Canvas, box: Any, right: Any, colors: _paint.ColorMap):
        """Arrow (and percentage) to the right of the number, on its midline."""
        up = self._trend_direction()
        fill = self._trend_color or (_paint.SUCCESS if up else _paint.DANGER)
        top = float(box[1]) if box is not None else self._height - 40.0
        bottom = float(box[3]) if box is not None else self._height - 10.0
        cx = right + 12.0
        cy = (top + bottom) / 2.0
        _paint.triangle(
            canvas, cx, cy, 8, direction="up" if up else "down", fill=fill, outline=""
        )
        label = self._trend_label()
        if label:
            canvas.create_text(
                cx + 8.0, cy, anchor="w", text=label, fill=fill, font=self._LABEL_FONT
            )

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
        return self

    # --- state ----------------------------------------------------------------
    @property
    def value(self):
        return self._value

    @property
    def label(self) -> str:
        return self._label

    def get(self):
        """The raw value (never the formatted string)."""
        return self._value

    def update(
        self,
        value: Any = None,
        label: Optional[str] = None,
        trend: Any = None,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        visible: Optional[bool] = None):
        """Set the value / texts / trend; ``trend=False`` removes the trend."""
        redraw = False
        if value is not None:
            self._value = value
            redraw = True
        if label is not None:
            self._label = str(label)
            redraw = True
        if trend is not None:
            self._trend = None if trend is False else trend
            redraw = True
        if prefix is not None:
            self._prefix = str(prefix)
            redraw = True
        if suffix is not None:
            self._suffix = str(suffix)
            redraw = True
        if redraw and self._widget is not None:
            self._refit()
            self._draw(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TEmpty(Element):
    """The "no data" placeholder: a small inline icon next to a muted
    caption.

    The web "no data" page (a giant illustration + headline + CTA) maps
    to a desktop idiom of a single line of greyed text — the action is
    already on the surrounding toolbar, so a CTA would be a duplicate.
    The default icon is a 16×16 dog-eared document outline; pass
    ``filename=`` / ``data_base64=`` to override. ``text=""`` drops the
    caption; the icon stays. ``size=(w, h)`` still accepts an explicit
    box (the old web-style 110 px hero size keeps working for code that
    passed it)::

        ts.TEmpty("No records yet")
    """

    __slots__ = (
        "_text",
        "_font",
        "_text_color",
        "_icon_color",
        "_filename",
        "_data_base64",
        "_width",
        "_height",
        "_photo",
    )

    _photo: Optional[tk.PhotoImage]

    # backward-compatible default; the new compact "one-line" sizing kicks
    # in only when the caller leaves size alone
    _LEGACY_DEFAULT = (160, 110)
    _COMPACT_ICON = 16

    def __init__(
        self,
        text: str = "No data",
        size: Optional[Size] = None,
        font: Optional[FontSpec] = None,
        text_color: Optional[Color] = None,
        icon_color: Optional[Color] = None,
        filename: Any = None,
        data_base64: Any = None,
        key: Optional[ElementKey] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        if size is None:
            size = (None, None)
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = "" if text is None else str(text)
        self._font = font
        self._text_color = text_color
        self._icon_color = icon_color
        self._filename = filename
        self._data_base64 = data_base64
        # If the caller did not pin a size, default to a one-line box
        # that hugs the icon + caption. If they did pass one, honour it
        # verbatim (back-compat for the 160×110 web-style hero).
        requested_w, requested_h = self._size
        if requested_w is None and requested_h is None:
            self._width = self._COMPACT_ICON + 6 + 140  # icon + gap + ~text
            self._height = self._COMPACT_ICON
        else:
            self._width = int(requested_w or self._LEGACY_DEFAULT[0])
            self._height = int(requested_h or self._LEGACY_DEFAULT[1])
        self._photo = None

    # --- geometry -------------------------------------------------------------
    def _geometry(self):
        return (self._width, self._height)

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        self._photo = None
        # Detect the legacy "big box" path: any caller-supplied width OR
        # height above the compact icon size keeps the centred-illustration
        # layout. Otherwise we lay out icon | caption in a single row.
        legacy = (
            self._width > self._COMPACT_ICON * 2
            or self._height > self._COMPACT_ICON * 2
        )
        if not self._draw_icon(canvas, colors):
            if legacy:
                self._draw_document_centered(canvas, colors)
            else:
                self._draw_document_inline(canvas, colors)
        if self._text:
            if legacy:
                canvas.create_text(
                    self._width / 2.0,
                    self._height - 6,
                    anchor="s",
                    text=self._text,
                    fill=self._text_color or colors["muted"],
                    font=self._font or ("TkDefaultFont", 9),
                )
            else:
                # icon + 6 px gap + caption, vertically centred
                icon = self._COMPACT_ICON
                canvas.create_text(
                    icon + 6 + 2,
                    self._height / 2.0,
                    anchor="w",
                    text=self._text,
                    fill=self._text_color or colors["muted"],
                    font=self._font or ("TkDefaultFont", 9),
                )

    def _draw_icon(self, canvas: tk.Canvas, colors: _paint.ColorMap) -> bool:
        """Try the image icon; False falls back to the document glyph."""
        if self._filename is None and self._data_base64 is None:
            return False
        try:
            if self._data_base64 is not None:
                self._photo = tk.PhotoImage(data=self._data_base64, master=canvas)
            else:
                self._photo = tk.PhotoImage(file=str(self._filename), master=canvas)
        except Exception:
            self._photo = None
            return False
        legacy = (
            self._width > self._COMPACT_ICON * 2
            or self._height > self._COMPACT_ICON * 2
        )
        if legacy:
            canvas.create_image(
                self._width / 2.0, self._height * 0.40, anchor="center", image=self._photo
            )
        else:
            canvas.create_image(
                self._COMPACT_ICON / 2.0, self._height / 2.0, anchor="center",
                image=self._photo,
            )
        return True

    def _draw_document_centered(self, canvas: tk.Canvas, colors: _paint.ColorMap):
        """The classic dog-eared document outline (legacy big-box layout)."""
        color = self._icon_color or _paint.blend(colors["track"], colors["ink"], 0.72)
        height = min(self._height * 0.42, 54.0)
        width = height * 0.78
        x0 = self._width / 2.0 - width / 2.0
        y0 = self._height * 0.40 - height / 2.0
        x1 = x0 + width
        y1 = y0 + height
        fold = min(width * 0.32, 15.0)
        _paint.rounded_polygon(
            canvas, x0, y0, x1, y1, 3, fill="", outline=color, width=2
        )
        canvas.create_polygon(
            x1 - fold, y0, x1, y0 + fold, x1 - fold, y0 + fold,
            fill=colors["surface"], outline=color, width=2,
        )

    def _draw_document_inline(self, canvas: tk.Canvas, colors: _paint.ColorMap):
        """16x16 dog-eared outline laid out at the left of the caption."""
        color = self._icon_color or _paint.blend(colors["track"], colors["ink"], 0.72)
        icon = self._COMPACT_ICON
        x0 = 0
        y0 = (self._height - icon) / 2.0
        x1 = x0 + icon * 0.78
        y1 = y0 + icon
        fold = max(3.0, icon * 0.22)
        _paint.rounded_polygon(
            canvas, x0, y0, x1, y1, 2, fill="", outline=color, width=1
        )
        canvas.create_polygon(
            x1 - fold, y0, x1, y0 + fold, x1 - fold, y0 + fold,
            fill=colors["surface"], outline=color, width=1,
        )

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
        return self

    # --- state ----------------------------------------------------------------
    @property
    def text(self) -> str:
        return self._text

    def get(self) -> str:
        """The caption ("" when the element shows no text)."""
        return self._text

    def update(self, value: Any = None, visible: Optional[bool] = None):
        """Change the caption (``""`` hides it); ``None`` leaves it alone."""
        if value is not None:
            self._text = str(value)
            if self._widget is not None:
                self._draw(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TResult(Element):
    """A result page: a status circle above a title and a subtitle.

    ``status`` picks the circle color and glyph (``success`` -> check mark,
    ``error`` -> cross, ``warning`` -> "!", anything else -> "i"). Buttons
    belong in the layout below the element, not inside it::

        ts.TResult("Payment done", "Receipt sent by mail", status="success")
    """

    __slots__ = (
        "_title",
        "_subtitle",
        "_status",
        "_icon_color",
        "_title_color",
        "_font",
        "_width",
        "_height",
    )

    _SUBTITLE_FONT = ("TkDefaultFont", 9)
    _TITLE_FONT = ("TkDefaultFont", 15, "bold")
    _TITLE_GAP = 18  # px between the circle bottom and the title top
    _SUBTITLE_GAP = 8  # px between the title bottom and the subtitle top

    def __init__(
        self,
        title: str,
        subtitle: Optional[str] = None,
        status: str = "info",
        size: Size = (300, 200),
        icon_color: Optional[Color] = None,
        title_color: Optional[Color] = None,
        font: Optional[FontSpec] = None,
        key: Optional[ElementKey] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._title = "" if title is None else str(title)
        self._subtitle = "" if subtitle is None else str(subtitle)
        self._status = status or "info"
        self._icon_color = icon_color
        self._title_color = title_color
        self._font = font
        self._width = int(self._size[0] or 300)
        self._height = int(self._size[1] or 200)

    # --- geometry -------------------------------------------------------------
    def _geometry(self):
        return (self._width, self._height)

    def _radius(self) -> float:
        return min(self._width * 0.12, 30.0)

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        radius = self._radius()
        cx = self._width / 2.0
        cy = radius + 14
        fill = self._icon_color or _paint.status_color(self._status, colors)
        canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius, fill=fill, outline=""
        )
        self._draw_glyph(canvas, fill, cx, cy, radius)
        title_y = cy + radius + self._TITLE_GAP
        title_id = canvas.create_text(
            cx, title_y, anchor="n", text=self._title,
            fill=self._title_color or colors["ink"],
            font=self._font or self._TITLE_FONT,
        )
        if self._subtitle:
            box = canvas.bbox(title_id)
            below = (float(box[3]) if box is not None else title_y) + self._SUBTITLE_GAP
            canvas.create_text(
                cx, below, anchor="n", text=self._subtitle, fill=colors["muted"],
                font=self._SUBTITLE_FONT, width=max(20, self._width - 40),
            )

    def _draw_glyph(self, canvas: tk.Canvas, fill: Any, cx: float, cy: float, radius: float):
        """The status mark inside the circle, in the contrasting ink."""
        ink = theme_mod.contrast_on(fill)
        glyph = _status_glyph(self._status)
        if glyph == _GLYPH_CHECK:
            _paint.check_mark(canvas, cx, cy, radius, fill=ink, width=3)
        elif glyph == _GLYPH_CROSS:
            _paint.cross(canvas, cx, cy, radius * 0.8, fill=ink, width=3)
        else:
            canvas.create_text(
                cx, cy, text="!" if glyph == _GLYPH_BANG else "i", fill=ink,
                font=("TkDefaultFont", max(8, int(radius * 0.95)), "bold"),
            )

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
        return self

    # --- state ----------------------------------------------------------------
    @property
    def title(self) -> str:
        return self._title

    def get(self) -> str:
        """The title text."""
        return self._title

    def update(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        status: Optional[str] = None,
        visible: Optional[bool] = None):
        """Change the texts / status; ``None`` leaves an argument unchanged."""
        redraw = False
        if title is not None:
            self._title = str(title)
            redraw = True
        if subtitle is not None:
            self._subtitle = str(subtitle)
            redraw = True
        if status is not None:
            self._status = status
            redraw = True
        if redraw and self._widget is not None:
            self._draw(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TSkeleton(Element):
    """An animated loading placeholder (skeleton screen).

    Bars (optionally after a round avatar placeholder) pulse between two
    shades while ``animated`` is set; the pulse runs on the window event
    loop through :meth:`Window.every`::

        skeleton = ts.TSkeleton(rows=3, avatar=True, key="-SKEL-")
        skeleton.stop_animation()   # e.g. once the data arrived
    """

    __slots__ = (
        "_rows",
        "_animated",
        "_avatar",
        "_bar_height",
        "_gap",
        "_width",
        "_height",
        "_timer",
        "_phase",
    )

    _PULSE_MS = 550  # half period of the pulse animation

    _timer: Optional[Any]  # window timer handle (None while stopped)

    def __init__(
        self,
        rows: int = 3,
        animated: bool = True,
        avatar: bool = False,
        size: Optional[Size] = None,
        bar_height: int = 14,
        gap: int = 10,
        key: Optional[ElementKey] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._rows = max(1, int(rows))
        self._animated = bool(animated)
        self._avatar = bool(avatar)
        self._bar_height = max(1, int(bar_height))
        self._gap = max(0, int(gap))
        self._timer = None
        self._phase = False
        width, height = self._geometry()
        self._width = int(width)
        self._height = int(height)

    # --- geometry -------------------------------------------------------------
    def _geometry(self):
        """(width, height): 240 wide, row count tall (at least 40 with avatar)."""
        height = self._size[1]
        if height is None:
            height = self._rows * self._bar_height + max(self._rows - 1, 0) * self._gap
            if self._avatar:
                height = max(height, 40)
        return (int(self._size[0] or 240), int(height))

    def _bar_box(self, index: int, height: int):
        """(left, top, right) of one bar: the last of many is 60% wide."""
        diameter = min(40, height) if self._avatar else 0
        left = float(diameter + 12) if self._avatar else 0.0
        top = float(index * (self._bar_height + self._gap))
        span = self._width - left
        short = index == self._rows - 1 and self._rows > 1
        right = left + span * 0.6 if short else float(self._width)
        return (left, top, right)

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        bar = _paint.blend(colors["ink"], colors["surface"], 0.80 if self._phase else 0.90)
        if self._avatar:
            diameter = min(40, self._height)
            top = (self._height - diameter) / 2.0
            canvas.create_oval(
                0, top, diameter, top + diameter, fill=bar, outline=""
            )
        for index in range(self._rows):
            left, top, right = self._bar_box(index, self._height)
            _paint.capsule(
                canvas, left, top, right, top + self._bar_height, fill=bar, outline=""
            )

    def _refresh(self):
        """Re-measure the placeholder for the current row count and redraw."""
        if self._widget is None:
            return
        width, height = self._geometry()
        self._width = int(width)
        self._height = int(height)
        self._widget.configure(width=self._width, height=self._height)
        self._draw(self._widget)

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
        return self

    # --- animation --------------------------------------------------------------
    def _post_create(self):
        super()._post_create()
        if self._animated:
            self.start_animation()

    def _pulse(self):
        """Timer callback: swap the bar shade and repaint."""
        if self._widget is None:
            return
        self._phase = not self._phase
        self._draw(self._widget)

    def start_animation(self):
        """Start the pulse (a no-op when it is already running)."""
        if self._window is None or self._timer is not None:
            return self
        self._timer = self._window.every(self._PULSE_MS, self._pulse)
        return self

    def stop_animation(self):
        """Stop the pulse and settle on the calm shade."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._phase = False
        return self

    # --- state ----------------------------------------------------------------
    @property
    def rows(self) -> int:
        return self._rows

    @property
    def animated(self) -> bool:
        return self._animated

    def get(self) -> int:
        """The placeholder row count."""
        return self._rows

    def update(
        self,
        rows: Any = None,
        animated: Optional[bool] = None,
        visible: Optional[bool] = None):
        """Change the row count / animation; ``None`` leaves it unchanged."""
        redraw = False
        if rows is not None:
            self._rows = max(1, int(rows))
            redraw = True
        if animated is not None and bool(animated) != self._animated:
            self._animated = bool(animated)
            redraw = True
            if self._animated:
                self.start_animation()
            else:
                self.stop_animation()
        if redraw:
            self._refresh()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TAlert(Element):
    """An inline message bar: icon, optional title and text.

    Nothing floats or overlays: the bar is a plain ``tk.Frame`` that sits
    in the layout. ``effect`` chooses a soft (``"light"``) or solid
    (``"dark"``) wash of the status color; ``closable`` adds an "x" that
    hides the bar and posts ``(key, "close")``::

        ts.TAlert("Backup finished", type="success", title="Done")
    """

    __slots__ = (
        "_text",
        "_title",
        "_status",
        "_closable",
        "_show_icon",
        "_effect",
        "_font",
        "_text_color",
        "_enable_events",
        "_body",
        "_title_label",
        "_text_label",
        "_icon_canvas",
        "_close_canvas",
    )

    _title_label: tk.Label
    _text_label: tk.Label
    _icon_canvas: Optional[tk.Canvas]
    _close_canvas: Optional[tk.Canvas]

    _ICON_SIZE = 18
    _CLOSE_SIZE = 16
    _TITLE_FONT = ("TkDefaultFont", 10, "bold")

    def __init__(
        self,
        text: str,
        status: str = "info",
        title: Optional[str] = None,
        closable: bool = True,
        show_icon: bool = True,
        effect: str = "light",
        size: Size = (None, None),
        font: Optional[FontSpec] = None,
        text_color: Optional[Color] = None,
        key: Optional[ElementKey] = None,
        enable_events: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = "" if text is None else str(text)
        self._title = "" if title is None else str(title)
        self._status = status or "info"
        self._closable = bool(closable)
        self._show_icon = bool(show_icon)
        self._effect = str(effect or "light").lower()
        self._font = font
        self._text_color = text_color
        self._enable_events = bool(enable_events)
        self._icon_canvas = None
        self._close_canvas = None

    # --- colors ---------------------------------------------------------------
    def _style(self, colors: Dict[str, str]) -> Dict[str, str]:
        """(fill, border, text, accent) for the active type and effect."""
        accent = _paint.status_color(self._status, colors)
        if self._effect == "dark":
            return {
                "fill": accent,
                "border": _paint.blend(accent, "#000000", 0.15),
                "text": theme_mod.contrast_on(accent),
                "accent": accent,
            }
        return {
            "fill": _paint.tint(accent, colors, 0.90),
            "border": _paint.tint(accent, colors, 0.62),
            "text": colors["ink"],
            "accent": accent,
        }

    def _wraplength(self):
        """The description wrap width when ``size`` asked for a fixed width."""
        if self._size[0] is None:
            return None
        return max(40, int(self._size[0]) - 70)

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        colors = _paint.palette(master)
        style = self._style(colors)
        frame = tk.Frame(
            master,
            highlightthickness=1,
            highlightbackground=style["border"],
            background=style["fill"],
            bd=0,
        )
        frame.columnconfigure(1, weight=1)
        if self._show_icon:
            self._icon_canvas = _paint.themed_canvas(
                frame, self._ICON_SIZE, self._ICON_SIZE, style["fill"]
            )
            self._icon_canvas.grid(row=0, column=0, sticky="n", padx=(10, 8), pady=6)
        self._body = tk.Frame(frame, background=style["fill"], bd=0, highlightthickness=0)
        self._body.grid(row=0, column=1, sticky="we", pady=6)
        self._title_label = self._make_label(self._body, self._TITLE_FONT, style)
        self._text_label = self._make_label(
            self._body, self._font or ("TkDefaultFont", 9), style
        )
        self._text_label.configure(text=self._text)
        self._text_label.configure(wraplength=self._wraplength() or 0)
        self._text_label.pack(anchor="w", fill="x")
        if self._closable:
            self._close_canvas = _paint.themed_canvas(
                frame, self._CLOSE_SIZE, self._CLOSE_SIZE, style["fill"]
            )
            self._close_canvas.grid(row=0, column=2, sticky="n", padx=(8, 10), pady=6)
        self._sync_title()
        self._draw_icon()
        self._draw_close()
        return frame

    def _make_label(
        self,
        master: tk.Misc,
        font: Optional[FontSpec],
        style: _paint.ColorMap) -> tk.Label:
        return tk.Label(
            master,
            text="",
            justify="left",
            anchor="w",
            background=style["fill"],
            foreground=self._text_color or style["text"],
            font=font,  # ty: ignore[invalid-argument-type]  tk accepts tuple specs
            bd=0,
            highlightthickness=0,
        )

    def _sync_title(self):
        """Pack the title label only while there is a title."""
        if self._title:
            self._title_label.configure(text=self._title)
            if not self._title_label.winfo_manager():
                self._title_label.pack(
                    anchor="w", fill="x", before=self._text_label
                )
        elif self._title_label.winfo_manager():
            self._title_label.pack_forget()

    def _draw_icon(self):
        """The status dot with its glyph inside."""
        canvas = self._icon_canvas
        if canvas is None:
            return
        style = self._style(_paint.palette(canvas))
        canvas.configure(background=style["fill"])
        canvas.delete("all")
        accent = style["accent"]
        ink = theme_mod.contrast_on(accent)
        size = self._ICON_SIZE
        center = size / 2.0
        canvas.create_oval(0, 0, size, size, fill=accent, outline="")
        glyph = _status_glyph(self._status)
        if glyph == _GLYPH_CHECK:
            _paint.check_mark(canvas, center, center, 9, fill=ink, width=2)
        elif glyph == _GLYPH_CROSS:
            _paint.cross(canvas, center, center, 7, fill=ink, width=2)
        else:
            canvas.create_text(
                center, center, text="!" if glyph == _GLYPH_BANG else "i",
                fill=ink, font=("TkDefaultFont", 8, "bold"),
            )

    def _draw_close(self):
        """The "x" that hides the bar."""
        canvas = self._close_canvas
        if canvas is None:
            return
        style = self._style(_paint.palette(canvas))
        canvas.configure(background=style["fill"])
        canvas.delete("all")
        center = self._CLOSE_SIZE / 2.0
        _paint.cross(
            canvas, center, center, 7, fill=self._text_color or style["text"], width=1.5
        )

    def apply_theme(self):
        """Re-derive the frame, both labels and both canvases."""
        if self._widget is None:
            return self
        style = self._style(_paint.palette(self._widget))
        ink = self._text_color or style["text"]
        self._widget.configure(
            background=style["fill"], highlightbackground=style["border"]
        )
        for widget in (self._body, self._title_label, self._text_label):
            widget.configure(background=style["fill"])
        self._title_label.configure(foreground=ink)
        self._text_label.configure(foreground=ink)
        self._text_label.configure(wraplength=self._wraplength() or 0)
        self._draw_icon()
        self._draw_close()
        return self

    # --- interaction ------------------------------------------------------------
    def _bind_events(self):
        targets = [self._widget, self._body, self._title_label, self._text_label]
        if self._icon_canvas is not None:
            targets.append(self._icon_canvas)
        for target in targets:
            target.bind("<Button-1>", self._on_body_click)
        if self._close_canvas is not None:
            self._close_canvas.bind("<Button-1>", self._on_close_click)

    def _on_body_click(self, _event: tk.Event):
        if self._enable_events:
            self._post_event()

    @property
    def closed(self):
        """Whether the user has dismissed this alert. Read-only;
        flip with :meth:`close` / :meth:`reopen`."""
        return not self._visible

    def close(self):
        """Programmatic equivalent of clicking the "×" — hides the bar
        (posts ``(key, "close")`` if the element has a key)."""
        if not self._visible:
            return self
        self._perform_close()
        return self

    def reopen(self):
        """Re-show a closed alert (counterpart of :meth:`close`)."""
        if self._visible:
            return self
        self.unhide()
        return self

    def _perform_close(self):
        """Shared body for the click and the :meth:`close` method."""
        self.hide()
        if self._key is not None:
            self._post_event((self._key, "close"))

    def _on_close_click(self, _event: tk.Event):
        self._perform_close()

    # --- state ----------------------------------------------------------------
    @property
    def text(self) -> str:
        return self._text

    @property
    def title(self) -> str:
        return self._title

    def get(self) -> str:
        """The message text (not the title)."""
        return self._text

    def update(
        self,
        text: Optional[str] = None,
        title: Optional[str] = None,
        status: Any = None,
        visible: Optional[bool] = None):
        """Change the message, title or status; ``""`` clears the title."""
        redraw = False
        if text is not None:
            self._text = str(text)
            self._text_label.configure(text=self._text)
            redraw = True
        if title is not None:
            self._title = str(title)
            redraw = True
        if status is not None:
            self._status = status
            redraw = True
        if redraw and self._widget is not None:
            self._sync_title()
            self.apply_theme()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self


class TWatermark(Element):
    """Tiled text over a blank surface.

    Tk child widgets are opaque -- a watermark cannot shine through the
    widget sitting on top of it. The text is drawn on this element's own
    canvas, so place the element where the watermark should appear (use
    ``expand_x`` / ``expand_y`` to fill a container). Diagonal tiling is
    rendered with Pillow and a system font file; when either is missing the
    text falls back to a horizontal grid at the same spacing::

        ts.TWatermark("DRAFT", gap=(160, 100), angle=-30)
    """

    __slots__ = (
        "_text",
        "_font",
        "_color",
        "_gap",
        "_angle",
        "_width",
        "_height",
        "_photo",
    )

    _photo: Optional[tk.PhotoImage]

    _DEFAULT_FONT = ("TkDefaultFont", 16)

    def __init__(
        self,
        text: str,
        size: Size = (400, 260),
        font: Optional[FontSpec] = None,
        color: Optional[Color] = None,
        gap: Tuple[int, int] = (140, 90),
        angle: int = -30,
        key: Optional[ElementKey] = None,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
            key=key,
            size=_as_pair(size),
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = "" if text is None else str(text)
        self._font = font
        self._color = color
        self._gap = (max(1, int(gap[0])), max(1, int(gap[1])))
        self._angle = float(angle or 0.0)
        self._width = int(self._size[0] or 400)
        self._height = int(self._size[1] or 260)
        self._photo = None

    # --- geometry -------------------------------------------------------------
    def _geometry(self):
        return (self._width, self._height)

    def _font_spec(self):
        return self._font if self._font is not None else self._DEFAULT_FONT

    def _grid_points(self, pitch_x: float, pitch_y: float):
        """The tile anchor points: one per cell of the (pitch_x, pitch_y) grid."""
        points = []
        for y in range(int(pitch_y) // 2, self._height, max(1, int(pitch_y))):
            for x in range(int(pitch_x) // 2, self._width, max(1, int(pitch_x))):
                points.append((x, y))
        return points

    # --- rendering ------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        colors = _paint.palette(master)
        canvas = _paint.themed_canvas(master, self._width, self._height, colors["surface"])
        self._draw(canvas)
        return canvas

    def _draw(self, canvas: tk.Canvas):
        colors = _paint.palette(canvas)
        canvas.configure(background=colors["surface"])
        canvas.delete("all")
        self._photo = None
        color = self._color or _paint.blend(colors["ink"], colors["surface"], 0.86)
        if self._angle != 0.0 and self._draw_rotated(canvas, color, colors):
            return
        self._draw_grid(canvas, color)

    def _draw_grid(self, canvas: tk.Canvas, color: Optional[Color]):
        """Plain horizontal tiling (also the fallback for the rotated look)."""
        gap_x, gap_y = self._gap
        for x, y in self._grid_points(gap_x, gap_y):
            canvas.create_text(
                x, y, text=self._text,
                fill=color,  # ty: ignore[invalid-argument-type]  tkinter drops None
                font=self._font_spec(),
                anchor="center",
            )

    def _draw_rotated(
        self,
        canvas: tk.Canvas,
        color: Optional[Color],
        colors: _paint.ColorMap) -> bool:
        """Rotated tiling through Pillow; False when it is not available."""
        modules = _paint.pil_modules()
        if not modules:
            return False
        image_mod, draw_mod = modules
        font_file = _paint.system_font_file(_font_family(self._font_spec()))
        if font_file is None:
            return False
        rgb = theme_mod._parse_hex(color) or (128, 128, 128)
        try:
            patch = self._text_patch(image_mod, draw_mod, font_file, rgb)
            patch = patch.rotate(
                self._angle, expand=True, resample=_resample(image_mod, "BICUBIC")
            )
            image = image_mod.new("RGB", (self._width, self._height), colors["surface"])
            gap_x, gap_y = self._gap
            for x, y in self._grid_points(gap_x, gap_y):
                image.paste(
                    patch,
                    (int(x - patch.width / 2.0), int(y - patch.height / 2.0)),
                    patch,
                )
            photo = _photo_from_image(image, canvas)
        except Exception:
            return False
        self._photo = photo
        canvas.create_image(0, 0, anchor="nw", image=photo)
        return True

    def _text_patch(self, image_mod: Any, draw_mod: Any, font_file: Any, rgb: Any):
        """One RGBA text tile, rendered with a Pillow font file."""
        text = self._text
        font = _pil_font(font_file, _font_size(self._font_spec()))
        if font is None:
            raise ValueError("unusable watermark font file")
        box = font.getbbox(text)
        width, height = int(box[2] - box[0]), int(box[3] - box[1])
        if width < 1 or height < 1:
            raise ValueError("empty watermark patch")
        pad = 4
        patch = image_mod.new(
            "RGBA", (width + pad * 2, height + pad * 2), (0, 0, 0, 0)
        )
        draw_mod.Draw(patch).text(
            (pad, pad), text, font=font, fill=(rgb[0], rgb[1], rgb[2], 255)
        )
        return patch

    def apply_theme(self):
        if self._widget is not None:
            self._draw(self._widget)
        return self

    # --- state ----------------------------------------------------------------
    @property
    def text(self) -> str:
        return self._text

    def get(self) -> str:
        """The watermark text."""
        return self._text

    def update(self, value: Any = None, visible: Optional[bool] = None):
        """Change the text; ``None`` leaves it unchanged."""
        if value is not None:
            self._text = str(value)
            if self._widget is not None:
                self._draw(self._widget)
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self
