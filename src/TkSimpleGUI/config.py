#!/usr/bin/env python3
"""Declarative configuration objects (Python 3.7 dataclasses).

The widget constructors keep their keyword signatures for compatibility and
IDE discovery, but every option can also be bundled into a typed dataclass
and passed as ``config=`` — useful for sharing one look across many widgets
or building layouts from data::

    opts = ts.ElementOptions(pad=(10, 4), expand_x=True,
                             right_click_menu=["&Menu", ["Refresh"]])
    ts.TInput("", config=opts)
    ts.TText("hi", config=opts)

    cfg = ts.WindowConfig(title="Demo", resizable=True, modal=True)
    ts.Window(layout=layout, config=cfg)
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from .elements.base import Element


@dataclass
class ElementOptions:
    """The shared per-element options (everything Element.__init__ takes).

    Pass as ``config=`` to any element; explicit keyword arguments still
    override the config values.
    """

    key: Optional[Any] = None
    size: Tuple[Optional[int], Optional[int]] = (None, None)
    tooltip: Optional[str] = None
    visible: bool = True
    pad: Optional[Any] = None
    expand_x: bool = False
    expand_y: bool = False
    justification: Optional[str] = None
    right_click_menu: Optional[list] = None
    metadata: Any = None
    disabled: bool = False

    def merged(self, element: Element, **overrides) -> dict:
        """The resolved kwargs for ``element``: config values with explicit
        ``overrides`` winning. Internal helper for the constructors."""
        resolved = {
            "key": self.key,
            "size": self.size,
            "tooltip": self.tooltip,
            "visible": self.visible,
            "pad": self.pad,
            "expand_x": self.expand_x,
            "expand_y": self.expand_y,
            "justification": self.justification,
            "right_click_menu": self.right_click_menu,
            "metadata": self.metadata,
        }
        if isinstance(element, Element) and hasattr(element, "_disabled"):
            resolved["disabled"] = self.disabled
        for name, value in overrides.items():
            if value is not None:
                resolved[name] = value
        return resolved


@dataclass
class WindowConfig:
    """The Window constructor options as one typed object.

    Pass as ``config=`` to :class:`~TkSimpleGUI.window.Window`; explicit
    keyword arguments still override the config values.
    """

    title: str = ""
    layout: Optional[Any] = None
    size: Tuple[Optional[int], Optional[int]] = (None, None)
    location: Tuple[Optional[int], Optional[int]] = (None, None)
    finalize: bool = False
    keep_on_top: bool = False
    modal: bool = False
    no_titlebar: bool = False
    grab_anywhere: bool = False
    return_keyboard_events: bool = False
    icon: Optional[Any] = None
    background_color: Optional[str] = None
    margins: Optional[Tuple[int, int]] = None
    resizable: Optional[Any] = None
    disable_close: bool = False
    disable_esc: bool = False
    system_block: bool = False
    element_justification: Optional[str] = None
    right_click_menu: Optional[list] = None
    parent: Optional[Any] = None
    on_close: Optional[Any] = None

    def as_kwargs(self, **overrides) -> dict:
        """The resolved kwargs for ``Window``: config values with explicit
        ``overrides`` winning."""
        resolved = {
            field_name: getattr(self, field_name)
            for field_name in (
                "title", "layout", "size", "location", "finalize",
                "keep_on_top", "modal", "no_titlebar", "grab_anywhere",
                "return_keyboard_events", "icon", "background_color",
                "margins", "resizable", "disable_close", "disable_esc",
                "system_block", "element_justification", "right_click_menu",
                "parent", "on_close",
            )
        }
        for name, value in overrides.items():
            if value is not None:
                resolved[name] = value
        return resolved
