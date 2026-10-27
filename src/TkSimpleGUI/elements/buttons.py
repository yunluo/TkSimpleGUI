#!/usr/bin/env python3
"""TButton elements for TkSimpleGUI."""

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
from typing import Any, Iterable, Optional, Sequence, Tuple, cast
from .._typing_compat import Literal

from .base import Color, Element, ElementKey, FontSpec, Justification, MenuDefinition, PadSpec, Size
from .. import constants as C
from .. import _theming as theme_mod



class TButton(Element):
    """A clickable button (ttk based for a native look).

    Clicking posts the button's key into the window event queue. Browse
    variants open native dialogs and write their result into a target
    element's key.
    """

    __slots__ = (
        "_button_text",
        "_button_type",
        "_button_color",
        "_target_key",
        "_file_types",
        "_disabled",
        "_font",
        "_image_filename",
        "_image_data",
        "_compound",
        "_photo",
        "_toggle",
        "_group_id",
        "_down",
    )

    def __init__(
        self,
        button_text: str = "",
        key: Optional[ElementKey] = None,
        button_type: Any = C.ButtonType.READ,
        button_color: Optional[Color] = None,
        size: Size = (None, None),
        target_key: Optional[ElementKey] = None,
        file_types: Optional[Sequence[Tuple[str, str]]] = None,
        image_filename: Optional[str] = None,
        image_data: Optional[bytes] = None,
        compound: Optional[str] = "left",
        font: Optional[FontSpec] = None,
        disabled: bool = False,
        toggle: bool = False,
        group_id: Any = None,
        down: bool = False,
        tooltip: Optional[str] = None,
        visible: bool = True,
        pad: Optional[PadSpec] = None,
        expand_x: bool = False,
        expand_y: bool = False,
        justification: Optional[Justification] = None,
        right_click_menu: Optional[MenuDefinition] = None,
        metadata: Any = None,
    ):
        super().__init__(
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
        self._button_text = button_text
        self._button_type = button_type
        self._button_color = button_color
        self._target_key = target_key
        self._file_types = tuple(file_types) if file_types is not None else C.FILE_TYPES_ALL_FILES
        self._image_filename = image_filename
        self._image_data = image_data
        self._compound = compound
        self._disabled = bool(disabled)
        self._font = font
        self._photo = None
        self._toggle = bool(toggle)
        self._group_id = group_id
        self._down = bool(down)

    @classmethod
    def browse_file(
        cls,
        button_text: str = "Browse",
        target_key: Optional[ElementKey] = None,
        file_types: Optional[Sequence[Tuple[str, str]]] = None,
        **kwargs: Any):
        """Create a button that opens a single-file picker."""
        return cls(
            button_text,
            button_type=C.ButtonType.BROWSE_FILE,
            target_key=target_key,
            file_types=file_types,
            **kwargs
        )

    @classmethod
    def browse_files(
        cls,
        button_text: str = "Browse",
        target_key: Optional[ElementKey] = None,
        file_types: Optional[Sequence[Tuple[str, str]]] = None,
        **kwargs: Any):
        """Create a button that opens a multi-file picker."""
        return cls(
            button_text,
            button_type=C.ButtonType.BROWSE_FILES,
            target_key=target_key,
            file_types=file_types,
            **kwargs
        )

    @classmethod
    def browse_folder(
        cls,
        button_text: str = "Browse",
        target_key: Optional[ElementKey] = None,
        **kwargs: Any):
        """Create a button that opens a folder picker."""
        return cls(
            button_text,
            button_type=C.ButtonType.BROWSE_FOLDER,
            target_key=target_key,
            **kwargs
        )

    @classmethod
    def save_as(
        cls,
        button_text: str = "Save As...",
        target_key: Optional[ElementKey] = None,
        file_types: Optional[Sequence[Tuple[str, str]]] = None,
        **kwargs: Any):
        """Create a button that opens a save-as dialog."""
        return cls(
            button_text,
            button_type=C.ButtonType.SAVEAS_FILE,
            target_key=target_key,
            file_types=file_types,
            **kwargs
        )

    @classmethod
    def color_chooser(
        cls,
        button_text: str = "Choose Color",
        target_key: Optional[ElementKey] = None,
        **kwargs: Any):
        """Create a button that opens the native color chooser."""
        return cls(
            button_text,
            button_type=C.ButtonType.COLOR_CHOOSER,
            target_key=target_key,
            **kwargs
        )

    @classmethod
    def from_action(cls, action: Any, **kwargs: Any):
        """Create a button wired to an :class:`~TkSimpleGUI.actions.Action`."""
        return cls(action.text, key=action.key, **kwargs)

    # --- identity ------------------------------------------------------------
    @property
    def button_text(self):
        return self._button_text

    @property
    def button_type(self):
        return self._button_type

    @property
    def disabled(self):
        return self._disabled

    # --- widget ----------------------------------------------------------------
    def _create_widget(self, master: tk.Misc):
        if self._toggle:
            return self._create_toggle_button(master)
        kwargs = {}
        width = self._size[0] if self._size else None
        if width is not None:
            kwargs["width"] = int(width)
        colors = self._button_color
        if colors is None:
            colors = theme_mod.theme_manager.button_colors
        style_options = {}
        if colors is not None:
            fg, bg = colors
            if fg is not None:
                style_options["foreground"] = fg
            if bg is not None:
                style_options["background"] = bg
        if self._font is not None:
            style_options["font"] = self._font
        kwargs["style"] = theme_mod.theme_manager.ttk_widget_style(
            master, "TButton", **style_options
        )
        button = ttk.Button(master, text=self._button_text, **kwargs)
        if self._image_filename is not None or self._image_data is not None:
            try:
                if self._image_data is not None:
                    self._photo = tk.PhotoImage(data=self._image_data, master=master)
                else:
                    self._photo = tk.PhotoImage(
                        file=str(self._image_filename), master=master
                    )
                button.configure(image=self._photo)
                if self._compound is not None:
                    compound = cast(
                        Literal[
                            "", "text", "image", "top", "left",
                            "right", "center", "bottom", "none",
                        ],
                        self._compound,
                    )
                    button.configure(compound=compound)
            except tk.TclError:
                self._photo = None
        if self._disabled:
            button.configure(state="disabled")
        return button

    def _create_toggle_button(self, master: tk.Misc):
        """Toggle buttons use tk.Button: ttk has no pressed-in relief."""
        kwargs = {}
        width = self._size[0] if self._size else None
        if width is not None:
            kwargs["width"] = int(width)
        if self._font is not None:
            kwargs["font"] = self._font
        kwargs.update(theme_mod.theme_manager.button_kwargs(self._button_color))
        button = tk.Button(
            master,
            text=self._button_text,
            bd=1,
            relief="sunken" if self._down else "raised",
            **kwargs
        )
        if self._disabled:
            button.configure(state="disabled")
        return button

    def _bind_events(self):
        if self._button_type is C.ButtonType.REALTIME and not self._toggle:
            self._widget.bind("<ButtonPress-1>", self._on_press)
            self._widget.bind("<ButtonRelease-1>", self._on_release)
        else:
            self._widget.configure(command=self._on_click)

    def apply_theme(self):
        """Repaint theme-derived button colors (explicit colors are kept)."""
        if self._toggle:
            # tk toggle button: re-apply its color kwargs directly
            kwargs = theme_mod.theme_manager.button_kwargs(self._button_color)
            if not kwargs:
                kwargs = theme_mod.native_widget_colors(
                    tk.Button, self._widget,
                    ("background", "foreground",
                     "activebackground", "activeforeground"),
                )
            self._widget.configure(**kwargs)
            return self
        colors = self._button_color
        if colors is None:
            colors = theme_mod.theme_manager.button_colors
        style_options = {}
        if colors is not None:
            fg, bg = colors
            if fg is not None:
                style_options["foreground"] = fg
            if bg is not None:
                style_options["background"] = bg
        if self._font is not None:
            style_options["font"] = self._font
        self._widget.configure(style=theme_mod.theme_manager.ttk_widget_style(
            self._widget, "TButton", **style_options
        ))
        return self

    # --- behaviour -------------------------------------------------------------
    def _on_click(self):
        if self._toggle:
            self._handle_toggle()
            return
        browse_result = self._run_browse()
        if browse_result is not None and self._target_key is not None:
            target = self._window.find_element(self._target_key)
            if target is not None:
                target.update(value=browse_result)
        self._post_event()

    def _handle_toggle(self):
        """Flip the pressed state (exclusive within ``group_id``)."""
        new_state = not self._down
        if new_state and self._group_id is not None and self._window is not None:
            self._window._press_toggle(self._group_id, self)
        self._set_down(new_state)
        self._post_event()

    def _set_down(self, down: bool):
        self._down = bool(down)
        if self._widget is not None:
            self._widget.configure(relief="sunken" if self._down else "raised")

    @property
    def down(self):
        """Pressed state of a toggle button (False for normal buttons)."""
        return self._down

    def _on_press(self, _event: tk.Event):
        self._post_event()

    def _on_release(self, _event: tk.Event):
        self._post_event()

    def _run_browse(self):
        browse_type = self._button_type
        if browse_type is C.ButtonType.BROWSE_FILE:
            return filedialog.askopenfilename(filetypes=self._file_types) or None
        if browse_type is C.ButtonType.BROWSE_FILES:
            return (
                C.BROWSE_FILES_DELIMITER.join(
                    filedialog.askopenfilenames(filetypes=self._file_types)
                )
                or None
            )
        if browse_type is C.ButtonType.BROWSE_FOLDER:
            return filedialog.askdirectory() or None
        if browse_type is C.ButtonType.SAVEAS_FILE:
            return filedialog.asksaveasfilename(filetypes=self._file_types) or None
        if browse_type is C.ButtonType.COLOR_CHOOSER:
            chosen = colorchooser.askcolor()
            return chosen[1] if chosen else None
        return None

    def get(self):
        """Toggle buttons return their pressed state; others their text."""
        return self._down if self._toggle else self._button_text

    def update(
        self,
        text: Optional[str] = None,
        disabled: Optional[bool] = None,
        visible: Optional[bool] = None):
        if text is not None:
            self._button_text = text
            self._widget.configure(text=text)
        if disabled is not None:
            self._disabled = bool(disabled)
            self._widget.configure(state="disabled" if disabled else "normal")
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    def click(self):
        """Programmatically click the button (posts its event)."""
        self._on_click()
        return self


class TSubmit(TButton):
    """TButton whose click also closes the window (returns its key)."""

    __slots__ = ()

    def _on_click(self):
        super()._on_click()
        if self._window is not None:
            self._window._post_event(C.WIN_CLOSED)


class TCloseButton(TButton):
    """TButton that closes its window without posting an event."""

    __slots__ = ()

    def _on_click(self):
        if self._window is not None:
            self._window._post_event(C.WIN_CLOSED)


class TMenubutton(Element):
    """A standalone ttk dropdown button (TToolbar uses these internally).

    Selecting a menu item posts the item's label into the window queue.
    """

    __slots__ = ("_text", "_items", "_menu", "_direction")

    _menu: tk.Menu

    def __init__(
        self,
        text: str,
        items: Iterable[Any],
        key: Optional[ElementKey] = None,
        direction: Optional[str] = "below",
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
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        self._text = str(text)
        self._items = list(items)
        self._menu = None  # ty: ignore[invalid-assignment]
        self._direction = direction

    def _create_widget(self, master: tk.Misc):
        self._menu = tk.Menu(master, tearoff=False)
        for item in self._items:
            if item == C.MENU_SEPARATOR_LINE:
                self._menu.add_separator()
                continue
            label = str(item).replace(C.MENU_SHORTCUT_CHARACTER, "")
            self._menu.add_command(
                label=label, command=lambda t=label: self._post_event(t)
            )
        # narrow the direction to the literal set ttk.Menubutton accepts
        direction = cast(
            Literal["above", "below", "left", "right", "flush"],
            self._direction if self._direction in ("above", "below",
                    "left", "right", "flush") else "below",
        )
        return ttk.Menubutton(
            master, text=self._text, direction=direction, menu=self._menu
        )

    @property
    def items(self):
        return list(self._items)

    def update(
        self,
        text: Optional[str] = None,
        items: Optional[Iterable[Any]] = None,
        visible: Optional[bool] = None):
        if text is not None:
            self._text = str(text)
            self._widget.configure(text=self._text)
        if items is not None:
            self._items = list(items)
            self._menu.delete(0, "end")
            for item in self._items:
                if item == C.MENU_SEPARATOR_LINE:
                    self._menu.add_separator()
                    continue
                label = str(item).replace(C.MENU_SHORTCUT_CHARACTER, "")
                self._menu.add_command(
                    label=label, command=lambda t=label: self._post_event(t)
                )
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self
