#!/usr/bin/env python3
"""Button elements for PySimpleGUI4."""

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser

from .base import Element
from .. import constants as C
from .. import _theming as theme_mod

try:
    from typing import Any, Callable, Optional, Tuple
except ImportError:
    Any = Callable = Optional = Tuple = None


class Button(Element):
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
    )

    def __init__(
        self,
        button_text="",
        key=None,
        button_type=C.ButtonType.READ,
        button_color=None,
        size=(None, None),
        target_key=None,
        file_types=None,
        font=None,
        disabled=False,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        justification=None,
        right_click_menu=None,
        metadata=None,
    ):
        super(Button, self).__init__(
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
        self._disabled = bool(disabled)
        self._font = font

    @classmethod
    def browse_file(cls, button_text="Browse", target_key=None, file_types=None, **kwargs):
        """Create a button that opens a single-file picker."""
        return cls(
            button_text,
            button_type=C.ButtonType.BROWSE_FILE,
            target_key=target_key,
            file_types=file_types,
            **kwargs
        )

    @classmethod
    def browse_files(cls, button_text="Browse", target_key=None, file_types=None, **kwargs):
        """Create a button that opens a multi-file picker."""
        return cls(
            button_text,
            button_type=C.ButtonType.BROWSE_FILES,
            target_key=target_key,
            file_types=file_types,
            **kwargs
        )

    @classmethod
    def browse_folder(cls, button_text="Browse", target_key=None, **kwargs):
        """Create a button that opens a folder picker."""
        return cls(
            button_text,
            button_type=C.ButtonType.BROWSE_FOLDER,
            target_key=target_key,
            **kwargs
        )

    @classmethod
    def save_as(cls, button_text="Save As...", target_key=None, file_types=None, **kwargs):
        """Create a button that opens a save-as dialog."""
        return cls(
            button_text,
            button_type=C.ButtonType.SAVEAS_FILE,
            target_key=target_key,
            file_types=file_types,
            **kwargs
        )

    @classmethod
    def color_chooser(cls, button_text="Choose Color", target_key=None, **kwargs):
        """Create a button that opens the native color chooser."""
        return cls(
            button_text,
            button_type=C.ButtonType.COLOR_CHOOSER,
            target_key=target_key,
            **kwargs
        )

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
    def _create_widget(self, master):
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
        if self._disabled:
            button.configure(state="disabled")
        return button

    def _bind_events(self):
        if self._button_type is C.ButtonType.REALTIME:
            self._widget.bind("<ButtonPress-1>", self._on_press)
            self._widget.bind("<ButtonRelease-1>", self._on_release)
        else:
            self._widget.configure(command=self._on_click)

    # --- behaviour -------------------------------------------------------------
    def _on_click(self):
        browse_result = self._run_browse()
        if browse_result is not None and self._target_key is not None:
            target = self._window.find_element(self._target_key)
            if target is not None:
                target.update(value=browse_result)
        self._post_event()

    def _on_press(self, _event):
        self._post_event()

    def _on_release(self, _event):
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
        return self._button_text

    def update(self, text=None, disabled=None, visible=None):
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


def ttk_button_class():
    """Legacy hook: the ttk button class used for a native look.

    Buttons are always ttk based since PySimpleGUI4 styles per-widget colors
    through ttk styles; the function is kept for backward compatibility.
    """
    return ttk.Button


class Submit(Button):
    """Button whose click also closes the window (returns its key)."""

    __slots__ = ()

    def _on_click(self):
        super(Submit, self)._on_click()
        if self._window is not None:
            self._window._post_event(C.WIN_CLOSED)


class CloseButton(Button):
    """Button that closes its window without posting an event."""

    __slots__ = ()

    def _on_click(self):
        if self._window is not None:
            self._window._post_event(C.WIN_CLOSED)
