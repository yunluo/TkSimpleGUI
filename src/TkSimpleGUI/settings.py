#!/usr/bin/env python3
"""TkSimpleGUI global settings.

All mutable global options live in one :class:`Settings` instance instead of
loose module level variables. The package exposes the ``settings`` singleton.
"""

from typing import Any
from . import constants as C



_KNOWN_OPTIONS = (
    "font",
    "element_size",
    "button_element_size",
    "margins",
    "element_padding",
    "border_width",
    "autoclose_time",
    "tooltip_time",
    "tooltip_offset",
    "keep_on_top",
    "scaling",
    "alpha_channel",
    "suppress_error_popups",
    "suppress_raise_key_errors",
    "suppress_key_guessing",
    "suppress_widget_not_finalized_warnings",
)


class Settings:
    """Encapsulated package wide options."""

    __slots__ = (
        "_font",
        "_element_size",
        "_button_element_size",
        "_margins",
        "_element_padding",
        "_border_width",
        "_autoclose_time",
        "_tooltip_time",
        "_tooltip_offset",
        "_keep_on_top",
        "_scaling",
        "_alpha_channel",
        "_suppress_error_popups",
        "_suppress_raise_key_errors",
        "_suppress_key_guessing",
        "_suppress_widget_not_finalized_warnings",
    )

    def __init__(self):
        self._font = C.DEFAULT_FONT
        self._element_size = C.DEFAULT_ELEMENT_SIZE
        self._button_element_size = C.DEFAULT_BUTTON_ELEMENT_SIZE
        self._margins = C.DEFAULT_MARGINS
        self._element_padding = C.DEFAULT_ELEMENT_PADDING
        self._border_width = 1
        self._autoclose_time = C.DEFAULT_AUTOCLOSE_TIME
        self._tooltip_time = C.DEFAULT_TOOLTIP_TIME
        self._tooltip_offset = C.DEFAULT_TOOLTIP_OFFSET
        self._keep_on_top = None
        self._scaling = None
        self._alpha_channel = 1.0
        self._suppress_error_popups = False
        self._suppress_raise_key_errors = True
        self._suppress_key_guessing = False
        self._suppress_widget_not_finalized_warnings = False

    # --- typed accessors ---------------------------------------------------
    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value: Any):
        if value is not None and (not isinstance(value, tuple) or len(value) < 2):
            raise ValueError("font must be a (name, size) tuple")
        self._font = value

    @property
    def element_size(self):
        return self._element_size

    @element_size.setter
    def element_size(self, value: Any):
        self._element_size = value

    @property
    def button_element_size(self):
        return self._button_element_size

    @button_element_size.setter
    def button_element_size(self, value: Any):
        self._button_element_size = value

    @property
    def margins(self):
        return self._margins

    @margins.setter
    def margins(self, value: Any):
        self._margins = value

    @property
    def element_padding(self):
        return self._element_padding

    @element_padding.setter
    def element_padding(self, value: Any):
        self._element_padding = value

    @property
    def border_width(self):
        return self._border_width

    @border_width.setter
    def border_width(self, value: Any):
        self._border_width = int(value)

    @property
    def autoclose_time(self):
        return self._autoclose_time

    @autoclose_time.setter
    def autoclose_time(self, value: Any):
        self._autoclose_time = value

    @property
    def tooltip_time(self):
        return self._tooltip_time

    @tooltip_time.setter
    def tooltip_time(self, value: Any):
        self._tooltip_time = value

    @property
    def tooltip_offset(self):
        return self._tooltip_offset

    @tooltip_offset.setter
    def tooltip_offset(self, value: Any):
        self._tooltip_offset = value

    @property
    def keep_on_top(self):
        return self._keep_on_top

    @keep_on_top.setter
    def keep_on_top(self, value: Any):
        self._keep_on_top = value

    @property
    def scaling(self):
        return self._scaling

    @scaling.setter
    def scaling(self, value: Any):
        self._scaling = value

    @property
    def alpha_channel(self):
        return self._alpha_channel

    @alpha_channel.setter
    def alpha_channel(self, value: Any):
        self._alpha_channel = value

    @property
    def suppress_error_popups(self):
        return self._suppress_error_popups

    @suppress_error_popups.setter
    def suppress_error_popups(self, value: Any):
        self._suppress_error_popups = bool(value)

    @property
    def suppress_raise_key_errors(self):
        return self._suppress_raise_key_errors

    @suppress_raise_key_errors.setter
    def suppress_raise_key_errors(self, value: Any):
        self._suppress_raise_key_errors = bool(value)

    @property
    def suppress_key_guessing(self):
        return self._suppress_key_guessing

    @suppress_key_guessing.setter
    def suppress_key_guessing(self, value: Any):
        self._suppress_key_guessing = bool(value)

    @property
    def suppress_widget_not_finalized_warnings(self):
        return self._suppress_widget_not_finalized_warnings

    @suppress_widget_not_finalized_warnings.setter
    def suppress_widget_not_finalized_warnings(self, value: Any):
        self._suppress_widget_not_finalized_warnings = bool(value)

    # --- dict style API ----------------------------------------------------
    def as_dict(self):
        """Snapshot of every option as a dict."""
        return {name: getattr(self, name) for name in _KNOWN_OPTIONS}

    def apply_options(self, **kwargs: Any):
        """Validate and apply a batch of options."""
        for name, value in kwargs.items():
            if name not in _KNOWN_OPTIONS:
                raise TypeError(f"Unknown option: {name}")
            setattr(self, name, value)


settings = Settings()
