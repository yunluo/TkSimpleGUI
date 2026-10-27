#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TkSimpleGUI theme definitions.

Five hand picked themes, designed to look at home in both consumer apps
and commercial / industrial software. The default look is the platform
native one (``System``); the other four are tasteful, low chroma palettes
that share the same widget coverage so widgets render consistently across
all of them.

The keys every theme carries:

* ``BACKGROUND`` / ``TEXT``             - window background, foreground text
* ``INPUT`` / ``TEXT_INPUT``            - input field background, foreground
* ``SCROLL``                            - scrollbar trough
* ``BUTTON``                            - ``(text_color, background_color)``
* ``PROGRESS``                          - ``(fill_color, track_color)``
* ``BORDER`` / ``SLIDER_DEPTH`` / ``PROGRESS_DEPTH``
                                        - geometry hints (borderwidth, slider
                                          trough depth, progress bar style)
* ``COLOR_LIST``                        - ordered [bg, accent, panel, fg]
                                          palette, used by charts and pickers
* ``DESCRIPTION``                       - free-form tags ("dark", "industrial"...)
                                          for theme chooser UIs

``System`` uses the literal string ``COLOR_SYSTEM_DEFAULT`` (= ``"1234567890"``)
for every color; the theme manager recognises that sentinel and skips the
override, leaving the platform's native look intact.
"""

from .constants import COLOR_SYSTEM_DEFAULT

_NATIVE = COLOR_SYSTEM_DEFAULT

THEMES = {
    # -----------------------------------------------------------------------
    # 1. System -- platform native. The default. No color overrides.
    # -----------------------------------------------------------------------
    "System": {
        "BACKGROUND": _NATIVE,
        "TEXT": _NATIVE,
        "INPUT": _NATIVE,
        "TEXT_INPUT": _NATIVE,
        "SCROLL": _NATIVE,
        "BUTTON": _NATIVE,
        "PROGRESS": _NATIVE,
        "BORDER": 1,
        "SLIDER_DEPTH": 0,
        "PROGRESS_DEPTH": 0,
        "COLOR_LIST": ["system", "system", "system", "system"],
        "DESCRIPTION": ["native", "default", "platform"],
    },

    # -----------------------------------------------------------------------
    # 2. Slate -- deep charcoal with a steel blue accent. The professional /
    #    industrial pick. IDE / dashboard / dark mode.
    # -----------------------------------------------------------------------
    "Slate": {
        "BACKGROUND": "#1f2329",
        "TEXT": "#d4d7dc",
        "INPUT": "#2a2f37",
        "TEXT_INPUT": "#e8eaed",
        "SCROLL": "#5a6068",
        "BUTTON": ("#e8eaed", "#3a4150"),
        "PROGRESS": ("#6b9bd1", "#2a2f37"),
        "BORDER": 1,
        "SLIDER_DEPTH": 0,
        "PROGRESS_DEPTH": 0,
        "COLOR_LIST": ["#1f2329", "#6b9bd1", "#3a4150", "#d4d7dc"],
        "DESCRIPTION": ["dark", "professional", "industrial", "cool"],
    },

    # -----------------------------------------------------------------------
    # 3. Daylight -- clean white with a deep blue accent. The office / consumer
    #    classic. Maximum legibility, prints well, looks neutral.
    # -----------------------------------------------------------------------
    "Daylight": {
        "BACKGROUND": "#ffffff",
        "TEXT": "#1a1d21",
        "INPUT": "#f5f7fa",
        "TEXT_INPUT": "#1a1d21",
        "SCROLL": "#c0c5cc",
        "BUTTON": ("#ffffff", "#1f6feb"),
        "PROGRESS": ("#1f6feb", "#e3e8ef"),
        "BORDER": 1,
        "SLIDER_DEPTH": 0,
        "PROGRESS_DEPTH": 0,
        "COLOR_LIST": ["#ffffff", "#1f6feb", "#e3e8ef", "#1a1d21"],
        "DESCRIPTION": ["light", "office", "clean", "modern"],
    },

    # -----------------------------------------------------------------------
    # 4. Dusk -- warm dark with an amber accent. Evening / low-light use.
    #    Easy on the eyes, no blue light, still clearly a "dark mode" theme.
    # -----------------------------------------------------------------------
    "Dusk": {
        "BACKGROUND": "#1d1a17",
        "TEXT": "#e8e2d8",
        "INPUT": "#2a2622",
        "TEXT_INPUT": "#f0eae0",
        "SCROLL": "#6a5f50",
        "BUTTON": ("#1d1a17", "#d49a5b"),
        "PROGRESS": ("#d49a5b", "#2a2622"),
        "BORDER": 1,
        "SLIDER_DEPTH": 0,
        "PROGRESS_DEPTH": 0,
        "COLOR_LIST": ["#1d1a17", "#d49a5b", "#2a2622", "#e8e2d8"],
        "DESCRIPTION": ["dark", "warm", "evening", "cosy"],
    },

    # -----------------------------------------------------------------------
    # 5. Sage -- soft green-grey with a forest green accent. Natural / calm /
    #    fresh consumer. Distinct from the blue and warm tones of the others.
    # -----------------------------------------------------------------------
    "Sage": {
        "BACKGROUND": "#f3f5f0",
        "TEXT": "#1d231b",
        "INPUT": "#e6ebe1",
        "TEXT_INPUT": "#1d231b",
        "SCROLL": "#b8c0b1",
        "BUTTON": ("#ffffff", "#4a7c59"),
        "PROGRESS": ("#4a7c59", "#e6ebe1"),
        "BORDER": 1,
        "SLIDER_DEPTH": 0,
        "PROGRESS_DEPTH": 0,
        "COLOR_LIST": ["#f3f5f0", "#4a7c59", "#e6ebe1", "#1d231b"],
        "DESCRIPTION": ["light", "natural", "calm", "fresh"],
    },
}
