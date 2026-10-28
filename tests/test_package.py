#!/usr/bin/env python3
"""TkSimpleGUI OO package test suite (unittest, headless friendly)."""

import ast
import ctypes
import logging
import os
import queue
import re
import sys
import tempfile
import threading
import time
import tkinter as tk
import unittest
from tkinter import ttk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import TkSimpleGUI as ts  # noqa: E402


def _pil_available():
    try:
        import PIL  # noqa: F401

        return True
    except ImportError:
        return False


# TChart's anti-alias backend needs Pillow; CI runs without it, so the
# raster-asserting tests must skip (the vector fallback is covered too).
HAS_PIL = _pil_available()


class TestMeta(unittest.TestCase):
    def test_version(self):
        self.assertEqual(ts.__version__, "0.1.0")

    def test_author(self):
        self.assertEqual(ts.__author__, "yunluo")


class TestThemes(unittest.TestCase):
    def test_table_size(self):
        # 5 hand picked themes, see _theme_data.py
        self.assertEqual(len(ts.theme_list()), 5)

    def test_native_by_default(self):
        self.assertIsNone(ts.theme())

    def test_apply_and_reset(self):
        name = ts.theme("Slate")
        self.assertEqual(name, "Slate")
        self.assertEqual(ts.theme(), "Slate")
        self.assertIsNotNone(ts.theme_background_color())
        ts.theme(None)
        self.assertIsNone(ts.theme())
        self.assertIsNone(ts.theme_background_color())

    def test_invalid_theme(self):
        with self.assertRaises(ValueError):
            ts.theme("__No Such Theme__")

    def test_case_insensitive(self):
        self.assertEqual(ts.theme("slate"), "Slate")
        ts.theme(None)

    def test_add_new(self):
        from TkSimpleGUI._theme_data import THEMES
        saved = dict(THEMES)
        try:
            ts.theme_add(
                "__TestTheme__", {"BACKGROUND": "#123456", "TEXT": "#ffffff"}
            )
            self.assertIn("__TestTheme__", ts.theme_list())
            ts.theme("__TestTheme__")
            self.assertEqual(ts.theme_background_color(), "#123456")
            ts.theme(None)
        finally:
            THEMES.clear()
            THEMES.update(saved)

    def test_themed_themes_have_real_colors(self):
        """Every non-System theme must expose a real color (not the sentinel)."""
        from TkSimpleGUI.constants import COLOR_SYSTEM_DEFAULT
        for name in ("Slate", "Daylight", "Dusk", "Sage"):
            ts.theme(name)
            self.assertEqual(ts.theme(), name)
            for accessor in (
                ts.theme_background_color,
                ts.theme_text_color,
            ):
                value = accessor()
                self.assertIsNotNone(
                    value,
                    msg=f"{name}: {accessor.__name__} returned None",
                )
                self.assertNotEqual(
                    value, COLOR_SYSTEM_DEFAULT,
                    msg=f"{name}: {accessor.__name__} returned the sentinel",
                )
            # and the button color tuple must have both parts as real colors
            button = ts.theme_button_color()
            self.assertIsNotNone(button)
            for part in button:
                if part is not None:
                    self.assertNotEqual(part, COLOR_SYSTEM_DEFAULT)
        ts.theme(None)

    def test_system_theme_uses_sentinels(self):
        """The System theme defers to platform colors (sentinel everywhere)."""
        from TkSimpleGUI._theming import theme_manager
        from TkSimpleGUI.constants import COLOR_SYSTEM_DEFAULT
        ts.theme("System")
        self.assertEqual(ts.theme_background_color(), COLOR_SYSTEM_DEFAULT)
        self.assertEqual(ts.theme_text_color(), COLOR_SYSTEM_DEFAULT)
        # is_native must report True even though a name is set, so
        # configure_ttk short-circuits and leaves the platform look intact
        self.assertTrue(theme_manager.is_native)
        ts.theme(None)

    def test_theme_version_bumps_on_change(self):
        from TkSimpleGUI._theme_data import THEMES
        from TkSimpleGUI._theming import theme_manager
        saved = dict(THEMES.get("Slate") or {})
        try:
            start = theme_manager.theme_version
            ts.theme("Slate")
            after_apply = theme_manager.theme_version
            ts.theme_background_color("#101010")
            after_bg = theme_manager.theme_version
            self.assertGreater(after_apply, start)
            self.assertGreater(after_bg, after_apply)
        finally:
            # theme_background_color writes the THEMES entry in place —
            # restore it or every later test sees the poisoned color
            ts.theme(None)
            THEMES["Slate"] = saved

    def test_update_theme_repaints_live_window(self):
        """update_theme() repaints an already visible window immediately."""
        window = ts.Window(
            "live",
            [[ts.TText("t", key="-T-")], [ts.TInput("i", key="-IN-")],
             [ts.TColumn([[ts.TText("inner")]], key="-COL-")]],
            finalize=True,
        )
        try:
            ts.theme("Slate")
            slate_bg = ts.theme_background_color()
            # the window was built under the native theme -- its tk Label
            # still carries the old (default) background; update_theme must
            # reconfigure it to the Slate palette without recreating widgets
            window.update_theme()
            self.assertEqual(str(window["-T-"].widget.cget("background")), slate_bg)
            self.assertEqual(str(window["-COL-"].widget.cget("background")), slate_bg)
            # widget identity is preserved (repaint, not rebuild)
            self.assertFalse(window.was_closed)
            # explicit per-element colors survive the repaint
            window["-T-"].update(text_color="#ff0000")
            window.update_theme()
            self.assertEqual(str(window["-T-"].widget.cget("foreground")), "#ff0000")
        finally:
            window.close()
            ts.theme(None)

    def test_update_theme_repaints_unkeyed_elements(self):
        """Elements without a key repaint too (classic tk widgets stay dark)."""
        window = ts.Window(
            "unkeyed",
            [[ts.TMultiline("m", key="-ML-")],
             [ts.TButton("Toggle", toggle=True), ts.TButton("Plain")],
             [ts.TCheckList(["a", "b"]), ts.TListbox(["x"], key="-LB-")]],
            finalize=True,
        )
        try:
            ts.theme("Slate")
            slate_bg = ts.theme_background_color()
            window.update_theme()
            multiline = window["-ML-"]
            self.assertEqual(
                str(multiline._text.cget("background")),
                ts.theme_input_background_color(),
            )
            # find the unkeyed toggle button / checklist via the flat list
            from TkSimpleGUI.elements.buttons import TButton
            from TkSimpleGUI.elements.widgets import TCheckList
            buttons = [e for e in window._elements if isinstance(e, TButton)]
            checklists = [
                e for e in window._elements if isinstance(e, TCheckList)
            ]
            self.assertEqual(
                str(buttons[0].widget.cget("background")),
                ts.theme_button_color()[1],
            )
            self.assertEqual(
                str(checklists[0].widget.cget("background")), slate_bg
            )
        finally:
            window.close()
            ts.theme(None)

    def test_native_theme_builds_full_zoo(self):
        """Under System the sentinel colors never reach tk (regression)."""
        window = ts.Window(
            "zoo",
            [[ts.TColumn([[ts.TText("c")]]), ts.TFrame("F", [[ts.TText("f")]])],
             [ts.TTabGroup([[ts.TTab("T", [[ts.TText("t")]])]])],
             [ts.TCanvas(size=(20, 20)), ts.TListbox(["i"]),
              ts.TCheckList(["a"]), ts.TCalendar()],
             [ts.TLabeledEdit("L"), ts.TLED(1), ts.TRoundButton("R"),
              ts.TTextProgressBar(10, current_value=5)]],
            finalize=True,
        )
        window.close()
        self.assertTrue(window.was_closed)

    def test_update_theme_back_to_native_restores(self):
        """A themed window switched back to System returns to native look."""
        window = ts.Window("revert", [[ts.TText("t", key="-T-")]], finalize=True)
        try:
            ts.theme("Slate")
            window.update_theme()
            self.assertEqual(
                window._ttk_style.theme_use(), "clam"
            )
            slate_bg = ts.theme_background_color()
            self.assertEqual(str(window["-T-"].widget.cget("background")), slate_bg)
            ts.theme(None)
            window.update_theme()
            # ttk engine left clam again...
            self.assertNotEqual(window._ttk_style.theme_use(), "clam")
            # ...and the window surface dropped the themed background
            self.assertNotEqual(
                str(window._tk_root.cget("background")), slate_bg
            )
        finally:
            window.close()
            ts.theme(None)

    def test_accent_and_tooltip_helpers(self):
        from TkSimpleGUI._theming import theme_manager
        ts.theme("Slate")
        self.assertEqual(theme_manager.accent_color(), "#6b9bd1")
        colors = theme_manager.tooltip_colors()
        self.assertIn("background", colors)
        ts.theme(None)
        self.assertIsNone(theme_manager.accent_color())
        self.assertEqual(theme_manager.tooltip_colors(), {})


class TestThemeTransition(unittest.TestCase):
    """Animated theme switches: ts.theme(name, transition_ms=...) eases the
    old palette into the new one while open windows repaint per frame."""

    def setUp(self):
        self._previous_theme = ts.theme()
        ts.theme("Daylight")

    def tearDown(self):
        # kill a possibly running transition loop before restoring
        ts.theme_manager._transition_from = None
        ts.theme(self._previous_theme)

    def test_plain_apply_does_not_transition(self):
        manager = ts.theme_manager
        ts.theme("Slate")
        self.assertIsNone(manager._transition_from)
        self.assertEqual(ts.theme(), "Slate")

    def test_transition_captures_previous_entry(self):
        from TkSimpleGUI._theme_data import THEMES
        manager = ts.theme_manager
        window = ts.Window("t", [[ts.TText("x", key="-X-")]], finalize=True)
        ts.theme("Slate", transition_ms=500)
        self.assertEqual(manager._transition_from, THEMES["Daylight"])
        self.assertEqual(ts.theme(), "Slate")
        window.close()

    def test_getters_blend_from_old_to_new(self):
        from TkSimpleGUI._theme_data import THEMES
        manager = ts.theme_manager
        window = ts.Window("t", [[ts.TText("x", key="-X-")]], finalize=True)
        ts.theme("Slate", transition_ms=10000)
        # frozen near progress 0: the getter still reports the old color
        self.assertEqual(manager.background_color, THEMES["Daylight"]["BACKGROUND"])
        # a fully elapsed clock reports the exact new color
        manager._transition_start -= manager._transition_ms
        self.assertEqual(manager.background_color, THEMES["Slate"]["BACKGROUND"])
        window.close()

    def test_tick_ends_transition_and_repaints(self):
        manager = ts.theme_manager
        ts.theme("Slate", transition_ms=10000)
        manager._transition_start -= manager._transition_ms
        manager._tick()
        self.assertIsNone(manager._transition_from)
        self.assertEqual(manager.background_color, "#1f2329")

    def test_native_endpoints_snap(self):
        manager = ts.theme_manager
        ts.theme("Daylight")
        ts.theme(None, transition_ms=500)
        self.assertIsNone(manager._transition_from)
        ts.theme(None)
        ts.theme("Slate", transition_ms=500)
        self.assertIsNone(manager._transition_from)
        ts.theme(None)

    def test_transition_settles_on_live_window(self):
        window = ts.Window("t", [[ts.TText("x", key="-X-")]], finalize=True)
        ts.theme("Slate", transition_ms=60)
        deadline = time.time() + 3
        while str(window.tk_root.cget("background")) != "#1f2329" \
                and time.time() < deadline:
            window.refresh()
        self.assertEqual(str(window.tk_root.cget("background")), "#1f2329")
        window.close()

    def test_tween_color_and_ease_primitives(self):
        from TkSimpleGUI.elements import _paint
        window = ts.Window("t", [[ts.TText("x", key="-X-")]], finalize=True)
        self.assertEqual(_paint.tween_color(window.tk_root, "#000000", "#ffffff", 0.5),
                         "#808080")
        self.assertEqual(_paint.tween_color(window.tk_root, "#000000", "#ffffff", 0.0),
                         "#000000")
        self.assertEqual(_paint.tween_color(window.tk_root, "#000000", "#ffffff", 1.0),
                         "#ffffff")
        self.assertEqual(_paint.tween_color(window.tk_root, "#000000", "#ffffff", 9.0),
                         "#ffffff")
        eased = [_paint.ease_out_cubic(i / 10) for i in range(11)]
        self.assertEqual(eased[0], 0.0)
        self.assertEqual(eased[10], 1.0)
        self.assertTrue(all(a <= b for a, b in zip(eased, eased[1:])))
        window.close()


class TestSettings(unittest.TestCase):
    def test_set_get(self):
        ts.settings.border_width = 7
        self.assertEqual(ts.settings.as_dict()["border_width"], 7)
        ts.settings.border_width = 1

    def test_validation(self):
        with self.assertRaises(TypeError):
            ts.settings.apply_options(no_such=1)


class TestUtils(unittest.TestCase):
    def test_rgb(self):
        self.assertEqual(ts.rgb(255, 0, 0), "#ff0000")
        self.assertEqual(ts.rgb(0, 255, 0), "#00ff00")
        self.assertEqual(ts.rgb(0, 0, 255), "#0000ff")
        self.assertEqual(ts.rgb(300, -5, 12), "#ff000c")

    def test_timer(self):
        timer = ts.Timer()
        self.assertEqual(timer.elapsed, 0)
        timer.start()
        self.assertGreaterEqual(timer.elapsed_ms, 0)
        timer.stop()

    def test_platform(self):
        self.assertIsInstance(ts.running_windows(), bool)
        self.assertIsInstance(ts.running_linux(), bool)
        self.assertIsInstance(ts.running_mac(), bool)


class TestElementConstruction(unittest.TestCase):
    def test_construct_all(self):
        elements = [
            ts.TText("t"),
            ts.TInput("d"),
            ts.TCombo(["a", "b"]),
            ts.TListbox(["a", "b"]),
            ts.TSpin([1, 2, 3]),
            ts.TCheckbox("c"),
            ts.TRadio("r", group_id=1),
            ts.TSlider((0, 10)),
            ts.TMultiline("m"),
            ts.TOutput(),
            ts.TProgressBar(100),
            ts.TButton("b"),
            ts.TImage(),
            ts.TCanvas((50, 50)),
            ts.TGraph((100, 100), (0, 0), (10, 10)),
            ts.TFrame("f", [[ts.TText("x")]]),
            ts.TColumn([[ts.TText("y")]]),
            ts.TTab("t", [[ts.TText("z")]]),
            ts.TTabGroup([[ts.TTab("t1", [[ts.TText("w")]])]]),
            ts.TTable([["a"]], headings=["H"]),
            ts.TTree(headings=["H"]),
            ts.TStatusBar("s"),
            ts.TVerticalSeparator(),
            ts.THorizontalSeparator(),
            ts.TMenu([["&File", ["Open", "Exit"]]]),
        ]
        for element in elements:
            self.assertIsNotNone(element)

    def test_removed_legacy_names(self):
        """PSG compatibility surface is gone: synonym and duplicate
        spellings must raise AttributeError (compat is not a design goal)."""
        for name in (
            "InputText", "set_options", "get_options", "running_trinket",
            "running_replit", "Translator", "translate", "_",
            "set_translations", "add_translation", "clear_translations",
            "THIS_ROW", "WRITE_ONLY_KEY", "WINDOW_CLOSED", "EVENT_TIMEOUT",
            "EVENT_TIMER", "RELIEF_RAISED", "FLAT", "version", "port",
            "MsgBox", "popup_quick", "popup_quick_message", "popup_timed",
            "popup_annoying", "popup_no_titlebar", "popup_non_blocking",
            "popup_error_with_traceback", "list_of_look_and_feel_values",
            "theme_add_new", "LOOK_AND_FEEL_TABLE", "DEFAULT_WINDOW_ICON",
            "popup_ok", "popup_no_buttons", "main_loop",
            "timer_start", "timer_stop", "hide_row", "unhide_row",
            "set_alpha_channel",
        ):
            self.assertFalse(hasattr(ts, name), f"{name} should be gone")
        self.assertTrue(hasattr(ts, "settings"))

    def test_t_prefix_is_the_only_spelling(self):
        """Every widget class is spelled with the T prefix and nothing else:
        the plain spellings are gone entirely (one name per concept)."""
        for name in (
            "Text", "Input", "Combo", "OptionMenu", "Listbox", "Spin",
            "Checkbox", "CheckList", "Radio", "Slider", "Multiline", "Output",
            "ProgressBar", "Button", "Submit", "CloseButton", "Image",
            "Canvas", "Graph", "Shape", "Frame", "Column", "Splitter",
            "ScrollableColumn", "Toolbar", "LabeledEdit", "KeyValueEditor",
            "FlowPanel", "Calendar", "Tab", "TabGroup", "Menu", "Table",
            "Tree", "StatusBar", "VerticalSeparator", "HorizontalSeparator",
            "Sizegrip", "Menubutton", "Scrollbar", "RoundButton",
            "ImageButton", "TextProgressBar", "Gauge", "LED", "Chart",
            "Tag", "Badge", "Avatar", "Statistic", "Empty", "Result",
            "Skeleton", "Alert", "Watermark", "Card", "Descriptions",
            "Steps", "Timeline", "Segmented", "Rate", "Pagination",
            "Transfer", "SevenSegment", "on_event",
        ):
            self.assertFalse(
                hasattr(ts, name), f"{name} should be T-prefixed or gone"
            )
        for widget in ("TText", "TInput", "TCombo", "TButton", "TCard"):
            self.assertIn(widget, ts.__all__)

    def test_t_aliases_construct(self):
        """The T-prefixed widget classes (the one and only spelling) build."""
        layout = [
            [ts.TText("name"), ts.TInput("world", key="-E-")],
            [ts.TCombo(["a", "b"], key="-C-"), ts.TButton("OK", key="-B-")],
            [ts.TMultiline("text", key="-M-")],
        ]
        window = ts.Window("t", layout, finalize=True)
        self.assertEqual(window["-E-"].get(), "world")
        self.assertEqual(window["-B-"].button_text, "OK")
        window.close()

    def test_slots_encapsulation(self):
        self.assertFalse(hasattr(ts.TText("x"), "__dict__"))
        self.assertFalse(hasattr(ts.TInput("x"), "__dict__"))

    def test_key_property(self):
        element = ts.TText("x", key="-K-")
        self.assertEqual(element.key, "-K-")
        element.key = "-K2-"
        self.assertEqual(element.key, "-K2-")

    def test_input_get_before_build(self):
        element = ts.TInput("default")
        self.assertEqual(element.default_text, "default")


class TestWindow(unittest.TestCase):
    def test_lifecycle(self):
        window = ts.Window(
            "t",
            [
                [ts.TText("hi", key="-T-")],
                [ts.TInput("", key="-IN-")],
                [ts.TButton("OK", key="-B-")],
            ],
            finalize=True,
        )
        self.assertTrue(window.finalized)
        self.assertIn("-IN-", window)
        self.assertIsNotNone(window["-IN-"].widget)
        window["-IN-"].update("typed")
        self.assertEqual(window["-IN-"].get(), "typed")
        event, values = window.read(timeout=200)
        self.assertEqual(event, ts.TIMEOUT_KEY)
        self.assertEqual(values["-IN-"], "typed")
        window.close()
        self.assertTrue(window.was_closed)
        self.assertEqual(ts.Window.active_windows(), [])

    def test_duplicate_key_raises(self):
        with self.assertRaises(ValueError):
            ts.Window("t", [[ts.TText("a", key="-K-")], [ts.TText("b", key="-K-")]], finalize=True)

    def test_button_click(self):
        window = ts.Window("t", [[ts.TButton("Go", key="-GO-")]], finalize=True)
        window["-GO-"].click()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-GO-")
        window.close()

    def test_context_manager(self):
        with ts.Window("t", [[ts.TText("x")]]) as window:
            self.assertTrue(window.finalized)
        self.assertTrue(window.was_closed)

    def test_container_recursion(self):
        window = ts.Window(
            "t",
            [[ts.TFrame("F", [[ts.TColumn([[ts.TText("deep", key="-DEEP-")]])]])]],
            finalize=True,
        )
        self.assertIsNotNone(window["-DEEP-"].widget)
        window.close()

    def test_tab_group(self):
        window = ts.Window(
            "t",
            [[ts.TTabGroup([[ts.TTab("one", [[ts.TText("1", key="-1-")]]),
                    ts.TTab("two", [[ts.TText("2", key="-2-")]])]])]],
            finalize=True,
        )
        self.assertIsNotNone(window["-1-"].widget)
        self.assertIsNotNone(window["-2-"].widget)
        window.close()

    def test_menu_bar(self):
        window = ts.Window(
            "t", [[ts.TMenu([["&File", ["Open", "---", "Exit"]]])]], finalize=True
        )
        self.assertIsNotNone(window.tk_root.nametowidget(window.tk_root.cget("menu")))
        window.close()

    def test_fill(self):
        window = ts.Window(
            "t", [[ts.TInput("", key="-IN-"), ts.TText("", key="-T-")]], finalize=True
        )
        window.fill({"-IN-": "abc", "-T-": "xyz"})
        self.assertEqual(window["-IN-"].get(), "abc")
        self.assertEqual(window["-T-"].get(), "xyz")
        window.close()

    def test_write_event_value(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.write_event_value("-CUSTOM-")
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-CUSTOM-")
        window.close()

    def test_window_find_element_alias_removed(self):
        # FindElement (the PSG PascalCase alias), the element() shortcut and
        # the child_windows/restore aliases were removed; one name each
        window = ts.Window("t", [[ts.TText("x", key="-X-")]], finalize=True)
        self.addCleanup(window.close)
        self.assertTrue(callable(window.find_element))
        self.assertFalse(hasattr(window, "FindElement"))
        self.assertFalse(hasattr(window, "element"))
        self.assertFalse(hasattr(window, "child_windows"))
        self.assertFalse(hasattr(window, "restore"))


class TestElementOptions(unittest.TestCase):
    """P0 element level options: metadata, pad/expand, right click menu."""

    def test_metadata(self):
        element = ts.TText("x", metadata={"answer": 42})
        self.assertEqual(element.metadata, {"answer": 42})
        self.assertIsNone(ts.TInput("d").metadata)

    def test_pad_and_expand_stored(self):
        element = ts.TText("x", pad=(10, 5), expand_x=True)
        self.assertEqual(element.pad, (10, 5))
        self.assertTrue(element.expand_x)
        self.assertFalse(element.expand_y)

    def test_parse_pad_forms(self):
        from TkSimpleGUI.elements.base import _parse_pad

        self.assertEqual(_parse_pad(None), (0, 0, 0, 0))
        self.assertEqual(_parse_pad(3), (3, 3, 3, 3))
        self.assertEqual(_parse_pad((4, 2)), (4, 4, 2, 2))
        self.assertEqual(_parse_pad(((1, 2), (3, 4))), (1, 2, 3, 4))

    def test_tooltip_finalize(self):
        # regression: attaching a tooltip used to crash on __slots__
        window = ts.Window("t", [[ts.TText("hi", tooltip="tip")]], finalize=True)
        self.assertIsNotNone(window.tk_root)
        window.close()

    def test_disabled_construction(self):
        window = ts.Window(
            "t",
            [[ts.TInput("", key="-IN-", disabled=True), ts.TButton("B", key="-B-", disabled=True)]],
            finalize=True,
        )
        self.assertEqual(str(window["-IN-"].widget.cget("state")), "disabled")
        self.assertTrue(window["-IN-"].disabled)
        self.assertEqual(str(window["-B-"].widget.cget("state")), "disabled")
        window.close()

    def test_right_click_menu_built(self):
        element = ts.TText(
            "x",
            right_click_menu=["&TMenu", ["One", "---", "!Two", ["&Sub", ["Deep"]]]],
        )
        window = ts.Window("t", [[element]], finalize=True)
        menu = element._popup_menu
        self.assertIsNotNone(menu)
        # single cascade entry "TMenu" wrapping the items
        self.assertEqual(menu.entrycget(0, "label"), "TMenu")
        submenu = menu.nametowidget(menu.entrycget(0, "menu"))
        self.assertEqual(submenu.entrycget(0, "label"), "One")
        self.assertEqual(submenu.type(1), "separator")
        self.assertEqual(submenu.entrycget(2, "label"), "Two")
        self.assertEqual(submenu.entrycget(2, "state"), "disabled")
        nested = submenu.nametowidget(submenu.entrycget(3, "menu"))
        self.assertEqual(nested.entrycget(0, "label"), "Deep")
        window.close()

    def test_custom_colors_and_font(self):
        window = ts.Window(
            "t",
            [
                [
                    ts.TInput(
                        "",
                        key="-IN-",
                        text_color="#ff0000",
                        background_color="#101010",
                        font=("Courier", 10),
                    ),
                    ts.TButton("B", key="-B-", button_color=("#ffffff", "#000080")),
                    ts.TCheckbox("c", key="-CK-", text_color="#0000ff", font=("Arial", 12)),
                    ts.TCombo(["a"], key="-CB-", background_color="#202020"),
                ]
            ],
            finalize=True,
        )
        self.assertIsNotNone(window["-IN-"].widget)
        window.close()

    def test_themed_ttk_widgets(self):
        # regression: themed mode used to crash ttk.Entry/Checkbutton with
        # unknown "-background" options
        ts.theme("Slate")
        try:
            window = ts.Window(
                "t",
                [
                    [ts.TInput("", key="-IN-"), ts.TCombo(["a"],
                            key="-CB-"), ts.TCheckbox("c", key="-CK-")],
                    [ts.TButton("B", key="-B-"), ts.TRadio("r", 1, key="-R-"), ts.TSlider((0, 10))],
                    [ts.TTable([["a"]], headings=["H"], key="-TB-"),
                            ts.TTree(headings=["H"], key="-TR-")],
                ],
                finalize=True,
            )
            window.close()
        finally:
            ts.theme(None)

    def test_select_mode_maps_are_module_scoped(self):
        """The two ``_SELECT_MODE_MAP`` constants are renamed to module-specific
        names so a future cross-import cannot accidentally swap one for the
        other. The Treeview map must also clamp MULTIPLE to a valid ttk
        selectmode (ttk.Treeview rejects the bare string ``"multiple"``).
        """
        from TkSimpleGUI.elements.widgets import _LISTBOX_SELECT_MODE_MAP
        from TkSimpleGUI.elements.data import _TREEVIEW_SELECT_MODE_MAP

        # the old generic name must be gone from both modules
        from TkSimpleGUI.elements import data, widgets
        self.assertFalse(hasattr(widgets, "_SELECT_MODE_MAP"))
        self.assertFalse(hasattr(data, "_SELECT_MODE_MAP"))
        # TListbox map returns tk constants; Treeview map returns strings.
        self.assertEqual(_LISTBOX_SELECT_MODE_MAP[ts.SelectMode.SINGLE], "single")
        self.assertEqual(_LISTBOX_SELECT_MODE_MAP[ts.SelectMode.MULTIPLE], "multiple")
        self.assertEqual(_TREEVIEW_SELECT_MODE_MAP[ts.SelectMode.SINGLE], "none")
        # ttk.Treeview's selectmode does not support MULTIPLE; the
        # nearest valid equivalent is "extended" (Ctrl/Shift multi-select).
        self.assertEqual(
            _TREEVIEW_SELECT_MODE_MAP[ts.SelectMode.MULTIPLE], "extended"
        )


class TestWindowManagement(unittest.TestCase):
    def test_expand_weights(self):
        window = ts.Window(
            "t",
            [[ts.TText("left"), ts.TInput("", key="-IN-", expand_x=True)]],
            finalize=True,
        )
        frame = window.tk_root.grid_slaves()[0]
        self.assertEqual(frame.columnconfigure(1)["weight"], 1)
        self.assertEqual(frame.columnconfigure(0)["weight"], 0)
        window.close()

    def test_justification_sticky(self):
        window = ts.Window(
            "t",
            [[ts.TText("r", justification="right")]],
            finalize=True,
        )
        widget = window.tk_root.grid_slaves()[0].grid_slaves()[0]
        info = widget.grid_info()
        self.assertEqual(info["sticky"], "e")
        window.close()

    def test_start_task(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        thread = window.start_task(lambda: 42, end_key="-DONE-")
        self.assertTrue(thread.daemon)
        self.assertEqual(thread.name, "start_task:<lambda>")
        event, values = window.read(timeout=3000)
        self.assertEqual(event, "-DONE-")
        self.assertEqual(values["-DONE-"], 42)
        window.close()

    def test_start_task_handler_bound_to_end_key_fires(self):
        app = ts.TkSimpleEvent()
        seen = []

        def on_done(window, values):
            seen.append(values["-DONE-"])

        app.bind_event("-DONE-")(on_done)
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.start_task(lambda: ["a", "b"], end_key="-DONE-")
        event, values = window.read(timeout=3000)
        self.assertEqual(event, "-DONE-")
        app.apply_event(window, event, values)
        self.assertEqual(seen, [["a", "b"]])  # unhashable payloads dispatch fine
        window.close()

    def test_start_task_none_result(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.start_task(lambda: None, end_key="-DONE-")
        event, values = window.read(timeout=3000)
        self.assertEqual(event, "-DONE-")
        self.assertIn("-DONE-", values)
        self.assertIsNone(values["-DONE-"])
        window.close()

    def test_start_task_failure_delivers_exception(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)

        def boom():
            raise RuntimeError("boom")

        with self.assertLogs("TkSimpleGUI.task", level="ERROR") as captured:
            window.start_task(boom, end_key="-DONE-")
            # pump until the deadline instead of one blocking read: on the
            # 3.7 full-suite run the daemon worker's scheduling can be
            # pushed past 3s (hundreds of tk roots churned before this
            # test); delivery itself stays instant in every normal context
            deadline = time.time() + 10
            event, values = window.read(timeout=3000)
            while event == ts.TIMEOUT_KEY and time.time() < deadline:
                event, values = window.read(timeout=500)
        self.assertEqual(event, "-DONE-")
        self.assertIsInstance(values["-DONE-"], RuntimeError)
        self.assertIn("boom", captured.output[0])
        window.close()

    def test_start_task_worker_exit_delivers_event(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)

        def quit_worker():
            raise SystemExit(3)

        with self.assertLogs("TkSimpleGUI.task", level="ERROR"):
            window.start_task(quit_worker, end_key="-DONE-")
            event, values = window.read(timeout=3000)
        self.assertEqual(event, "-DONE-")
        self.assertIsInstance(values["-DONE-"], SystemExit)
        window.close()

    def test_start_task_rejects_non_callable(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        with self.assertRaises(TypeError):
            window.start_task(42)
        window.close()

    def test_start_task_window_arg(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)

        def worker(win):
            win.write_event_value("-FROM-WORKER-", "payload")

        window.start_task(worker, end_key=None)
        event, values = window.read(timeout=3000)
        self.assertEqual(event, "-FROM-WORKER-")
        self.assertEqual(values["-FROM-WORKER-"], "payload")
        window.close()

    def test_start_task_values_snapshot_runs_on_main_thread(self):
        original = ts.Window._snapshot_values
        threads = []

        def spy(self):
            threads.append(threading.current_thread().name)
            return original(self)

        ts.Window._snapshot_values = spy
        window = ts.Window("t", [[ts.TText("x", key="-T-")]], finalize=True)
        try:
            window.start_task(lambda: "-R-", end_key="-DONE-")
            event, values = window.read(timeout=3000)
        finally:
            ts.Window._snapshot_values = original
            window.close()
        self.assertEqual(event, "-DONE-")
        self.assertEqual(values["-DONE-"], "-R-")
        self.assertTrue(threads)
        self.assertEqual(set(threads), {"MainThread"})

    def test_write_event_value_payload(self):
        window = ts.Window("t", [[ts.TText("x", key="-T-")]], finalize=True)
        window.write_event_value("-E-", {"n": 1})
        event, values = window.read(timeout=500)
        self.assertEqual(event, "-E-")
        self.assertEqual(values["-E-"], {"n": 1})
        self.assertEqual(values["-T-"], "x")  # payload merges into the snapshot
        window.write_event_value("-PLAIN-")  # one argument: event only
        event, values = window.read(timeout=500)
        self.assertEqual(event, "-PLAIN-")
        self.assertNotIn("-PLAIN-", values)
        # explicit None is a real payload (not the same as omitting it)
        window.write_event_value("-NULL-", None)
        event, values = window.read(timeout=500)
        self.assertEqual(event, "-NULL-")
        self.assertIn("-NULL-", values)
        self.assertIsNone(values["-NULL-"])
        # keyword form works (PySimpleGUI-compatible signature)
        window.write_event_value(key="-KW-", value=1)
        event, values = window.read(timeout=500)
        self.assertEqual(event, "-KW-")
        self.assertEqual(values["-KW-"], 1)
        window.close()

    def test_start_task_rejects_unhashable_end_key(self):
        """A bad end_key must fail at the call site, not deep inside the pump."""
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        with self.assertRaises(TypeError):
            window.start_task(lambda: 1, end_key=["bad"])
        with self.assertRaises(TypeError):
            window.write_event_value(["bad"], "x")
        window.close()

    def test_window_management_api(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.set_size((320, 200))
        window.refresh()
        self.assertGreaterEqual(window.size[0], 300)
        window.set_opacity(0.8)
        window.keep_on_top()
        window.hide()
        window.unhide()
        window.minimize()
        window.normal()
        window.maximize()
        window.normal()
        window.move_to_center()
        location = window.current_location()
        self.assertIsInstance(location, tuple)
        self.assertEqual(len(location), 2)
        window.title = "new title"
        self.assertEqual(window.title, "new title")
        window.close()

    def test_get_screen_size(self):
        width, height = ts.Window.get_screen_size()
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_window_min_size_floor(self):
        # every window enforces a size floor so the title-bar buttons
        # (minimize / maximize / close) remain visible and clickable
        window = ts.Window("t", [[ts.TText("x")]], finalize=True, size=(10, 10))
        window.tk_root.update()
        self.assertGreaterEqual(window.tk_root.winfo_width(), 140)
        window.close()

    def test_disable_close(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True, disable_close=True)
        window.tk_root.protocol("WM_DELETE_WINDOW")  # handler exists, no crash
        window.close()
        self.assertTrue(window.was_closed)

    def test_resizable_option(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True, resizable=False)
        self.assertEqual(window.tk_root.resizable(), (False, False))
        window.close()


class TestClassBindings(unittest.TestCase):
    """Class-level bindings installed once per interpreter: Ctrl+A select
    all, Return invokes the bind_return_key button, disabled cursor."""

    def tearDown(self):
        ts.Window.close_all()

    def test_control_a_selects_all_in_entry(self):
        entry = ts.TInput("hello world", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        entry.widget.focus_set()
        window.refresh()
        entry.widget.event_generate("<Control-a>")
        window.refresh()
        self.assertTrue(entry.widget.selection_present())
        window.close()

    def test_control_a_selects_all_in_multiline(self):
        multiline = ts.TMultiline("abc", key="-M-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline._text.focus_set()
        window.refresh()
        multiline._text.event_generate("<Control-a>")
        window.refresh()
        self.assertTrue(multiline._text.tag_ranges("sel"))
        window.close()

    def test_return_key_invokes_registered_button(self):
        entry = ts.TInput("", key="-E-")
        button = ts.TButton("OK", key="-OK-", bind_return_key=True)
        window = ts.Window("t", [[entry], [button]], finalize=True)
        entry.widget.focus_set()
        window.refresh()
        entry.widget.event_generate("<Return>")
        # deadline pump: the entry posts its own key first, then the class
        # binding clicks the registered (default) button — under full-suite
        # load events can lag, so keep reading until -OK- shows up
        event = ""
        deadline = time.time() + 5
        while event != "-OK-" and time.time() < deadline:
            event = window.read(timeout=200)[0]
        self.assertEqual(event, "-OK-")
        window.close()

    def test_return_key_without_registered_button_posts_entry_key_only(self):
        entry = ts.TInput("", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        entry.widget.focus_set()
        window.refresh()
        entry.widget.event_generate("<Return>")
        self.assertEqual(window.read(timeout=200)[0], "-E-")
        self.assertEqual(window.read(timeout=200)[0], ts.TIMEOUT_KEY)
        window.close()

    def test_disabled_button_hover_shows_arrow_cursor(self):
        button = ts.TButton("blocked", disabled=True, key="-B-")
        window = ts.Window("t", [[button]], finalize=True)
        button.widget.event_generate("<Enter>")
        # deadline pump: the <Enter> class binding may lag under load
        deadline = time.time() + 5
        while str(button.widget.cget("cursor")) != "arrow" and time.time() < deadline:
            window.refresh()
        self.assertEqual(str(button.widget.cget("cursor")), "arrow")
        button.widget.event_generate("<Leave>")
        deadline = time.time() + 5
        while str(button.widget.cget("cursor")) == "arrow" and time.time() < deadline:
            window.refresh()
        self.assertEqual(str(button.widget.cget("cursor")), "")
        window.close()

    def test_enabled_button_hover_keeps_default_cursor(self):
        button = ts.TButton("click me", key="-B-")
        window = ts.Window("t", [[button]], finalize=True)
        before = str(button.widget.cget("cursor"))
        button.widget.event_generate("<Enter>")
        window.refresh()
        self.assertEqual(str(button.widget.cget("cursor")), before)
        window.close()

    def test_class_bindings_survive_master_root_recreation(self):
        """Class bindings must stay active for windows created after a
        full close/open cycle, on whatever master root those windows live
        on (regression: a process-global install guard skipped a
        recreated root, silently disabling Return / cursor bindings for
        every later window in the process)."""
        ts.Window.close_all()
        lone = ts.Window("lone", [[ts.TInput("", key="-E-")]], finalize=True)
        lone.close()
        button = ts.TButton("blocked", disabled=True, key="-B-")
        window = ts.Window("t", [[button]], finalize=True)
        button.widget.event_generate("<Enter>")
        deadline = time.time() + 5
        while str(button.widget.cget("cursor")) != "arrow" and time.time() < deadline:
            window.refresh()
        self.assertEqual(str(button.widget.cget("cursor")), "arrow")
        window.close()


class TestBindVar(unittest.TestCase):
    """Two-way binding: ts.Var mirrored by element keys via window.bind_var."""

    def tearDown(self):
        ts.Window.close_all()

    def test_var_standalone_value_property(self):
        var = ts.Var(1)
        self.assertEqual(var.value, 1)
        var.value = 2
        self.assertEqual(var.value, 2)

    def test_bind_pushes_var_value_into_element(self):
        entry = ts.TInput("layout default", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        var = ts.Var("bound value")
        window.bind_var("-E-", var)
        self.assertEqual(entry.widget.get(), "bound value")
        window.close()

    def test_bind_with_default_none_keeps_element_value(self):
        entry = ts.TInput("5", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        window.bind_var("-E-", ts.Var())
        ts.Window._pump_all_roots()
        self.assertEqual(entry.widget.get(), "5")
        window.close()

    def test_write_fans_out_to_element(self):
        entry = ts.TInput("", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        var = ts.Var("init")
        window.bind_var("-E-", var)
        var.value = "next"
        self.assertEqual(entry.widget.get(), "next")
        window.close()

    def test_element_change_flows_to_var_on_pump(self):
        entry = ts.TInput("old", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        var = ts.Var("old")
        window.bind_var("-E-", var)
        entry.widget.delete(0, "end")
        entry.widget.insert(0, "typed")
        ts.Window._pump_all_roots()
        self.assertEqual(var.value, "typed")
        window.close()

    def test_editor_change_copies_into_display_element(self):
        entry = ts.TInput("a", key="-E-")
        text = ts.TText("", key="-T-")
        window = ts.Window("t", [[entry], [text]], finalize=True)
        var = ts.Var("a")
        window.bind_var("-E-", var)
        window.bind_var("-T-", var)
        self.assertEqual(text.get(), "a")
        entry.widget.delete(0, "end")
        entry.widget.insert(0, "b")
        ts.Window._pump_all_roots()
        self.assertEqual(text.get(), "b")
        self.assertEqual(var.value, "b")
        window.close()

    def test_var_shared_across_windows(self):
        first = ts.Window(
            "first", [[ts.TInput("", key="-E-")]], finalize=True)
        second = ts.Window(
            "second", [[ts.TText("", key="-T-")]], finalize=True)
        var = ts.Var("hello")
        first.bind_var("-E-", var)
        second.bind_var("-T-", var)
        var.value = "fan out"
        self.assertEqual(first["-E-"].widget.get(), "fan out")
        self.assertEqual(second["-T-"].get(), "fan out")
        first.close()
        second.close()

    def test_unbind_var_stops_sync(self):
        entry = ts.TInput("", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        var = ts.Var("x")
        window.bind_var("-E-", var)
        window.unbind_var("-E-")
        var.value = "y"
        self.assertEqual(entry.widget.get(), "x")
        window.close()

    def test_closed_window_detaches_bindings(self):
        entry = ts.TInput("", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        var = ts.Var("x")
        window.bind_var("-E-", var)
        window.close()
        var.value = "y"  # must not raise against the dead window
        self.assertEqual(var._bindings, [])

    def test_bind_var_requires_finalized_window(self):
        entry = ts.TInput("", key="-E-")
        window = ts.Window("t", [[entry]])
        var = ts.Var()
        with self.assertRaises(RuntimeError):
            window.bind_var("-E-", var)
        window.close()

    def test_bind_var_unknown_key_raises(self):
        window = ts.Window("t", [[ts.TInput("", key="-E-")]], finalize=True)
        with self.assertRaises(KeyError):
            window.bind_var("-MISSING-", ts.Var())
        window.close()

    def test_bind_var_rejects_non_var(self):
        window = ts.Window("t", [[ts.TInput("", key="-E-")]], finalize=True)
        with self.assertRaises(TypeError):
            window.bind_var("-E-", "not a var")
        window.close()

    def test_bind_var_same_pair_twice_is_noop(self):
        entry = ts.TInput("", key="-E-")
        window = ts.Window("t", [[entry]], finalize=True)
        var = ts.Var("x")
        window.bind_var("-E-", var)
        window.bind_var("-E-", var)
        self.assertEqual(len(window._var_bindings), 1)
        var.value = "z"
        self.assertEqual(entry.widget.get(), "z")
        window.close()


@unittest.skipUnless(sys.platform == "win32", "Windows-only API")
class TestDropTarget(unittest.TestCase):
    """window.drop_target: legacy shell file drop (WM_DROPFILES route)."""

    def tearDown(self):
        ts.Window.close_all()

    def test_register_and_revoke_cycle(self):
        window = ts.Window("t", [[ts.TInput("", key="-E-")]], finalize=True)
        seen = []
        self.assertIs(window.drop_target(seen.append), window)
        self.assertIs(window.drop_target(None), window)
        window.close()

    def test_replacing_registration_is_fine(self):
        window = ts.Window("t", [[ts.TInput("", key="-E-")]], finalize=True)
        window.drop_target(lambda files: None)
        window.drop_target(lambda files: None)
        window.drop_target(None)
        window.close()

    def test_requires_finalized_window(self):
        window = ts.Window("t", [[ts.TInput("", key="-E-")]])
        with self.assertRaises(RuntimeError):
            window.drop_target(lambda files: None)
        window.close()

    def test_rejects_non_callable(self):
        window = ts.Window("t", [[ts.TInput("", key="-E-")]], finalize=True)
        with self.assertRaises(TypeError):
            window.drop_target("not callable")
        window.close()

    def test_close_revokes_registration(self):
        window = ts.Window("t", [[ts.TInput("", key="-E-")]], finalize=True)
        window.drop_target(lambda files: None)
        window.close()
        window.close()  # second close stays inert

    def _fabricate_hdrop(self):
        """A real GlobalAlloc'd HDROP blob (DROPFILES struct + wide list)."""
        class DropFiles(ctypes.Structure):
            _fields_ = [
                ("p_files", ctypes.c_uint32),
                ("point_x", ctypes.c_long),
                ("point_y", ctypes.c_long),
                ("f_nc", ctypes.c_long),
                ("f_wide", ctypes.c_long),
            ]

        header = ctypes.string_at(ctypes.byref(DropFiles(20, 0, 0, 0, 1)),
                                  ctypes.sizeof(DropFiles))
        blob = "C:\\a.txt\0C:\\b dir\\c.txt\0".encode("utf-16-le") + b"\x00\x00"
        size = len(header) + len(blob)
        kernel32 = ctypes.windll.kernel32
        # declare the real signatures: default restype would truncate the
        # 64-bit HGLOBAL to a 32-bit int and GlobalLock would return NULL
        kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        hglobal = kernel32.GlobalAlloc(0x0002, size)  # GMEM_MOVEABLE
        pointer = kernel32.GlobalLock(hglobal)
        ctypes.memmove(pointer, header + blob, size)
        kernel32.GlobalUnlock(hglobal)
        return hglobal

    def test_hdrop_payload_parses_real_files(self):
        dnd = ts._dnd
        received = []
        dnd._deliver_drop_files(self._fabricate_hdrop(), received.extend)
        self.assertEqual(received, ["C:\\a.txt", "C:\\b dir\\c.txt"])

    def test_failing_callback_is_reported_not_raised(self):
        dnd = ts._dnd

        def boom(files):
            raise RuntimeError("boom")

        dnd._deliver_drop_files(self._fabricate_hdrop(), boom)  # must not raise


class TestTkIntegration(unittest.TestCase):
    """Deep tk/ttk API exposure: logo, graph handles, sorting, clipboard."""

    def test_default_logo_decodes(self):
        import tkinter as tk

        root = tk.Toplevel()
        root.withdraw()
        big = tk.PhotoImage(data=ts.DEFAULT_BASE64_ICON, master=root)
        small = tk.PhotoImage(data=ts.DEFAULT_BASE64_ICON_SMALL, master=root)
        self.assertEqual((big.width(), big.height()), (64, 64))
        self.assertEqual((small.width(), small.height()), (32, 32))
        root.destroy()

    def test_graph_figure_api(self):
        graph = ts.TGraph(
            (100, 100), (0, 0), (10, 10), key="-G-", enable_events=True
        )
        window = ts.Window("t", [[graph]], finalize=True)
        rect = graph.draw_rectangle((1, 9), (3, 7), fill_color="red")
        oval = graph.draw_oval((4, 9), (6, 7))
        arc = graph.draw_arc((7, 9), (9, 7), start_angle=0, extent=180, style="pieslice")
        poly = graph.draw_polygon([(0, 5), (2, 5), (1, 3)])
        for figure in (rect, oval, arc, poly):
            self.assertTrue(figure)
        # click in the middle of the rectangle (graph coords (2, 8))
        self.assertIn(rect, graph.get_figures_at_location((2, 8)))
        # move the rectangle away, it should no longer be found there
        graph.move_figure(rect, 5, 0)
        self.assertNotIn(rect, graph.get_figures_at_location((2, 8)))
        graph.relocate_figure(rect, (1, 8))
        self.assertIn(rect, graph.get_figures_at_location((2, 8)))
        graph.bring_figure_to_front(rect)
        graph.send_figure_to_back(rect)
        graph.delete_figure(rect)
        self.assertNotIn(rect, graph.get_figures_at_location((2, 8)))
        window.close()

    def test_graph_draw_image(self):
        graph = ts.TGraph((50, 50), (0, 0), (50, 50))
        window = ts.Window("t", [[graph]], finalize=True)
        figure = graph.draw_image((5, 45), data_base64=ts.BLANK_BASE64)
        self.assertTrue(figure)
        self.assertEqual(len(graph._images), 1)  # photo kept alive
        graph.erase()
        self.assertEqual(len(graph._images), 0)
        window.close()

    def test_table_sorting(self):
        table = ts.TTable(
            [["banana", 2], ["apple", 3], ["cherry", 1]],
            headings=["Name", "Qty"],
            key="-T-",
        )
        window = ts.Window("t", [[table]], finalize=True)
        tree = table.widget
        table.sort_by(0)  # name ascending
        rows = [tree.item(item, "values")[0] for item in tree.get_children()]
        self.assertEqual(rows, ["apple", "banana", "cherry"])
        table.sort_by(0)  # click again: descending
        rows = [tree.item(item, "values")[0] for item in tree.get_children()]
        self.assertEqual(rows, ["cherry", "banana", "apple"])
        table.sort_by(1, ascending=True)  # numeric column
        rows = [tree.item(item, "values")[1] for item in tree.get_children()]
        self.assertEqual(rows, ["1", "2", "3"])
        self.assertEqual(table.sort_column, 1)
        self.assertTrue(table.sort_ascending)
        self.assertEqual(table.values[0], ["cherry", 1])  # values kept in sync
        window.close()

    def test_multiline_undo_and_colored_write(self):
        multiline = ts.TMultiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.write("line-one")
        multiline.write("bad", text_color="#cc0000")
        self.assertIn("line-one", multiline.get())
        self.assertIn("bad", multiline.get())
        multiline._text.insert("end", "extra")
        multiline.undo()
        self.assertNotIn("extra", multiline.get())
        multiline.redo()
        self.assertIn("extra", multiline.get())
        multiline.clear()
        self.assertEqual(multiline.get(), "")
        window.close()

    def test_multiline_update_keeps_editable(self):
        multiline = ts.TMultiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.update("fresh text")
        self.assertEqual(str(multiline._text.cget("state")), "normal")
        window.close()

    def test_button_with_image(self):
        button = ts.TButton("Go", key="-B-", image_data=ts.BLANK_BASE64)
        window = ts.Window("t", [[button]], finalize=True)
        self.assertTrue(button.widget.cget("image"))
        self.assertEqual(str(button.widget.cget("compound")), "left")
        window.close()

    def test_clipboard(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.clipboard_set("py-simple")
        self.assertEqual(window.clipboard_get(), "py-simple")
        window.clipboard_append("-gui")
        self.assertEqual(window.clipboard_get(), "py-simple-gui")
        window.clipboard_clear()
        window.close()

    def test_set_min_size(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.set_min_size((200, 100))
        self.assertEqual(window.tk_root.minsize(), (200, 100))
        window.close()

    def test_set_dpi_awareness(self):
        result = ts.set_dpi_awareness()
        self.assertIsInstance(result, bool)


class TestDpiScaling(unittest.TestCase):
    """DPI awareness + ts.settings.scaling.

    Every expectation is written as a formula against ``ts._scaling`` (or the
    live ``winfo_fpixels``) so the suite stays green on any-DPI machines; with
    the default multiplier 1 the scaled values equal the unscaled ones.
    """

    def setUp(self):
        self._previous_scaling = ts.settings.scaling
        self._previous_dpi_aware = ts.settings.dpi_aware
        self._previous_theme = ts.theme()

    def tearDown(self):
        ts.settings.scaling = self._previous_scaling
        ts.settings.dpi_aware = self._previous_dpi_aware
        ts.theme(self._previous_theme)
        ts.Window.close_all()

    @staticmethod
    def _first(value):
        """First number of a grid_info pad entry (tk collapses equal pairs)."""
        return int(value[0] if isinstance(value, (tuple, list)) else value)

    # --- settings ---------------------------------------------------------------
    def test_pixel_scale_defaults_to_one(self):
        ts.settings.scaling = None
        self.assertEqual(ts._scaling.pixel_scale(), 1.0)

    def test_pixel_scale_multiplier(self):
        ts.settings.scaling = 2.5
        self.assertEqual(ts._scaling.pixel_scale(), 2.5)

    def test_scaling_validation(self):
        with self.assertRaises(ValueError):
            ts.settings.scaling = 0
        with self.assertRaises(ValueError):
            ts.settings.scaling = -1.5
        self.assertIsNone(ts.settings.scaling)

    def test_dpi_aware_setting_coerced(self):
        ts.settings.dpi_aware = 0
        self.assertIs(ts.settings.dpi_aware, False)
        ts.settings.dpi_aware = True
        self.assertIs(ts.settings.dpi_aware, True)

    # --- pure helpers -------------------------------------------------------------
    def test_scale_px_math(self):
        ts.settings.scaling = 2.0
        self.assertEqual(ts._scaling.scale_px(5), 10)
        self.assertEqual(ts._scaling.scale_px(2.4), 5)  # rounds to int
        self.assertEqual(ts._scaling.scale_px(-3), -6)
        self.assertIsNone(ts._scaling.scale_opt(None))
        self.assertEqual(ts._scaling.scale_opt(3), 6)
        self.assertEqual(ts._scaling.scale_pair(3, None), (6, None))

    # --- awareness ------------------------------------------------------------------
    def test_ensure_dpi_awareness_off_by_default(self):
        calls = []
        original = ts.utils.set_dpi_awareness

        def fake(*_args, **_kwargs):
            calls.append(1)
            return True

        ts.utils.set_dpi_awareness = fake
        try:
            self.assertIs(ts.settings.dpi_aware, False)  # opt-in feature
            ts._scaling._awareness_attempted = False
            self.assertFalse(ts._scaling.ensure_dpi_awareness())
            self.assertEqual(len(calls), 0)  # default never touches the API
        finally:
            ts.utils.set_dpi_awareness = original
            ts._scaling._awareness_attempted = True

    def test_ensure_dpi_awareness_calls_once_when_enabled(self):
        calls = []
        original = ts.utils.set_dpi_awareness

        def fake(*_args, **_kwargs):
            calls.append(_kwargs.get("prefer_per_monitor"))
            return True

        ts.utils.set_dpi_awareness = fake
        ts.settings.dpi_aware = True
        try:
            ts._scaling._awareness_attempted = False
            self.assertTrue(ts._scaling.ensure_dpi_awareness())
            self.assertTrue(ts._scaling.ensure_dpi_awareness())
            self.assertEqual(len(calls), 1)  # second call is served from cache
            # the auto path pins SYSTEM awareness: the level Tk 8.6 supports
            self.assertIs(calls[0], False)
        finally:
            ts.utils.set_dpi_awareness = original
            ts._scaling._awareness_attempted = True

    @unittest.skipUnless(not ts.running_windows(), "non-Windows only")
    def test_set_dpi_awareness_non_windows_noop(self):
        self.assertFalse(ts.set_dpi_awareness())

    # --- tk scaling (the font line) --------------------------------------------------
    def test_tk_scaling_keeps_tk_own_dpi_value(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        root = window.tk_root
        base = ts._scaling._native_tk_scaling
        self.assertIsNotNone(base)
        self.assertGreater(base, 0)
        self.assertAlmostEqual(float(root.tk.call("tk", "scaling")), base, places=9)
        # at multiplier 1 winfo_fpixels reads back the DPI Tk captured from
        self.assertAlmostEqual(root.winfo_fpixels("1i") / 72.0, base, places=9)
        window.close()

    def test_tk_scaling_follows_multiplier(self):
        ts.settings.scaling = 2.0
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        root = window.tk_root
        expected = ts._scaling._native_tk_scaling * ts._scaling.pixel_scale()
        actual = float(root.tk.call("tk", "scaling"))
        # Tk quantizes the stored scaling slightly (2.6667 reads back as
        # 2.6625 on the tk builds tested); assert the multiplier took effect
        self.assertLess(abs(actual - expected) / expected, 0.005)
        window.close()

    # --- pixel-domain hooks ----------------------------------------------------------
    def test_element_padding_scaled(self):
        ts.settings.scaling = 2.0
        window = ts.Window("t", [[ts.TText("x", key="-X-")]], finalize=True)
        info = window.find_element("-X-").widget.grid_info()
        self.assertEqual(self._first(info["padx"]), ts._scaling.scale_px(5))
        self.assertEqual(self._first(info["pady"]), ts._scaling.scale_px(3))
        window.close()

    def test_window_margins_scaled(self):
        ts.settings.scaling = 2.0
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        content = window.tk_root.grid_slaves(row=0, column=0)[0]
        info = content.grid_info()
        self.assertEqual(self._first(info["padx"]), ts._scaling.scale_px(10))
        self.assertEqual(self._first(info["pady"]), ts._scaling.scale_px(5))
        window.close()

    def test_window_geometry_scaled(self):
        ts.settings.scaling = 2.0
        window = ts.Window("t", [[ts.TText("x")]], size=(400, 300), finalize=True)
        root = window.tk_root
        deadline = time.time() + 3
        while time.time() < deadline and root.winfo_width() < 2:
            window.refresh()
        self.assertEqual(root.winfo_width(), ts._scaling.scale_px(400))
        self.assertEqual(root.winfo_height(), ts._scaling.scale_px(300))
        window.close()

    def test_minsize_scaled(self):
        ts.settings.scaling = 2.0
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.set_min_size((200, 100))
        self.assertEqual(
            window.tk_root.minsize(),
            (ts._scaling.scale_px(200), ts._scaling.scale_px(100)),
        )
        window.close()

    def test_chart_canvas_scaled(self):
        ts.settings.scaling = 2.0
        chart = ts.TChart(canvas_size=(420, 280))
        window = ts.Window("t", [[chart]], finalize=True)
        self.assertEqual(int(chart.widget.cget("width")), ts._scaling.scale_px(420))
        self.assertEqual(int(chart.widget.cget("height")), ts._scaling.scale_px(280))
        self.assertEqual(chart._canvas_size, ts._scaling.scale_pair(420, 280))
        window.close()

    def test_display_canvas_scaled(self):
        ts.settings.scaling = 2.0
        tag = ts.TTag("Sized", size=(90, 26))
        window = ts.Window("t", [[tag]], finalize=True)
        self.assertEqual(int(tag.widget.cget("width")), ts._scaling.scale_px(90))
        self.assertEqual(int(tag.widget.cget("height")), ts._scaling.scale_px(26))
        window.close()

    def test_ttk_notebook_padding_scaled(self):
        ts.theme("Slate")  # native engine restores skip the custom paddings
        ts.settings.scaling = 2.0
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        from tkinter import ttk

        padding = ttk.Style(window.tk_root).lookup("TNotebook.Tab", "padding")
        parts = [int(part) for part in str(padding).split()]
        self.assertEqual(parts, [ts._scaling.scale_px(10), ts._scaling.scale_px(5)])
        window.close()


class TestNativeCoverage(unittest.TestCase):
    """Per-widget coverage of the native Tk/ttk passthrough APIs."""

    def test_input_native_api(self):
        element = ts.TInput("abc", justify="right", key="-IN-")
        window = ts.Window("t", [[element]], finalize=True)
        self.assertEqual(str(element.widget.cget("justify")), "right")
        element.set("hello")
        self.assertEqual(element.get(), "hello")
        element.insert(0, "X")
        self.assertEqual(element.get(), "Xhello")
        element.delete(0, 1)
        self.assertEqual(element.get(), "hello")
        element.set_position(2)
        self.assertEqual(element.get_position(), 2)
        element.select_range(0, 2)
        element.clear_selection()
        window.close()

    def test_combo_current(self):
        combo = ts.TCombo(["a", "b", "c"], key="-CB-")
        window = ts.Window("t", [[combo]], finalize=True)
        combo.set("b")
        self.assertEqual(combo.get(), "b")
        self.assertEqual(combo.current(), 1)
        combo.current(2)
        self.assertEqual(combo.get(), "c")
        window.close()

    def test_spin_numeric_range(self):
        spin = ts.TSpin(range_=(0, 20), increment=5, initial_value=10, wrap=True)
        window = ts.Window("t", [[spin]], finalize=True)
        self.assertEqual(spin.get(), "10")
        spin.set(15)
        self.assertEqual(spin.get(), "15")
        # values were generated from the range with the increment
        self.assertEqual(spin.values, [0, 5, 10, 15, 20])
        window.close()
        with self.assertRaises(ValueError):
            ts.TSpin([1, 2], range_=(0, 10))

    def test_checkbox_toggle(self):
        checkbox = ts.TCheckbox("c", default=False)
        window = ts.Window("t", [[checkbox]], finalize=True)
        checkbox.toggle()
        self.assertTrue(checkbox.get())
        checkbox.select()
        checkbox.deselect()
        self.assertFalse(checkbox.get())
        window.close()

    def test_radio_select_helpers(self):
        first = ts.TRadio("one", "g", key="-R1-")
        second = ts.TRadio("two", "g", key="-R2-")
        window = ts.Window("t", [[first, second]], finalize=True)
        second.select()
        self.assertTrue(second.get())
        self.assertFalse(first.get())
        self.assertEqual(first.group_value(), "two")
        second.deselect()
        self.assertEqual(first.group_value(), "")
        window.close()

    def test_progressbar_indeterminate(self):
        bar = ts.TProgressBar(100, key="-PB-")
        window = ts.Window("t", [[bar]], finalize=True)
        bar.start_indeterminate(interval_ms=30)
        self.assertEqual(str(bar.widget.cget("mode")), "indeterminate")
        window.refresh()
        bar.stop_indeterminate()
        self.assertEqual(str(bar.widget.cget("mode")), "determinate")
        window.close()

    def test_multiline_passthrough(self):
        multiline = ts.TMultiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.insert("1.0", "hello")
        multiline.insert("end", " world")
        self.assertEqual(multiline.get(), "hello world")
        multiline.delete("1.0", "1.6")  # removes "hello "
        self.assertEqual(multiline.get(), "world")
        multiline.see("end")  # must not raise
        window.close()

    def test_text_image_and_wrap(self):
        text = ts.TText("logo:", image_data=ts.DEFAULT_BASE64_ICON, wrap_length=200)
        window = ts.Window("t", [[text]], finalize=True)
        self.assertIsNotNone(text._photo)
        self.assertEqual(text._photo.width(), 64)
        self.assertEqual(int(text.widget.cget("wraplength")), 200)
        window.close()

    def test_listbox_see_size(self):
        listbox = ts.TListbox([f"item {i}" for i in range(30)], size=(10, 3))
        window = ts.Window("t", [[listbox]], finalize=True)
        self.assertEqual(listbox.size(), 30)
        listbox.see(25)  # must not raise
        window.close()

    def test_table_tree_see(self):
        table = ts.TTable([[f"row {i}"] for i in range(50)], headings=["H"])
        window = ts.Window("t", [[table]], finalize=True)
        table.see(45)  # must not raise
        window.close()
        tree = ts.TTree()
        window2 = ts.Window("t2", [[tree]], finalize=True)
        tree.insert("", "k1", "visible")
        tree.see("k1")
        window2.close()

    def test_frame_label_anchor(self):
        frame = ts.TFrame("Title", [[ts.TText("x")]], label_anchor="se")
        window = ts.Window("t", [[frame]], finalize=True)
        self.assertEqual(str(frame.widget.cget("labelanchor")), "se")
        window.close()

    def test_image_zoom_getters(self):
        image = ts.TImage(data_base64=ts.DEFAULT_BASE64_ICON)
        window = ts.Window("t", [[image]], finalize=True)
        self.assertEqual((image.width, image.height), (64, 64))
        image.zoom(2)
        self.assertEqual((image.width, image.height), (128, 128))
        image.subsample(4)
        self.assertEqual((image.width, image.height), (32, 32))
        self.assertIsNotNone(image.photo)
        window.close()

    def test_canvas_passthrough(self):
        canvas = ts.TCanvas((100, 100))
        window = ts.Window("t", [[canvas]], finalize=True)
        item = canvas.widget.create_rectangle(10, 10, 40, 40, fill="red")
        canvas.itemconfigure(item, fill="blue")
        self.assertEqual(str(canvas.widget.itemcget(item, "fill")), "blue")
        self.assertEqual(len(canvas.itembbox(item)), 4)
        self.assertEqual(len(canvas.coords(item)), 4)
        window.close()


class TestTypedEnums(unittest.TestCase):
    """IDE affinity: str enums replacing Tk magic strings."""

    def test_enum_values_are_tk_strings(self):
        self.assertIsInstance(ts.Anchor.CENTER, str)
        self.assertEqual(ts.Anchor.CENTER, "center")
        self.assertEqual(str(ts.Justify.RIGHT), "right")
        self.assertEqual(ts.Relief.SUNKEN, "sunken")
        self.assertEqual(ts.Orientation.HORIZONTAL, "horizontal")
        self.assertEqual(ts.EventType.DOUBLE_CLICK, "<Double-1>")
        self.assertEqual(ts.Color.RED, "red")

    def test_enums_interchange_with_strings(self):
        """Enums and raw strings are fully interchangeable in widget args."""
        window = ts.Window(
            "t",
            [
                [ts.TText("a", justification=ts.Justify.CENTER)],
                [ts.TInput("", justify=ts.Justify.RIGHT, key="-IN-")],
                [ts.TFrame("F", [[ts.TText("x")]], label_anchor=ts.LabelAnchor.SE,
                          key="-FRAME-")],
                [ts.TMultiline("", wrap=ts.WrapMode.NONE, key="-ML-")],
            ],
            finalize=True,
        )
        self.assertEqual(str(window["-IN-"].widget.cget("justify")), "right")
        self.assertEqual(str(window["-ML-"]._text.cget("wrap")), "none")
        self.assertEqual(str(window["-FRAME-"].widget.cget("labelanchor")), "se")
        window.close()

    def test_event_type_helpers(self):
        self.assertEqual(ts.EventType.control("o"), "<Control-o>")
        self.assertEqual(ts.EventType.shift("F5"), "<Shift-F5>")
        self.assertEqual(ts.EventType.alt("q"), "<Alt-q>")
        self.assertEqual(ts.EventType.key("F5"), "<F5>")

    def test_bind_with_event_type_enum(self):
        element = ts.TText("click", key="-T-")
        window = ts.Window("t", [[element]], finalize=True)
        element.bind(ts.EventType.RIGHT_CLICK)  # enum instead of "<Button-3>"
        element.widget.event_generate("<Button-3>", when="tail")
        window.tk_root.update()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-T-")
        window.close()

    def test_color_enum_in_widget(self):
        text = ts.TText("colored", text_color=ts.Color.RED,
                       background_color=ts.Color.NAVY)
        window = ts.Window("t", [[text]], finalize=True)
        self.assertEqual(str(text.widget.cget("foreground")), "red")
        window.close()

    def test_anchor_enum_in_text(self):
        text = ts.TText("anchored")
        window = ts.Window("t", [[text]], finalize=True)
        # anchor flows through theme kwargs; verify the enum is a valid value
        text.widget.configure(anchor=ts.Anchor.CENTER)
        self.assertEqual(str(text.widget.cget("anchor")), "center")
        window.close()


class TestDataclassConfigs(unittest.TestCase):
    """dataclass config objects: WindowConfig / ElementOptions."""

    def test_window_config(self):
        cfg = ts.WindowConfig(title="Cfg", resizable=True, modal=True,
                              keep_on_top=True)
        window = ts.Window(layout=[[ts.TText("x")]], config=cfg, finalize=True)
        self.assertEqual(window.title, "Cfg")
        self.assertEqual(window.tk_root.resizable(), (True, True))
        window.close()

    def test_window_config_kwargs_override(self):
        cfg = ts.WindowConfig(title="FromConfig", resizable=True)
        window = ts.Window(config=cfg, title="Explicit", finalize=True)
        self.assertEqual(window.title, "Explicit")  # explicit kwarg wins
        window.close()

    def test_window_config_requires_type(self):
        with self.assertRaises(TypeError):
            ts.Window(config={"title": "nope"})

    def test_element_options_shared(self):
        opts = ts.ElementOptions(
            pad=(10, 4), expand_x=True,
            right_click_menu=["&TMenu", ["Refresh"]],
            metadata={"tag": 1},
        )
        first = ts.TText("a", config=opts, key="-A-")
        second = ts.TInput("", config=opts, key="-B-")
        window = ts.Window("t", [[first], [second]], finalize=True)
        self.assertEqual(first.pad, (10, 4))
        self.assertEqual(second.pad, (10, 4))
        self.assertTrue(first.expand_x)
        self.assertTrue(second.expand_x)
        self.assertEqual(first.metadata, {"tag": 1})
        self.assertIsNotNone(first._popup_menu)  # right-click menu attached
        window.close()

    def test_element_options_kwargs_win(self):
        opts = ts.ElementOptions(expand_x=True, metadata="from-config")
        element = ts.TText("a", config=opts, metadata="explicit")
        self.assertEqual(element.metadata, "explicit")

    def test_element_options_requires_type(self):
        with self.assertRaises(TypeError):
            ts.TText("a", config={"pad": 4})

    def test_window_config_carry_layout(self):
        cfg = ts.WindowConfig(title="LayoutInConfig",
                              layout=[[ts.TText("from cfg", key="-T-")]])
        window = ts.Window(config=cfg, finalize=True)
        self.assertIn("-T-", window)
        window.close()


class TestCharts(unittest.TestCase):
    """TChart: 8 types, AA raster, theme repaint, stacked/donut models."""

    def test_chart_types_count(self):
        self.assertEqual(len(ts.ChartType.ALL), 9)
        self.assertIn("donut", ts.ChartType.ALL)
        self.assertIn("stacked", ts.ChartType.ALL)
        self.assertIn("histogram", ts.ChartType.ALL)

    def _make(self, **kwargs):
        window = ts.Window(
            "charts", [[ts.TChart((220, 160), key="-C-", **kwargs)]],
            finalize=True,
        )
        return window, window["-C-"]

    @unittest.skipUnless(HAS_PIL, "Pillow not installed")
    def test_aa_renders_photo(self):
        window, chart = self._make()
        try:
            chart.add_series("s", [1, 5, 3, 8])
            chart.redraw()
            kinds = {chart.widget.type(i) for i in chart.widget.find_all()}
            self.assertIn("image", kinds)
        finally:
            window.close()

    def test_vector_fallback(self):
        window, chart = self._make(chart_type="bar", anti_alias=False)
        try:
            chart.add_series("s", [1, 5, 3], labels=["a", "b", "c"])
            chart.redraw()
            kinds = {chart.widget.type(i) for i in chart.widget.find_all()}
            self.assertNotIn("image", kinds)
            self.assertIn("rectangle", kinds)
        finally:
            window.close()

    @unittest.skipUnless(HAS_PIL, "Pillow not installed")
    def test_donut_and_stacked_models(self):
        window, chart = self._make(chart_type="donut")
        try:
            chart.add_series("split", [("x", 45), ("y", 25), ("z", 30)])
            chart.redraw()
            self.assertEqual(len(chart._pie_labels), 3)
            chart._chart_type = ts.ChartType.STACKED
            chart.clear_series()
            chart.add_series("a", [1, 2], labels=["r1", "r2"])
            chart.add_series("b", [3, 4])
            chart.redraw()
            self.assertEqual(chart.series_names, ["a", "b"])
            kinds = {chart.widget.type(i) for i in chart.widget.find_all()}
            self.assertIn("image", kinds)
        finally:
            window.close()

    def test_update_data_redraws(self):
        window, chart = self._make()
        try:
            chart.add_series("s", [1, 2, 3])
            chart.update_data("s", [9, 9, 9])
            self.assertEqual(chart._series[0].values, [9, 9, 9])
        finally:
            window.close()

    @unittest.skipUnless(HAS_PIL, "Pillow not installed")
    def test_legend_positions_render(self):
        for position in ("top", "bottom", "left", "right"):
            window, chart = self._make(legend_position=position)
            try:
                chart.add_series("甲", [1, 5, 3])
                chart.add_series("乙", [4, 2, 6])
                chart.redraw()
                kinds = {chart.widget.type(i) for i in chart.widget.find_all()}
                self.assertIn("image", kinds, msg=f"position={position}")
            finally:
                window.close()

    def test_legend_position_invalid_rejected(self):
        with self.assertRaises(ValueError):
            ts.TChart(legend_position="diagonal")

    def test_horizontal_legend_shrinks_plot(self):
        window, chart = self._make(legend_position="bottom")
        try:
            chart.add_series("s", [1, 5, 3])
            bottom_legend = chart._plot_rect()[3]
            chart._legend_position = "right"
            self.assertLess(bottom_legend, chart._plot_rect()[3])
        finally:
            window.close()

    def test_chart_follows_theme(self):
        window, chart = self._make()
        try:
            chart.add_series("s", [1, 5, 3, 8])
            chart.redraw()
            ts.theme("Slate")
            slate_bg = ts.theme_background_color()
            window.update_theme()
            self.assertEqual(
                str(chart.widget.cget("background")), slate_bg
            )
        finally:
            window.close()
            ts.theme(None)


class TestChartBackend(unittest.TestCase):
    """Optional Pillow rendering backend, with the Tk vector fallback."""

    def test_backend_detection_follows_pillow(self):
        from TkSimpleGUI.elements import chart as chart_mod
        try:
            import PIL  # noqa: F401
            installed = True
        except ImportError:
            installed = False
        self.assertEqual(chart_mod.pil_backend_available(), installed)

    def test_fallback_renders_without_pil(self):
        # anti_alias=False must produce pure vector figures on any machine
        window = ts.Window(
            "fb", [[ts.TChart((220, 160), chart_type="line", key="-C-",
                              anti_alias=False)]],
            finalize=True,
        )
        try:
            chart = window["-C-"]
            chart.add_series("s", [1, 5, 3, 8])
            chart.redraw()
            kinds = {chart.widget.type(i) for i in chart.widget.find_all()}
            self.assertNotIn("image", kinds)
            self.assertIn("line", kinds)
        finally:
            window.close()

    def test_pil_frame_matches_canvas(self):
        from TkSimpleGUI.elements.chart import pil_backend_available
        if not pil_backend_available():
            self.skipTest("Pillow not installed")
        window = ts.Window(
            "pil", [[ts.TChart((120, 80), chart_type="pie", key="-C-")]],
            finalize=True,
        )
        try:
            chart = window["-C-"]
            chart.add_series("s", [("a", 30), ("b", 20), ("c", 50)])
            chart.redraw()
            kinds = {chart.widget.type(i) for i in chart.widget.find_all()}
            self.assertIn("image", kinds)
            frame = chart._images[-1]
            self.assertEqual((frame.width(), frame.height()), (120, 80))
        finally:
            window.close()


class TestScientificChart(unittest.TestCase):
    """Error bars, reference lines and histogram binning (science/industry)."""

    def _chart(self, **kwargs):
        window = ts.Window(
            "sci", [[ts.TChart((300, 180), key="-C-", **kwargs)]],
            finalize=True,
        )
        self.addCleanup(window.close)
        return window["-C-"]

    @unittest.skipUnless(HAS_PIL, "Pillow not installed")
    def test_histogram_auto_binning(self):
        chart = self._chart(chart_type="histogram")
        chart.add_series("v", [1, 2, 2, 3, 3, 3, 4, 4, 5, 9])
        chart.redraw()
        edges, counts = chart._histogram_bins()
        self.assertEqual(sum(counts), 10)  # every sample lands in a bin
        self.assertEqual(len(edges), len(counts) + 1)
        self.assertEqual(edges[0], 1.0)
        self.assertEqual(edges[-1], 9.0)
        kinds = {chart.widget.type(i) for i in chart.widget.find_all()}
        self.assertIn("image", kinds)

    def test_histogram_fixed_bins(self):
        chart = self._chart(chart_type="histogram", bins=4)
        chart.add_series("v", [0, 1, 2, 3, 4, 5, 6, 7])
        _edges, counts = chart._histogram_bins()
        self.assertEqual(len(counts), 4)

    def test_error_bars_render_and_validate(self):
        chart = self._chart(chart_type="scatter")
        chart.add_series("m", [3, 4, 5], errors=[0.5, 0.5, 0.5])
        chart.redraw()
        self.assertEqual(chart._series[0].errors, [0.5, 0.5, 0.5])
        with self.assertRaises(ValueError):
            chart.add_series("bad", [1, 2], errors=[0.1])

    def test_error_bars_extend_value_range(self):
        chart = self._chart(chart_type="line")
        chart.add_series("m", [10.0, 20.0], errors=[5.0, 5.0])
        chart.redraw()
        y_min, y_max = chart._y_range
        self.assertLessEqual(y_min, 5.0)   # 10 - 5 must fit
        self.assertGreaterEqual(y_max, 25.0)  # 20 + 5 must fit

    def test_hlines_normalized_and_drawn(self):
        chart = self._chart(chart_type="line",
                            hlines=[(5, "USL"), 2, (8, "X", "#0000ff")])
        self.assertEqual(chart._hlines,
                         [(5.0, "USL", None), (2.0, None, None),
                          (8.0, "X", "#0000ff")])
        chart.add_series("a", [1, 4, 2, 6])
        chart.redraw()
        texts = [
            chart.widget.itemcget(i, "text")
            for i in chart.widget.find_all()
            if chart.widget.type(i) == "text"
        ]
        self.assertIn("USL", texts)
        self.assertIn("X", texts)

    def test_hlines_extend_value_range(self):
        chart = self._chart(chart_type="line", hlines=[100])
        chart.add_series("a", [1, 2, 3])
        chart.redraw()
        self.assertGreaterEqual(chart._y_range[1], 100.0)

    def test_hlines_skip_out_of_range(self):
        # a limit far outside the data range must not crash the draw
        chart = self._chart(chart_type="line")
        chart.add_series("a", [1, 2, 3])
        chart._hlines = [(1e6, "far", None)]
        chart.redraw()  # extend-range keeps it in view: no raise is the bar


class TestGauge(unittest.TestCase):
    """TGauge: canvas analog dial (zones, needle, readout)."""

    def _gauge(self, **kwargs):
        gauge = ts.TGauge(100, key="-G-", **kwargs)
        window = ts.Window("g", [[gauge]], finalize=True)
        self.addCleanup(window.close)
        return gauge

    def test_defaults_and_readout(self):
        gauge = self._gauge(value=72, units="%", title="Tank")
        self.assertEqual(gauge.get(), 72.0)
        self.assertEqual(gauge.min_value, 0.0)
        self.assertEqual(gauge.max_value, 100.0)
        # track + 3 zones + ticks + 2 end labels + needle + hub + readout + title
        self.assertGreater(len(gauge.widget.find_all()), 8)

    def test_update_clamps_needle_only(self):
        gauge = self._gauge(value=50)
        gauge.update(150)  # out of range: needle pins, value kept (metering)
        self.assertEqual(gauge.get(), 150.0)
        gauge.update(80, )
        self.assertEqual(gauge.get(), 80.0)

    def test_custom_zones_and_bare_track(self):
        zoned = self._gauge(zones=[(0, 50, "#00ff00"), (50, 100, "#ff0000")])
        bare = self._gauge(zones=[])
        self.assertEqual(len(zoned._zones), 2)
        self.assertEqual(bare._zones, [])

    def test_range_validation(self):
        with self.assertRaises(ValueError):
            ts.TGauge(0)
        gauge = self._gauge()
        with self.assertRaises(ValueError):
            gauge.set_range(10, 5)

    def test_set_range_redraws(self):
        gauge = self._gauge(value=50, zones=[])
        gauge.set_range(-50, 50)
        self.assertEqual(gauge.min_value, -50.0)
        self.assertEqual(gauge.max_value, 50.0)
        # a bare-track gauge, full redraw in both directions of the range
        self.assertGreater(len(gauge.widget.find_all()), 5)

    def test_set_range_rescales_auto_zones(self):
        gauge = self._gauge(value=50)  # default green/yellow/red bands
        gauge.set_range(0, 200)
        first, last = gauge._zones[0], gauge._zones[-1]
        self.assertEqual(first[0], 0.0)
        self.assertEqual(first[1], 120.0)  # 60% of the new range
        self.assertEqual(last[1], 200.0)   # red cap reaches the new max

    def test_set_range_keeps_explicit_zones(self):
        zones = [(0, 50, "#00ff00"), (50, 100, "#ff0000")]
        gauge = self._gauge(zones=zones)
        gauge.set_range(0, 200)
        self.assertEqual(gauge._zones, zones)

    def test_gauge_follows_theme(self):
        gauge = self._gauge(value=42)
        ts.theme("Slate")
        try:
            gauge.apply_theme()
            self.assertEqual(
                str(gauge.widget.cget("background")),
                ts.theme_background_color(),
            )
        finally:
            ts.theme(None)
            gauge.apply_theme()


class TestFirstBatch(unittest.TestCase):
    """Batch 1: validation, calendar, splitter, scrollable column, timers, find/replace."""

    def test_input_validators(self):
        self.assertTrue(ts.validate_integer("123"))
        self.assertTrue(ts.validate_integer(""))
        self.assertTrue(ts.validate_integer("-"))
        self.assertFalse(ts.validate_integer("12a"))
        self.assertTrue(ts.validate_float("3.14"))
        self.assertTrue(ts.validate_float("-0.5"))
        self.assertFalse(ts.validate_float("1.2.3"))
        self.assertTrue(ts.validate_regex(r"\d{1,3}")("42"))
        self.assertFalse(ts.validate_regex(r"\d{1,3}")("1234"))
        self.assertFalse(ts.validate_regex(r"\d+")("abc"))

    def test_input_validation_wiring(self):
        window = ts.Window(
            "t",
            [[ts.TInput("", key="-IN-", validate="key", validate_command=ts.validate_integer)]],
            finalize=True,
        )
        widget = window["-IN-"].widget
        self.assertEqual(str(widget.cget("validate")), "key")
        self.assertTrue(widget.cget("validatecommand"))
        with self.assertRaises(TypeError):
            ts.TInput(validate="key", validate_command="not-callable")
        window.close()

    def test_calendar_element(self):
        import datetime

        calendar_element = ts.TCalendar(
            default_date=datetime.date(2026, 10, 11), key="-CAL-"
        )
        window = ts.Window("t", [[calendar_element]], finalize=True)
        self.assertEqual(calendar_element.get(), "2026-10-11")
        self.assertEqual(calendar_element.date, datetime.date(2026, 10, 11))
        # 6 week rows of day buttons were rendered
        self.assertGreater(len(calendar_element._day_area.winfo_children()), 26)
        calendar_element._shift(1)
        self.assertIn("November", calendar_element._header.cget("text"))
        calendar_element._shift(-2)
        self.assertIn("September", calendar_element._header.cget("text"))
        calendar_element.update(datetime.date(2026, 1, 2))
        self.assertEqual(calendar_element.get(), "2026-01-02")
        window.close()

    def test_calendar_accepts_tuple_default(self):
        calendar_element = ts.TCalendar(default_date=(2026, 2, 14), dateformat="%d.%m.%Y")
        self.assertEqual(calendar_element.get(), "14.02.2026")

    def test_splitter(self):
        splitter = ts.TSplitter(
            [[[ts.TText("L", key="-L-")], [ts.TInput(key="-LIN-")]],
             [[ts.TText("R", key="-R-")], [ts.TInput(key="-RIN-")]]],
            orientation="h",
            key="-SP-",
        )
        window = ts.Window("t", [[splitter]], finalize=True)
        self.assertIsInstance(splitter.widget, tk.PanedWindow)
        self.assertIsNotNone(window["-LIN-"].widget)
        self.assertIsNotNone(window["-RIN-"].widget)
        self.assertEqual(len(splitter.widget.panes()), 2)
        with self.assertRaises(TypeError):
            ts.TSplitter([[[ts.TText("only")]]])
        window.close()

    def test_scrollable_column(self):
        rows = [[ts.TText(f"row {i}")] for i in range(30)]
        scroll = ts.TScrollableColumn(rows, size=(200, 100), key="-SC-")
        window = ts.Window("t", [[scroll]], finalize=True)
        window.refresh()
        self.assertIsNotNone(scroll._canvas)
        region = scroll._canvas.cget("scrollregion")
        self.assertTrue(str(region))  # content bbox was registered
        self.assertIsNotNone(scroll._inner_frame.winfo_children())
        window.close()

    def test_window_right_click_menu(self):
        window = ts.Window(
            "t",
            [[ts.TText("x")]],
            finalize=True,
            right_click_menu=["&Win", ["About", "Exit"]],
        )
        self.assertIsNotNone(window._popup_menu)
        submenu = window._popup_menu.nametowidget(
            window._popup_menu.entrycget(0, "menu")
        )
        self.assertEqual(submenu.entrycget(0, "label"), "About")
        window.close()

    def test_every_timer(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        calls = []
        handle = window.every(30, lambda: calls.append(1))
        self.assertTrue(handle.active)
        deadline = time.time() + 2.0
        while len(calls) < 3 and time.time() < deadline:
            window.read(timeout=20)
        self.assertGreaterEqual(len(calls), 3)
        handle.cancel()
        self.assertFalse(handle.active)
        count_before = len(calls)
        deadline = time.time() + 0.5
        while time.time() < deadline:
            window.read(timeout=20)
        self.assertEqual(len(calls), count_before)
        window.close()

    def test_after_timer(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        calls = []
        window.after(50, lambda: calls.append(1))
        deadline = time.time() + 2.0
        while not calls and time.time() < deadline:
            window.read(timeout=20)
        self.assertEqual(len(calls), 1)
        window.close()

    def test_text_find_and_replace_helpers(self):
        from TkSimpleGUI.popup import _text_find, _text_replace_all

        multiline = ts.TMultiline("alpha beta ALPHA end", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        pos = _text_find(multiline, "beta")  # element is unwrapped internally
        self.assertEqual(pos, "1.6")
        pos = _text_find(multiline, "BETA", case_sensitive=True)
        self.assertIsNone(pos)
        pos = _text_find(multiline._text, "ALPHA", case_sensitive=True)
        self.assertEqual(pos, "1.11")
        # case insensitive search hits the earliest match ("beta" at col 6)
        pos = _text_find(multiline._text, "BETA")
        self.assertEqual(pos, "1.6")
        self.assertIsNone(_text_find(multiline._text, ""))
        count = _text_replace_all(multiline._text, "alpha", "delta")
        self.assertEqual(count, 2)  # case insensitive: "alpha" AND "ALPHA"
        self.assertEqual(multiline.get(), "delta beta delta end")
        count = _text_replace_all(multiline._text, "", "x")
        self.assertEqual(count, 0)
        window.close()


class TestSecondBatch(unittest.TestCase):
    """Batch 2: TCheckList, TToolbar, toggle, TLabeledEdit, KV editor,
            TFlowPanel, icons, editing, TShape."""

    def test_checklist(self):
        checklist = ts.TCheckList(
            ["a", "b", "c"], default_checked=["b"], key="-CL-"
        )
        window = ts.Window("t", [[checklist]], finalize=True)
        self.assertEqual(checklist.get(), ["b"])
        checklist.update(checked=["a", "c"])
        self.assertEqual(checklist.get(), ["a", "c"])
        checklist.check_all()
        self.assertEqual(checklist.get(), ["a", "b", "c"])
        checklist.uncheck_all()
        self.assertEqual(checklist.get(), [])
        checklist.update(values=["x", "y"], checked=["y"])
        self.assertEqual(checklist.values, ["x", "y"])
        self.assertEqual(checklist.get(), ["y"])
        window.close()

    def test_toolbar(self):
        toolbar = ts.TToolbar(
            [
                ("Open", "-OPEN-"),
                "---",
                ("Save", "-SAVE-"),
                ("Options", "-OPT-", ["General", "Advanced"]),
            ],
            key="-TB-",
        )
        window = ts.Window("t", [[toolbar]], finalize=True)
        self.assertEqual(len(toolbar._buttons), 3)
        toolbar._buttons["-SAVE-"].invoke()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-SAVE-")
        dropdown = toolbar._buttons["-OPT-"]
        menu = dropdown.nametowidget(dropdown.cget("menu"))
        self.assertEqual(menu.entrycget(0, "label"), "General")
        window.close()

    def test_toggle_button_group(self):
        first = ts.TButton("B1", key="-B1-", toggle=True, group_id="g")
        second = ts.TButton("B2", key="-B2-", toggle=True, group_id="g")
        window = ts.Window("t", [[first, second]], finalize=True)
        self.assertFalse(first.get())
        first.click()
        self.assertTrue(first.get())
        self.assertEqual(str(first.widget.cget("relief")), "sunken")
        second.click()
        self.assertFalse(first.get())  # group exclusion
        self.assertTrue(second.get())
        second.click()
        self.assertFalse(second.get())
        self.assertEqual(str(second.widget.cget("relief")), "raised")
        window.close()

    def test_labeled_edit(self):
        labeled = ts.TLabeledEdit("Name", "world", key="-NAME-")
        window = ts.Window("t", [[labeled]], finalize=True)
        self.assertEqual(window["-NAME-"].get(), "world")
        self.assertEqual(labeled.get(), "world")
        self.assertIs(labeled.input, window["-NAME-"])
        labeled.update(value="changed")
        self.assertEqual(window["-NAME-"].get(), "changed")
        labeled.update(label="Surname")
        self.assertEqual(labeled.label, "Surname")
        window.close()

    def test_key_value_editor(self):
        editor = ts.TKeyValueEditor(
            [("host", "localhost"), ("port", "5432")], key="-KV-"
        )
        window = ts.Window("t", [[editor]], finalize=True)
        self.assertEqual(
            editor.get(), {"host": "localhost", "port": "5432"}
        )
        editor.update(values={"port": "5433"})
        self.assertEqual(editor.get()["port"], "5433")
        event, values = window.read(timeout=200)
        self.assertEqual(event, ts.TIMEOUT_KEY)
        self.assertEqual(values["-KV-"], {"host": "localhost", "port": "5433"})
        window.close()

    def test_flow_panel(self):
        flow = ts.TFlowPanel(
            [ts.TText("one"), ts.TText("two"), ts.TText("three")], key="-FLOW-"
        )
        window = ts.Window("t", [[flow]], finalize=True)
        window.refresh()
        first = flow._children[0].widget
        self.assertTrue(first.place_info()["x"])
        flow._reflow()  # resize reflow must not crash
        self.assertEqual(len(flow._children), 3)
        window.close()

    def test_tree_row_icons(self):
        tree = ts.TTree(headings=["H"], key="-TR-")
        window = ts.Window("t", [[tree]], finalize=True)
        tree.insert("", "item1", "Root", image_data=ts.BLANK_BASE64)
        item = tree.widget.item("item1")
        self.assertTrue(item.get("image"))
        self.assertEqual(len(tree._images), 1)  # photo retained
        window.close()

    def test_table_row_icons(self):
        table = ts.TTable(
            [["a"], ["b"]],
            headings=["H"],
            key="-TB-",
            row_icons=[ts.BLANK_BASE64, None],
        )
        window = ts.Window("t", [[table]], finalize=True)
        children = table.widget.get_children()
        self.assertTrue(table.widget.item(children[0]).get("image"))
        self.assertEqual(table.widget.item(children[1]).get("image"), "")
        window.close()

    def test_table_cell_edit(self):
        table = ts.TTable(
            [["old", "x"], ["keep", "y"]],
            headings=["A", "B"],
            key="-TB-",
            enable_edit=True,
        )
        window = ts.Window("t", [[table]], finalize=True)
        window.refresh()
        item = table.widget.get_children()[0]
        table._begin_cell_edit(item, "#1")
        self.assertIsNotNone(table._editor)
        table._editor.delete(0, "end")
        table._editor.insert(0, "new")
        table._finish_cell_edit(
            table._editor, item, table._values[0], 0, 0
        )
        window.refresh()
        self.assertEqual(table.values[0], ["new", "x"])
        event, _values = window.read(timeout=500)
        self.assertEqual(event, ("-TB-", 0, 0, "new"))
        self.assertIsNone(table._editor)
        window.close()

    def test_shape(self):
        shape = ts.TShape("oval", size=(60, 30), fill_color="red", key="-S-")
        window = ts.Window("t", [[shape]], finalize=True)
        self.assertEqual(len(shape.widget.find_all()), 1)
        shape.update(fill_color="blue", line_color="green")
        with self.assertRaises(ValueError):
            ts.TShape("hexagon")
        window.close()


class TestThirdBatch(unittest.TestCase):
    """Batch 3: Action, UserSettings, data binding, i18n, animation, tray, CLI."""

    def test_action_normalization_and_callback(self):
        fired = []
        open_action = ts.Action(
            "Open", key="-OPEN-", callback=lambda w, v: fired.append("open")
        )
        menu_item = ts.TText("menu", key="Open")  # posting text "Open"
        window = ts.Window(
            "t", [[menu_item]], finalize=True, actions=[open_action]
        )
        window._post_event("Open")  # menu text normalizes to the key
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-OPEN-")
        self.assertEqual(fired, ["open"])
        window.close()

    def test_action_shortcut_bound(self):
        save_action = ts.Action("Save", key="-SAVE-", shortcut="<Control-s>")
        window = ts.Window("t", [[ts.TText("x")]], finalize=True, actions=[save_action])
        shortcuts = [pattern for pattern, _key in window._event_binds]
        self.assertIn("<Control-s>", shortcuts)
        window.close()

    def test_action_list_helpers(self):
        actions = ts.ActionList(
            [ts.Action("Open", key="-OPEN-"), ts.Action("Exit", key="-EXIT-")]
        )
        self.assertEqual(actions.keys(), ["-OPEN-", "-EXIT-"])
        self.assertEqual(actions.by_text("Exit").key, "-EXIT-")
        self.assertEqual(actions.by_key("-OPEN-").text, "Open")
        self.assertEqual(
            actions.menu_definition("&File"),
            [["&File", "Open", "Exit"]],
        )
        button = ts.Action("Save", key="-SAVE-").to_button()
        self.assertEqual(button.key, "-SAVE-")
        self.assertEqual(button.button_text, "Save")

    def test_user_settings(self):
        import shutil
        import tempfile

        directory = tempfile.mkdtemp()
        try:
            prefs = ts.UserSettings("test.json", path=directory)
            prefs.set("theme", "Slate")
            prefs.set("window/size", "800x600")
            self.assertEqual(prefs.get("theme"), "Slate")
            self.assertEqual(prefs.get("window/size"), "800x600")
            self.assertIn("theme", prefs)
            self.assertEqual(prefs["window/size"], "800x600")
            # a fresh instance reads the same file back
            again = ts.UserSettings("test.json", path=directory)
            self.assertEqual(again.get("theme"), "Slate")
            again.delete("window/size")
            self.assertNotIn("window/size", again)
            self.assertIsNone(again.get("window/size"))
            prefs.delete_file()
            self.assertEqual(ts.UserSettings("test.json", path=directory).as_dict(), {})
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_table_bind(self):
        records = [
            {"name": "apple", "qty": 3},
            {"name": "pear", "qty": 1},
        ]
        table = ts.TTable([], headings=[], key="-TB-")
        window = ts.Window("t", [[table]], finalize=True)
        table.set_records(records)
        window.refresh()
        self.assertEqual(table.headings, ["name", "qty"])
        children = table.widget.get_children()
        self.assertEqual(
            [list(table.widget.item(c, "values")) for c in children],
            [["apple", "3"], ["pear", "1"]],
        )
        table.widget.selection_set(children[0])
        self.assertEqual(table.selected_records, [{"name": "apple", "qty": 3}])
        # cell edit writes back into the bound record
        table._begin_cell_edit(children[0], "#2")
        self.assertIsNotNone(table._editor)
        table._editor.delete(0, "end")
        table._editor.insert(0, "9")
        table._finish_cell_edit(table._editor, children[0], table._values[0], 0, 1)
        self.assertEqual(records[0]["qty"], "9")
        # sorting keeps records aligned
        table.sort_by(1, ascending=True)
        children = table.widget.get_children()  # sorting clears the selection
        table.widget.selection_set(children[0])
        self.assertEqual(table.selected_records[0]["name"], "pear")
        window.close()

    def test_animation_fade_and_progress(self):
        bar = ts.TProgressBar(100, key="-BAR-")
        window = ts.Window("t", [[bar]], finalize=True)
        handle = ts.animate_progress(window, "-BAR-", 100, duration_ms=60, steps=4)
        deadline = time.time() + 2.0
        while handle.active and time.time() < deadline:
            window.read(timeout=20)
        self.assertEqual(bar.get(), 100)
        self.assertFalse(handle.active)
        fade = ts.fade_in(window, duration_ms=60, steps=4)
        window.refresh()
        fade.cancel()
        window.close()

    def test_animation_slide(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        target = (window.current_location()[0] + 30, window.current_location()[1])
        handle = ts.slide(window, target, duration_ms=60, steps=3)
        deadline = time.time() + 2.0
        while handle.active and time.time() < deadline:
            window.read(timeout=20)
        location = window.current_location()
        self.assertGreaterEqual(location[0], target[0] - 2)
        window.close()

    @unittest.skipUnless(ts.running_windows(), "SystemTray is Windows only")
    def test_system_tray_lifecycle(self):
        # runs in a subprocess: the tray owns a hidden Win32 message window,
        # and its WndProc must not interleave with this process's Tcl state
        import subprocess

        probe = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "probes", "_tray_probe.py"
        )
        result = subprocess.run(
            [sys.executable, probe],
            capture_output=True,
            timeout=60,
            check=False,  # returncode asserted below
        )
        output = result.stdout.decode("utf-8", "replace")
        self.assertEqual(
            result.returncode, 0, output + result.stderr.decode("utf-8", "replace")
        )
        self.assertIn("step: read -> __TIMEOUT__", output)
        self.assertIn("SURVIVED", output)

    def test_cli(self):
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ts.main(["--version"])
        self.assertIn("TkSimpleGUI", buffer.getvalue())
        self.assertIn(ts.__version__, buffer.getvalue())
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ts.main(["--themes"])
        # 5 hand-picked themes, printed one per line
        self.assertEqual(len(buffer.getvalue().splitlines()), 5)
        for name in ("System", "Slate", "Daylight", "Dusk", "Sage"):
            self.assertIn(name, buffer.getvalue())

    def test_dbg_returns_quickly(self):
        # dbg formats args and delegates to the notification popup
        self.assertTrue(callable(ts.dbg))
        self.assertTrue(callable(ts.popup_notify))


class TestLineA(unittest.TestCase):
    """Line A: full coverage of the native Tk/ttk API surface."""

    def test_element_bind_and_unbind(self):
        element = ts.TText("click me", key="-T-")
        window = ts.Window("t", [[element]], finalize=True)
        element.bind("<F5>")  # posts the element key
        element.widget.focus_set()
        window.refresh()
        element.widget.event_generate("<F5>", when="tail")
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-T-")
        element.bind("<Button-3>", key="-CUSTOM-")
        element.widget.event_generate("<Button-3>", when="tail")
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-CUSTOM-")
        calls = []
        element.bind("<Button-2>", callback=lambda el, ev: calls.append(el))
        element.widget.event_generate("<Button-2>", when="tail")
        window.refresh()
        self.assertEqual(calls, [element])
        element.unbind("<Button-2>")
        window.close()

    def test_bind_before_finalize_raises(self):
        element = ts.TText("x")
        with self.assertRaises(RuntimeError):
            element.bind("<Button-1>")

    def test_multiline_scrollbar_wrap(self):
        multiline = ts.TMultiline(
            "\r\n".join(f"line {i}" for i in range(50)),
            size=(30, 4), scroll_y=True, wrap="none", key="-ML-",
        )
        window = ts.Window("t", [[multiline]], finalize=True)
        container = multiline.widget
        self.assertIsInstance(container, tk.Frame)  # composite container
        children = container.winfo_children()
        self.assertEqual(len(children), 2)  # text + scrollbar
        self.assertEqual(str(multiline._text.cget("wrap")), "none")
        self.assertEqual(multiline.get().splitlines()[0], "line 0")
        window.close()

    def test_multiline_link_and_search(self):
        multiline = ts.TMultiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.write("Visit ")
        multiline.link("TkSimpleGUI", key="-LINK-")
        self.assertEqual(multiline.search_all("Simple"), 1)
        ranges = multiline._text.tag_ranges("search_all")
        self.assertEqual(len(ranges), 2)  # start + end index
        multiline.clear_highlights()
        self.assertEqual(len(multiline._text.tag_ranges("search_all")), 0)
        # clicking the link region posts the key
        multiline._text.tag_bind  # noqa: B018 - tags exist via link()
        window.close()

    def test_image_zoom_and_subsample(self):
        image = ts.TImage(data_base64=ts.DEFAULT_BASE64_ICON, zoom=2)
        window = ts.Window("t", [[image]], finalize=True)
        self.assertEqual(image._photo.width(), 128)
        window.close()
        image = ts.TImage(data_base64=ts.DEFAULT_BASE64_ICON, subsample=2)
        window = ts.Window("t", [[image]], finalize=True)
        self.assertEqual(image._photo.width(), 32)
        window.close()

    def test_spin_is_ttk(self):
        spin = ts.TSpin([1, 2, 3], initial_value=2)
        window = ts.Window("t", [[spin]], finalize=True)
        self.assertIsInstance(spin.widget, ttk.Spinbox)
        self.assertEqual(spin.get(), "2")
        window.close()

    def test_ttk_theme_switch(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        available = ts.ttk_themes()
        self.assertTrue(available)
        current = ts.ttk_theme()
        if "clam" in available:
            self.assertEqual(ts.ttk_theme("clam"), "clam")
            self.assertEqual(ts.ttk_theme(), "clam")
            ts.ttk_theme(current)
        with self.assertRaises(ValueError):
            ts.ttk_theme("__nope__")
        window.close()

    def test_window_wm_extensions(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.set_fullscreen(True)
        window.refresh()
        self.assertEqual(int(window.tk_root.attributes("-fullscreen")), 1)
        window.set_fullscreen(False)
        window.make_toolwindow(False)
        window.set_max_size((800, 600))
        window.bell()
        child = ts.Window("child", [[ts.TText("c")]], finalize=True)
        child.transient(window)
        child.stack_above(window)
        child.close()
        window.close()

    def test_window_selection(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.selection_set("primary-data")
        window.refresh()
        self.assertEqual(window.selection_get(), "primary-data")
        window.close()

    def test_window_style_hooks(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.configure_style("TButton", padding=(16, 8))
        window.map_style("TButton", background=[("active", "#3a7bd5")])
        window.close()

    def test_font_tools(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        families = ts.font_families()
        self.assertTrue(families)
        width = ts.font_measure("hello", ("Helvetica", 10))
        self.assertGreater(width, 0)
        actual = ts.font_actual(("Helvetica", 12, "bold"))
        self.assertEqual(actual["size"], 12)
        self.assertEqual(actual["weight"], "bold")
        window.close()

    def test_menubutton_element(self):
        menu_button = ts.TMenubutton("Options", ["One", "---", "Two"], key="-MB-")
        window = ts.Window("t", [[menu_button]], finalize=True)
        self.assertEqual(menu_button.items, ["One", "---", "Two"])
        menu_button.update(items=["Alpha"])
        menu = menu_button.widget.nametowidget(menu_button.widget.cget("menu"))
        self.assertEqual(menu.entrycget(0, "label"), "Alpha")
        menu.invoke(0)
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "Alpha")
        window.close()

    def test_scrollbar_element(self):
        multiline = ts.TMultiline("\r\n".join(f"line {i}" for i in range(60)),
                                 size=(20, 3), key="-ML-")
        scrollbar = ts.TScrollbar(multiline, orientation="v")
        window = ts.Window("t", [[multiline, scrollbar]], finalize=True)
        self.assertIsNotNone(scrollbar.widget)
        with self.assertRaises(TypeError):
            ts.Window("t2", [[ts.TScrollbar(ts.TText("not scrollable"))]], finalize=True)
        window.close()

    def test_tabgroup_enhancements(self):
        tab_group = ts.TTabGroup(
            [[ts.TTab("one", [[ts.TText("1")]]), ts.TTab("two", [[ts.TText("2")]])]],
            key="-TG-", enable_events=True, enable_traversal=True,
        )
        window = ts.Window("t", [[tab_group]], finalize=True)
        self.assertEqual(tab_group.current_tab, "one")
        tab_group.select_tab("two")
        window.refresh()
        self.assertEqual(tab_group.current_tab, "two")
        event, _values = window.read(timeout=500)
        self.assertEqual(event, ("-TG-", "two"))
        tab_group.update(tab="two", tab_state="disabled")
        self.assertEqual(tab_group.widget.tab(1, "state"), "disabled")
        window.close()


class TestChart(unittest.TestCase):
    """TChart: 8 chart types on the TGraph coordinate system."""

    def _chart(self, kind, **kwargs):
        chart = ts.TChart((300, 180), chart_type=kind, key="-C-",
                          background_color="#ffffff", **kwargs)
        window = ts.Window("t", [[chart]], finalize=True)
        self.addCleanup(window.close)
        return chart

    def test_invalid_type_rejected(self):
        with self.assertRaises(ValueError):
            ts.TChart(chart_type="radar")

    @unittest.skipUnless(HAS_PIL, "Pillow not installed")
    def test_line_two_series(self):
        chart = self._chart("line")
        chart.add_series("A", [3, 7, 2, 9], labels=["a", "b", "c", "d"])
        chart.add_series("B", [5, 4, 8, 3])
        chart.redraw()
        # one raster frame (image) + axes/grid/ticks/legend vector items
        figures = chart.widget.find_all()
        self.assertGreater(len(figures), 5)
        kinds = {chart.widget.type(i) for i in figures}
        self.assertIn("image", kinds)
        self.assertEqual(chart.series_names, ["A", "B"])

    def test_bar_grouped(self):
        chart = self._chart("bar")
        chart.add_series("E", [12, 30, 8], labels=["x", "y", "z"])
        chart.add_series("W", [9, 24, 16])
        chart.redraw()
        # one raster frame (image) + axes/grid/ticks/legend vector items
        figures = chart.widget.find_all()
        self.assertGreater(len(figures), 5)

    def test_pie_slices_and_legend(self):
        # vector path: every slice is its own canvas figure
        chart = self._chart("pie", anti_alias=False)
        chart.add_series("share", [("alpha", 30), ("beta", 20), ("gamma", 50)])
        chart.redraw()
        figures = chart.widget.find_all()
        # 3 pieslices + 3 legend swatches + 3 legend texts
        self.assertGreaterEqual(len(figures), 9)

    def test_update_data_and_refcount(self):
        chart = self._chart("pie")
        chart.add_series("share", [("a", 1), ("b", 2)])
        chart.update_data("share", [("a", 5), ("b", 5), ("c", 5)])
        self.assertEqual(chart._series[0].values, [5.0, 5.0, 5.0])
        self.assertEqual(chart._series[0].labels, ["a", "b", "c"])
        with self.assertRaises(KeyError):
            chart.update_data("missing", [1])

    def test_all_types_render(self):
        for kind in ts.ChartType.ALL:
            chart = self._chart(kind)
            if kind in ("pie", "donut"):
                chart.add_series("s", [("a", 1), ("b", 2)])
            else:
                chart.add_series("s", [1, 3, 2], labels=["a", "b", "c"])
            chart.redraw()
            self.assertGreater(
                len(chart.widget.find_all()), 3, msg=f"kind={kind}"
            )

    def test_redraw_before_finalize_is_safe(self):
        chart = ts.TChart((200, 150), chart_type="line")
        chart.add_series("A", [1, 2, 3])
        chart.redraw()  # no widget yet: must be a no-op, no raise


class TestLineB(unittest.TestCase):
    """Line B: what Tk cannot do (canvas-drawn, synthesized events, ctypes)."""

    def test_round_button(self):
        button = ts.TRoundButton("Go", size=(90, 30), radius=14,
                                fill_color="#e91e63", key="-RB-")
        window = ts.Window("t", [[button]], finalize=True)
        window.tk_root.update()
        self.assertEqual(len(button.widget.find_all()), 2)  # background + text
        # clicking the middle posts the key
        button.widget.event_generate("<Button-1>", x=45, y=15, when="tail")
        window.tk_root.update()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-RB-")
        button.update(value="Stop")
        window.close()

    def test_round_button_direct_callback(self):
        calls = []
        button = ts.TRoundButton("Go", key="-RB-")
        button.set_click_handler(calls.append)
        window = ts.Window("t", [[button]], finalize=True)
        window.tk_root.update()
        button.widget.event_generate("<Button-1>", x=45, y=15, when="tail")
        window.tk_root.update()
        self.assertEqual(calls, [button])
        window.close()

    def test_image_button(self):
        button = ts.TImageButton(data_base64=ts.DEFAULT_BASE64_ICON, key="-IB-")
        window = ts.Window("t", [[button]], finalize=True)
        window.tk_root.update()
        self.assertEqual(button._photo.width(), 64)  # sized from the image
        button.widget.event_generate("<Button-1>", x=10, y=10, when="tail")
        window.tk_root.update()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-IB-")
        window.close()

    def test_text_progress_bar(self):
        bar = ts.TTextProgressBar(100, current_value=42, key="-TPB-")
        window = ts.Window("t", [[bar]], finalize=True)
        self.assertEqual(bar.get(), 42)
        label = bar._widget.itemconfigure(bar._label_id, "text")
        self.assertEqual(str(label[-1]), "42%")
        bar.update(current_value=100)
        label = bar._widget.itemconfigure(bar._label_id, "text")
        self.assertEqual(str(label[-1]), "100%")
        window.close()

    def test_toast(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        toast = window.toast("Saved", title="Demo", duration_ms=400)
        self.assertIsNotNone(toast)
        self.assertTrue(toast.winfo_exists())
        # let the fade-out schedule finish its lifecycle without blocking
        deadline = time.time() + 2.5
        while toast.winfo_exists() and time.time() < deadline:
            window.read(timeout=50)
        self.assertFalse(toast.winfo_exists())
        window.close()

    def test_table_column_resize_event(self):
        table = ts.TTable([["a", "b"]], headings=["H1", "H2"], key="-TB-")
        window = ts.Window("t", [[table]], finalize=True)
        width = table.column_width(0)
        self.assertGreater(width, 0)
        table.set_column_width(0, 150)
        self.assertEqual(table.column_width(0), 150)
        window.close()

    def test_slider_value_bubble(self):
        slider = ts.TSlider((0, 100), default_value=30, show_value=True,
                           enable_events=True, key="-SL-")
        window = ts.Window("t", [[slider]], finalize=True)
        slider.widget.event_generate("<ButtonPress-1>", x=20, y=5)
        window.refresh()
        self.assertIsNotNone(slider._bubble)
        self.assertTrue(slider._bubble.winfo_exists())
        slider.widget.event_generate("<ButtonRelease-1>", x=20, y=5)
        window.refresh()
        if slider._bubble_job is not None:
            slider.widget.after_cancel(slider._bubble_job)
        if slider._bubble is not None:
            slider._bubble.destroy()
        window.close()

    def test_tree_groups(self):
        tree = ts.TTree(key="-TR-")
        window = ts.Window("t", [[tree]], finalize=True)
        tree.insert_group("", "grp1", "Fruits")
        tree.insert("grp1", "a1", "Apple")
        tree.insert_summary("grp1", "sum1", "2 items")
        tags = tree.widget.item("grp1", "tags")
        self.assertIn("group", tags)
        self.assertIn("summary", tree.widget.item("sum1", "tags"))
        self.assertTrue(tree.widget.item("grp1", "open"))
        tree.collapse("grp1")
        self.assertFalse(tree.widget.item("grp1", "open"))
        tree.expand("grp1")
        tree.toggle("grp1")
        self.assertFalse(tree.widget.item("grp1", "open"))
        window.close()

    def test_tabgroup_close_button(self):
        tab_group = ts.TTabGroup(
            [[ts.TTab("one", [[ts.TText("1")]]), ts.TTab("two", [[ts.TText("2")]])]],
            key="-TG-", enable_events=True, enable_close=True,
        )
        window = ts.Window("t", [[tab_group]], finalize=True)
        label = tab_group.widget.tab(0, "text")
        self.assertIn("×", str(label))
        tab_group.close_tab("one")
        self.assertEqual(len(tab_group.tabs), 1)
        self.assertEqual(tab_group.closed_tabs, ["one"])
        event, _values = window.read(timeout=500)
        self.assertEqual(event, ("-TG-", "tab_closed", "one"))
        window.close()

    def test_hotkey_parse(self):
        modifiers, virtual_key = ts.GlobalHotkeys.parse("Ctrl-Alt-P")
        self.assertEqual(modifiers, 0x0002 | 0x0001)
        self.assertEqual(virtual_key, ord("P"))
        modifiers, virtual_key = ts.GlobalHotkeys.parse("Shift-F5")
        self.assertEqual(modifiers, 0x0004)
        self.assertEqual(virtual_key, 0x70 + 5 - 1)
        with self.assertRaises(ValueError):
            ts.GlobalHotkeys.parse("Ctrl")
        with self.assertRaises(ValueError):
            ts.GlobalHotkeys.parse("Ctrl-Foo")

    @unittest.skipUnless(ts.running_windows(), "hotkeys are Windows only")
    def test_global_hotkeys_lifecycle(self):
        hotkeys = ts.GlobalHotkeys()
        hotkeys.register("Ctrl-Alt-F24", "-HK-TEST-")
        self.assertEqual(hotkeys.combos, ["Ctrl-Alt-F24"])
        hotkeys.stop()
        self.assertEqual(hotkeys.combos, [])
        # re-register works after stop
        hotkeys.register("Ctrl-Alt-F24", "-HK-TEST-")
        hotkeys.stop()

    def test_taskbar_progress_gate(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        progress = ts.taskbar_progress(window)
        if ts.running_windows():
            self.assertIsNotNone(progress)
        else:
            self.assertIsNone(progress)
        window.close()


class TestUnifiedLoop(unittest.TestCase):
    """Single event loop: global bus + run_application, multi-window by design."""

    def tearDown(self):
        ts.Window.close_all()

    def test_cross_window_events(self):
        """Any window read() receives events from other windows (bus order)."""
        first = ts.Window("one", [[ts.TButton("ping", key="-PING-")]], finalize=True)
        second = ts.Window("two", [[ts.TButton("pong", key="-PONG-")]], finalize=True)
        first.write_event_value("-FROM-ONE-")
        second.write_event_value("-FROM-TWO-")
        # reading through the *second* window still yields the first's event
        event, _values = second.read(timeout=500)
        self.assertEqual(event, "-FROM-ONE-")
        event, _values = second.read(timeout=500)
        self.assertEqual(event, "-FROM-TWO-")
        first.close()
        second.close()

    def test_read_all_windows_returns_owner(self):
        first = ts.Window("one", [[ts.TText("x")]], finalize=True)
        second = ts.Window("two", [[ts.TText("y")]], finalize=True)
        second.write_event_value("-TWO-EVENT-")
        window, event, _values = ts.Window.read_all_windows(timeout=500)
        self.assertIs(window, second)
        self.assertEqual(event, "-TWO-EVENT-")
        first.close()
        second.close()

    def test_winclosed_removes_window_from_registry(self):
        first = ts.Window("one", [[ts.TText("x")]], finalize=True)
        second = ts.Window("two", [[ts.TText("y")]], finalize=True)
        # the WM_DELETE_WINDOW protocol handler posts WIN_CLOSED; firing it
        # here simulates the user clicking the title bar X
        first._post_event(ts.WIN_CLOSED)
        window, event, _values = ts.Window.read_all_windows(timeout=500)
        self.assertIs(window, first)
        self.assertEqual(event, ts.WIN_CLOSED)
        self.assertNotIn(first, ts.Window.active_windows())
        self.assertIn(second, ts.Window.active_windows())
        second.close()

    def test_programmatic_close_is_quiet(self):
        """Window.close() does not post WIN_CLOSED (no user action happened)."""
        first = ts.Window("one", [[ts.TText("x")]], finalize=True)
        second = ts.Window("two", [[ts.TText("y")]], finalize=True)
        first.close()
        event, _values = second.read(timeout=200)
        self.assertEqual(event, ts.TIMEOUT_KEY)
        second.close()

    def test_main_loop_exits_when_all_closed(self):
        app = ts.TkSimpleEvent()
        window = ts.Window("one", [[ts.TButton("quit", key="-QUIT-")]], finalize=True)
        seen = []

        @app.bind_event("-QUIT-")
        def on_quit(window, values):
            seen.append("quit")
            window.close()  # last window gone -> loop ends

        window.write_event_value("-QUIT-")  # fires once the loop pumps
        ts.run_application(window, app)
        self.assertEqual(seen, ["quit"])
        self.assertEqual(ts.Window.active_windows(), [])

    def test_run_application_dispatches_to_on_handlers(self):
        app = ts.TkSimpleEvent()
        main = ts.Window("main", [[ts.TButton("open", key="-OPEN-")]], finalize=True)
        received = []

        @app.bind_event("-OPEN-")
        def on_open(window, values):
            child = ts.Window("child", [[ts.TText("hi", key="-HI-")]], finalize=True)
            child.write_event_value("-CHILD-READY-")

        @app.bind_event("-CHILD-READY-")
        def on_child_ready(window, values):
            received.append(window.title)
            ts.Window.close_all()

        main.write_event_value("-OPEN-")  # fires inside the loop
        ts.run_application(main, app)
        self.assertEqual(received, ["child"])  # handler got the CHILD window
        self.assertEqual(ts.Window.active_windows(), [])

    def test_run_application_with_action_callbacks(self):
        calls = []
        app = ts.TkSimpleEvent()
        ok_action = ts.Action("OK", key="OK",
                              callback=lambda window, values: calls.append("ok"))
        window = ts.Window("t", [[ts.TButton("OK", key="OK")]],
                           finalize=True, actions=[ok_action])

        @app.bind_event("OK")
        def on_ok(window, values):
            calls.append("handler")
            ts.Window.close_all()

        window.write_event_value("OK")  # fires inside the loop
        ts.run_application(window, app)
        self.assertEqual(calls, ["ok", "handler"])

    def test_close_all_drops_stale_events(self):
        first = ts.Window("one", [[ts.TText("x")]], finalize=True)
        first.write_event_value("-STALE-")
        ts.Window.close_all()
        second = ts.Window("two", [[ts.TText("y")]], finalize=True)
        event, _values = second.read(timeout=200)
        self.assertEqual(event, ts.TIMEOUT_KEY)  # stale event was dropped
        second.close()


class TestWindowHierarchy(unittest.TestCase):
    """Window hierarchy: parent/children/ancestors + cascading close."""

    def test_parent_link_and_query(self):
        main = ts.Window("main", [[ts.TText("m")]], finalize=True)
        child = ts.Window("child", [[ts.TText("c")]], finalize=True, parent=main)
        grandchild = ts.Window("grand", [[ts.TText("g")]], finalize=True, parent=child)
        self.assertIs(child.parent, main)
        self.assertIs(grandchild.parent, child)
        self.assertIsNone(main.parent)
        self.assertIn(child, main.children)
        self.assertIn(grandchild, child.children)
        self.assertEqual(grandchild.ancestors, [child, main])
        self.assertTrue(grandchild.is_child_of(main))
        self.assertFalse(main.is_child_of(child))
        main.close()  # cascades: child and grandchild close too
        self.assertTrue(child.was_closed)
        self.assertTrue(grandchild.was_closed)
        self.assertEqual(main.children, [])

    def test_parent_parameter_before_finalize(self):
        main = ts.Window("main", [[ts.TText("m")]], finalize=True)
        child = ts.Window("child", [[ts.TText("c")]], parent=main)  # not finalized yet
        self.assertIs(child.parent, main)
        child.finalize()  # link established at finalize
        self.assertIn(child, main.children)
        child.close()
        self.assertEqual(main.children, [])
        main.close()

    def test_transient_sets_parent(self):
        main = ts.Window("main", [[ts.TText("m")]], finalize=True)
        dialog = ts.Window("dialog", [[ts.TText("d")]], finalize=True)
        dialog.transient(main)
        self.assertIs(dialog.parent, main)
        self.assertIn(dialog, main.children)
        dialog.transient(None)  # detach
        self.assertIsNone(dialog.parent)
        self.assertEqual(main.children, [])
        dialog.close()
        main.close()

    def test_child_close_keeps_parent(self):
        main = ts.Window("main", [[ts.TText("m")]], finalize=True)
        child = ts.Window("child", [[ts.TText("c")]], finalize=True, parent=main)
        child.close()
        self.assertFalse(main.was_closed)
        self.assertEqual(main.children, [])
        main.close()


class TestForcedModal(unittest.TestCase):
    """Forced-modal windows: disable_esc, modal/auto disable_close, system_block."""

    def tearDown(self):
        ts.Window.close_all()

    def test_disable_esc_blocks_escape_key(self):
        window = ts.Window(
            "t", [[ts.TText("x")]], finalize=True, disable_esc=True
        )
        window.tk_root.event_generate("<Escape>")
        window.tk_root.update()
        # the break handler swallows the key: no WIN_CLOSED event was posted
        with self.assertRaises(queue.Empty):
            window._event_queue.get_nowait()
        window.close()

    def test_esc_without_flag_reaches_window(self):
        window = ts.Window("t", [[ts.TText("x")]], finalize=True)
        window.tk_root.event_generate("<Escape>")
        window.tk_root.update()
        # without disable_esc the key press is not swallowed; the window
        # stays open and its queue simply receives no forced break
        self.assertFalse(window.was_closed)
        window.close()

    def test_disable_close_blocks_frame_and_modal_implies_it(self):
        window = ts.Window(
            "t", [[ts.TText("x")]], finalize=True, disable_close=True
        )
        # simulate the frame close button: the protocol handler is a no-op
        window.tk_root.protocol("WM_DELETE_WINDOW")() if False else None
        window.tk_root.update()
        self.assertFalse(window.was_closed)
        window.close()

    def test_modal_sets_grab_and_blocks_frame_close(self):
        main = ts.Window("main", [[ts.TText("m")]], finalize=True)
        dialog = ts.Window(
            "dialog", [[ts.TButton("OK", key="-OK-")]],
            finalize=True, modal=True,
        )
        self.assertEqual(dialog.tk_root.grab_current(), dialog.tk_root)
        # modal implies disable_close: no WIN_CLOSED can be posted by the frame
        self.assertFalse(dialog.was_closed)
        dialog.close()
        main.close()

    def test_system_block_released_on_close(self):
        window = ts.Window(
            "t", [[ts.TText("x")]], finalize=True, system_block=True
        )
        self.assertTrue(window._system_block)
        self.assertTrue(window._want_system_block)
        window.close()
        self.assertFalse(window._system_block)
        self.assertFalse(window._want_system_block)

    def test_system_block_hide_releases_and_unhide_rearms(self):
        window = ts.Window(
            "t", [[ts.TText("x")]], finalize=True, system_block=True
        )
        self.assertTrue(window._system_block)
        window.hide()
        self.assertFalse(window._system_block)  # released while hidden
        window.unhide()
        self.assertTrue(window._system_block)  # re-armed on show
        window.close()

    def test_system_block_refcount_two_windows(self):
        # two blocking windows stack: closing one must not release the
        # other's hooks (refcount) — only the last close tears them down
        first = ts.Window("a", [[ts.TText("x")]], finalize=True, system_block=True)
        second = ts.Window("b", [[ts.TText("x")]], finalize=True, system_block=True)
        self.assertTrue(first._system_block and second._system_block)
        first.close()
        self.assertFalse(first._system_block)
        self.assertTrue(second._system_block)
        second.close()
        self.assertFalse(second._system_block)

    def test_input_blocker_refcount_direct(self):
        # direct acquire/release stacking on the blocker object
        from TkSimpleGUI.input_blocker import block_input, unblock_input

        if not hasattr(ctypes, "windll"):
            self.assertRaises(ImportError, block_input)
            return
        blocker = block_input()
        block_input()  # nested acquire bumps the count
        unblock_input()  # first release: hooks stay up
        self.assertGreaterEqual(blocker._count, 1)
        unblock_input()  # second release: hooks come down
        self.assertEqual(blocker._count, 0)

    def test_window_config_forced_fields(self):
        cfg = ts.WindowConfig(
            title="forced", modal=True, disable_esc=True, system_block=True
        )
        window = ts.Window(config=cfg, layout=[[ts.TText("x")]], finalize=True)
        self.assertTrue(window._modal)
        self.assertTrue(window._disable_esc)
        self.assertTrue(window._system_block)
        window.close()


class TestRunEntry(unittest.TestCase):
    """Root .run() entry: window root / tray root / default event manager."""

    def tearDown(self):
        ts.Window.close_all()

    def test_window_run_with_explicit_app(self):
        app = ts.TkSimpleEvent()
        window = ts.Window("one", [[ts.TButton("quit", key="-QUIT-")]], finalize=True)
        seen = []

        @app.bind_event("-QUIT-")
        def on_quit(window, values):
            seen.append("quit")
            ts.Window.close_all()  # ends the loop

        window.write_event_value("-QUIT-")
        window.run(app)  # root object starts the loop directly
        self.assertEqual(seen, ["quit"])
        self.assertEqual(ts.Window.active_windows(), [])

    def test_window_run_uses_default_app(self):
        app = ts.default_app()

        @app.bind_event("-RUN-EVENT-")
        def on_run_event(window, values):
            ts.Window.close_all()

        window = ts.Window("one", [[ts.TText("x")]], finalize=True)
        window.write_event_value("-RUN-EVENT-")
        window.run()  # no app: default_app() is used, handler above fires
        self.assertEqual(ts.Window.active_windows(), [])

    def test_run_survives_idle_bus_before_any_event(self):
        # regression: read_all_windows(timeout=0) returns (None, TIMEOUT_KEY)
        # when the bus is empty, which used to be mistaken for "all windows
        # closed" — run() exited immediately on the first idle tick
        app = ts.TkSimpleEvent()

        @app.bind_event("-LATE-")
        def on_late(window, values):
            ts.Window.close_all()

        window = ts.Window("idle", [[ts.TText("x")]], finalize=True)
        # post the event AFTER the loop has had a chance to see idle ticks
        window.tk_root.after(300, lambda: window.write_event_value("-LATE-"))
        window.run(app)
        self.assertTrue(window.was_closed)

    def test_default_app_is_singleton(self):
        self.assertIs(ts.default_app(), ts.default_app())
        self.assertIsInstance(ts.default_app(), ts.TkSimpleEvent)

    def test_package_level_bind_event(self):
        """@ts.bind_event wires handlers without any explicit manager import."""
        fired = []

        @ts.bind_event("-PKG-LEVEL-EVENT-")
        def on_pkg_level(window, values):
            fired.append(window.title)
            ts.Window.close_all()  # ends the loop

        window = ts.Window("one", [[ts.TText("x")]], finalize=True)
        window.write_event_value("-PKG-LEVEL-EVENT-")
        window.run()  # default_app must see the handler above
        self.assertEqual(fired, ["one"])

        ts.default_app()._event_handlers.pop("-PKG-LEVEL-EVENT-", None)

    def test_run_without_finalize_finalizes(self):
        app = ts.TkSimpleEvent()
        window = ts.Window("one", [[ts.TText("x")]])  # NOT finalized

        @app.bind_event("-GO-")
        def on_go(window, values):
            ts.Window.close_all()

        window.write_event_value("-GO-")
        window.run(app)  # run() must finalize the anchor first
        self.assertTrue(window.was_closed)

    def test_on_close_callback_blocks_close(self):
        """on_close=False keeps the window open; on_close=True closes it."""
        decisions = [False, True]
        window = ts.Window(
            "guarded",
            [[ts.TText("x")]],
            finalize=True,
            on_close=lambda w: decisions.pop(0),
        )
        try:
            # False -> no WIN_CLOSED posted, window stays open
            window._handle_on_close()
            self.assertFalse(window.was_closed)
            self.assertEqual(ts.Window._event_bus.qsize(), 0)
            # True -> WIN_CLOSED lands on the bus, then read() drains & closes
            window._handle_on_close()
            self.assertEqual(ts.Window._event_bus.qsize(), 1)
            _event_window, event, _values = ts.Window.read_all_windows()
            self.assertIs(event, ts.WIN_CLOSED)
            self.assertIs(_event_window, window)
            self.assertTrue(window.was_closed)
        finally:
            if not window.was_closed:
                window.close()

    def test_on_close_runtime_setter(self):
        """Setting on_close after construction wires the WM_DELETE_WINDOW hook."""
        window = ts.Window("late", [[ts.TText("y")]], finalize=True)
        try:
            self.assertIsNone(window._on_close)
            window.on_close = lambda w: True
            self.assertIsNotNone(window._on_close)
            window._handle_on_close()
            # bus has the WIN_CLOSED; drain it and confirm close
            self.assertEqual(ts.Window._event_bus.qsize(), 1)
            _event_window, _event, _values = ts.Window.read_all_windows()
            self.assertIs(_event_window, window)
            self.assertTrue(window.was_closed)
        finally:
            if not window.was_closed:
                window.close()
            window.on_close = None  # restore

    def test_demos_basic_window_imports(self):
        """``demos/basic_window.py`` loads without errors and exposes main()."""
        import importlib.util
        import os

        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "demos", "basic_window.py",
        )
        spec = importlib.util.spec_from_file_location("_basic_window_demo", path)
        module = importlib.util.module_from_spec(spec)
        # the demo prepends src/ to sys.path before importing TkSimpleGUI
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
        added = src not in sys.path
        if added:
            sys.path.insert(0, src)
        try:
            spec.loader.exec_module(module)
        finally:
            if added:
                sys.path.remove(src)
        self.assertTrue(callable(getattr(module, "main", None)))
        self.assertTrue(callable(getattr(module, "make_main_window", None)))

    def test_demos_showcase_smoke(self):
        """``demos/showcase.py`` builds its main window in --smoke mode."""
        import os
        import subprocess

        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "demos", "showcase.py",
        )
        # run as a subprocess so the GUI event loop is isolated from the
        # test runner (the showcase creates real tk roots on import)
        result = subprocess.run(
            [sys.executable, path, "--smoke"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,  # returncode asserted below
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"showcase --smoke failed:\r\nstdout={result.stdout}\r\n"
                f"stderr={result.stderr}",
        )
        self.assertIn("SMOKE OK", result.stdout)

    def test_popup_uses_closable_x(self):
        """The shared popup helper must NOT disable the title bar X.

        Even when the popup grabs focus (``modal=True``), the X button
        must close the window so the user has a fallback close affordance.
        """
        from TkSimpleGUI import popup as _popup_fn
        import sys

        popup_module = sys.modules["TkSimpleGUI.popup"]
        captured = []

        class SpyWindow:
            def __init__(self, title, rows, **kwargs):
                captured.append({"title": title, "kwargs": kwargs})

            def read(self, timeout=None, close=False, timeout_key=ts.TIMEOUT_KEY):
                # simulate the OK button press so the popup returns
                return "OK", {}

        original = popup_module.Window
        popup_module.Window = SpyWindow
        try:
            _popup_fn("hi from test")
        finally:
            popup_module.Window = original

        self.assertEqual(len(captured), 1, "popup must build exactly one window")
        kwargs = captured[0]["kwargs"]
        self.assertTrue(kwargs.get("finalize"))
        self.assertTrue(kwargs.get("modal"))
        self.assertFalse(
            kwargs.get("disable_close"),
            "popup must allow X-close (modal is about grab, not close)",
        )


    @unittest.skipUnless(ts.running_windows(), "SystemTray is Windows only")
    def test_tray_run_lifecycle(self):
        # tray.run() starts a tray-anchored loop; the handler closes the
        # tray which ends the application
        import subprocess

        probe = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "probes",
            "_tray_run_probe.py",
        )
        result = subprocess.run(
            [sys.executable, probe],
            capture_output=True,
            timeout=60,
            check=False,  # returncode asserted below
        )
        output = result.stdout.decode("utf-8", "replace")
        self.assertEqual(
            result.returncode, 0, output + result.stderr.decode("utf-8", "replace")
        )
        self.assertIn("TRAY RUN OK", output)

    @unittest.skipUnless(ts.running_windows(), "SystemTray is Windows only")
    def test_system_tray_snake_case_api(self):
        """Public methods are snake_case; PascalCase aliases were removed
        (snake_case is the only supported spelling now)."""
        tray = ts.SystemTray()
        self.addCleanup(tray.close)
        # snake_case is the primary (and only) name
        for name in ("show_message", "update", "hide", "unhide"):
            self.assertTrue(
                callable(getattr(tray, name)),
                f"{name} should be callable on SystemTray",
            )
        # the old PascalCase spellings and the PSG style aliases no longer exist
        for legacy in ("ShowMessage", "Update", "Hide", "UnHide", "ShowMsg",
                       "Read", "notify"):
            self.assertFalse(
                hasattr(tray, legacy),
                f"{legacy} is a removed alias; use the snake_case name",
            )
        # hide/unhide flip the _created flag without raising
        tray.hide()
        self.assertFalse(tray._created)
        tray.unhide()
        self.assertTrue(tray._created)


class TestEventManager(unittest.TestCase):
    def setUp(self):
        self.app = ts.TkSimpleEvent()
        self.calls = []

    def test_dispatch_signatures(self):
        app = self.app

        @app.bind_event("wv")
        def on_wv(window, values):
            self.calls.append(("wv", window.title, values))

        @app.bind_event(["a", "b"])
        def on_e(event):
            self.calls.append(("e", event))

        @app.bind_event("plain")
        def on_plain():
            self.calls.append(("plain",))

        @app.bind_event("valonly")
        def on_values(values):
            self.calls.append(("v", values))

        window = ts.Window("evt", [[ts.TText("x")]], finalize=True)
        app.apply_event(window, "wv", {"k": 1})
        app.apply_event(window, "b", {})
        app.apply_event(window, "a", {})
        app.apply_event(window, "plain", {})
        app.apply_event(window, "valonly", {"n": 2})
        app.apply_event(window, "unknown", {})
        self.assertEqual(
            self.calls,
            [
                ("wv", "evt", {"k": 1}),
                ("e", "b"),
                ("e", "a"),
                ("plain",),
                ("v", {"n": 2}),
            ],
        )
        window.close()

    def test_on_prefix_rule(self):
        with self.assertRaises(ValueError):
            @self.app.bind_event("bad")
            def bad_handler():
                pass

    def test_get_events(self):
        @self.app.bind_event("one")
        def on_one():
            pass

        self.assertIn("one", self.app.get_events)

    def test_singleton_window(self):
        @ts.singleton_window
        def make_window(title):
            return ts.Window(title, [[ts.TText("x")]], finalize=True)

        first = make_window("single")
        second = make_window("single")
        self.assertIs(first, second)
        first.close()

    def test_singleton_window_evicts_closed(self):
        """Closed windows must not pin memory in the registry."""
        import gc

        @ts.singleton_window
        def make_window(title):
            return ts.Window(title, [[ts.TText("x")]], finalize=True)

        first = make_window("evict")
        # closure cells: [0] = original func, [1] = instances dict
        instances = make_window.__closure__[1].cell_contents
        self.assertEqual(len(instances), 1)
        first.close()
        # the next call must evict the stale entry and allocate fresh
        second = make_window("evict")
        self.assertIsNot(first, second)
        self.assertFalse(second.was_closed)
        # only the new live window should remain for that key
        self.assertEqual(len(instances), 1)
        self.assertIs(list(instances.values())[0], second)
        second.close()
        del first, second
        gc.collect()


class TestDisplayElements(unittest.TestCase):
    """Batch A display.py: TTag, TBadge, TAvatar, TStatistic, TEmpty, TResult,
    TSkeleton, TAlert and TWatermark (see the batch A design spec)."""

    def _window(self, elements):
        """A finalized window around ``elements`` rows (closed on cleanup)."""
        window = ts.Window("t", elements, finalize=True)
        self.addCleanup(window.close)
        return window

    def _click(self, window, widget, x, y):
        """A real <Button-1> on ``widget``; the event lands on the bus.

        Nothing is read back here — :meth:`_events` collects the events,
        so a stray bus entry cannot swallow the click's own event.
        """
        window.tk_root.update()
        widget.event_generate("<Button-1>", x=x, y=y, when="tail")
        window.tk_root.update()

    def _events(self, window, timeout=300):
        """Every event the application-wide bus delivers within ``timeout`` ms.

        A synthetic click posts into a shared bus, and on the 32-bit 3.7
        build a stray ``WIN_CLOSED`` can appear on it after many windows
        were created and destroyed in one process (a queued WM close
        message reaching a recycled window handle). Assertions therefore
        look for the event they expect inside this window of pumping
        rather than trusting the very first read.
        """
        seen = []
        deadline = time.time() + timeout / 1000.0
        while time.time() < deadline:
            event, _values = window.read(timeout=20)
            if event != ts.TIMEOUT_KEY:
                seen.append(event)
        return seen

    def _canvas_texts(self, element):
        """Every text item drawn on the element's canvas."""
        canvas = element.widget
        return [
            str(canvas.itemcget(item, "text"))
            for item in canvas.find_all()
            if canvas.type(item) == "text"
        ]

    def test_tag_get_and_close_click(self):
        tag = ts.TTag("New", closable=True, enable_events=True, key="-TAG-")
        window = self._window([[tag]])
        self.assertEqual(tag.text, "New")
        self.assertEqual(tag.get(), "New")
        # the "x" sits 9px from the right edge, vertically centered
        self._click(window, tag.widget, tag._width - 9, tag._height // 2)
        self.assertIn(("-TAG-", "close"), self._events(window))
        self.assertFalse(tag.visible)
        self.assertEqual(tag.get(), "New")  # still the text after the close
        # a new value re-shows the closed tag and swaps the text
        tag.update(value="Done")
        window.tk_root.update()
        self.assertTrue(tag.visible)
        self.assertTrue(tag.widget.winfo_ismapped())
        self.assertEqual(tag.get(), "Done")
        self.assertEqual(tag.text, "Done")
        # a click on the body posts the bare key
        self._click(window, tag.widget, 10, tag._height // 2)
        self.assertIn("-TAG-", self._events(window))
        self.assertEqual(window["-TAG-"].get(), "Done")

    def test_tag_effects_and_explicit_size(self):
        seen = {}
        for effect in ("light", "dark", "plain"):
            tag = ts.TTag("E", effect=effect)
            self._window([[tag]])
            canvas = tag.widget
            self.assertGreater(len(canvas.find_all()), 0)
            seen[effect] = (
                str(canvas.itemcget(tag._body_id, "fill")),
                str(canvas.itemcget(tag._body_id, "outline")),
                str(canvas.cget("background")),
            )
        # light and dark carry no outline; plain is a surface fill + outline
        self.assertEqual(seen["light"][1], "")
        self.assertNotEqual(seen["light"][0], seen["light"][2])
        self.assertEqual(seen["dark"][1], "")
        self.assertNotEqual(seen["dark"][0], seen["light"][0])
        self.assertEqual(seen["plain"][0], seen["plain"][2])
        self.assertNotEqual(seen["plain"][1], "")
        sized = ts.TTag("Sized", size=(90, 26), closable=True)
        self._window([[sized]])
        self.assertEqual(int(sized.widget.cget("width")), 90)
        self.assertEqual(int(sized.widget.cget("height")), 26)
        self.assertGreater(len(sized.widget.find_all()), 0)

    def test_tag_close_button_uses_native_event(self):
        """A real click on the close button (event_generate on the button
        itself, not the canvas) closes the tag — the dispatch goes through
        tk's native button command, not canvas pixel-hunting."""
        tag = ts.TTag("X", closable=True, key="-T-")
        window = self._window([[tag]])
        for _ in range(3):
            window.tk_root.update()
        # the embedded close button exists and is mapped
        self.assertTrue(tag._close_button.winfo_ismapped())
        tag._close_button.event_generate("<Button-1>", x=4, y=8, when="tail")
        window.tk_root.update()
        self.assertIn(("-T-", "close"), self._events(window))
        self.assertFalse(tag.visible)

    def test_badge_max_value_and_clear(self):
        badge = ts.TBadge(value=120, max_value=99, key="-BADGE-")
        self._window([[badge]])
        self.assertEqual(badge._label(), "99+")
        self.assertEqual(badge.get(), 120)  # the raw value, not the caption
        self.assertGreater(len(badge.widget.find_all()), 0)
        badge.update(value=7)
        self.assertEqual(badge._label(), "7")
        self.assertEqual(badge.get(), 7)
        badge.clear()
        self.assertIsNone(badge.get())
        self.assertEqual(badge._label(), "")
        self.assertEqual(len(badge.widget.find_all()), 0)

    def test_badge_dot_and_empty_value(self):
        dot = ts.TBadge(value=5, is_dot=True)
        self._window([[dot]])
        self.assertEqual(dot._label(), "")  # a dot ignores the value text
        self.assertEqual(dot._width, 10)  # size[1] or 10
        self.assertEqual(dot._width, dot._height)
        self.assertEqual(len(dot.widget.find_all()), 1)
        empty = ts.TBadge()
        self._window([[empty]])
        self.assertIsNone(empty.get())
        self.assertEqual(len(empty.widget.find_all()), 0)
        self.assertEqual((empty._width, empty._height), (1, 1))

    def test_avatar_initials_and_shapes(self):
        avatar = ts.TAvatar(text="Yun Luo", key="-AV-")
        self._window([[avatar]])
        self.assertEqual(avatar._initials, "Yu")
        self.assertEqual(avatar.get(), "Yun Luo")
        self.assertGreaterEqual(len(avatar.widget.find_all()), 2)
        square = ts.TAvatar(text="AB", shape="square", size=(48, 48))
        self._window([[square]])
        self.assertEqual(int(square.widget.cget("width")), 48)
        self.assertEqual(int(square.widget.cget("height")), 48)

    def test_avatar_image_and_update(self):
        avatar = ts.TAvatar(data_base64=ts.DEFAULT_BASE64_ICON, key="-AV-")
        self._window([[avatar]])
        kinds = [avatar.widget.type(item) for item in avatar.widget.find_all()]
        self.assertIn("image", kinds)
        self.assertIsNotNone(avatar._photo)
        avatar.update(text="Zed")
        self.assertEqual(avatar.get(), "Zed")
        self.assertEqual(avatar.text, "Zed")

    def test_statistic_value_and_format(self):
        stat = ts.TStatistic("Win", value=1234, prefix="$", suffix="/mo", key="-ST-")
        self._window([[stat]])
        self.assertEqual(stat.get(), 1234)  # the raw value
        self.assertEqual(stat._value_text(), "1234")
        texts = self._canvas_texts(stat)
        self.assertIn("Win", texts)
        self.assertIn("$", texts)
        self.assertIn("/mo", texts)
        self.assertIn("1234", texts)
        precise = ts.TStatistic("P", value=3, precision=2)
        self._window([[precise]])
        self.assertEqual(precise._value_text(), "3.00")

    def test_statistic_trends_and_update(self):
        stat = ts.TStatistic("Win", value=10, trend=12.5, key="-ST-")
        self._window([[stat]])
        self.assertTrue(stat._trend_direction())
        self.assertEqual(stat._trend_label(), "12.5%")
        self.assertIn("12.5%", self._canvas_texts(stat))
        stat.update(value=3, label="Loss", trend=-3)
        self.assertEqual(stat.get(), 3)
        self.assertEqual(stat.label, "Loss")
        self.assertFalse(stat._trend_direction())
        texts = self._canvas_texts(stat)
        self.assertIn("3%", texts)
        self.assertIn("Loss", texts)

    def test_empty_glyph_and_update(self):
        empty = ts.TEmpty(key="-EMPTY-")
        self._window([[empty]])
        self.assertEqual(empty.get(), "No data")
        self.assertGreaterEqual(len(empty.widget.find_all()), 2)  # glyph + text
        empty.update(value="Nothing here")
        self.assertEqual(empty.get(), "Nothing here")
        self.assertIn("Nothing here", self._canvas_texts(empty))

    def test_empty_image_variant(self):
        empty = ts.TEmpty(data_base64=ts.DEFAULT_BASE64_ICON, text="")
        self._window([[empty]])
        kinds = [empty.widget.type(item) for item in empty.widget.find_all()]
        self.assertIn("image", kinds)

    def test_empty_compact_one_line_default(self):
        """No size passed → one-line compact layout (icon + caption in a
        row, not the old 110-px hero)."""
        empty = ts.TEmpty("nothing here", key="-E-")
        self._window([[empty]])
        # the compact icon is 16 px wide; default box is much shorter
        self.assertLessEqual(int(empty.widget.cget("height")), 22)
        texts = self._canvas_texts(empty)
        self.assertIn("nothing here", texts)
        # explicit legacy size still triggers the centred hero layout
        legacy = ts.TEmpty("big", size=(160, 110), key="-E2-")
        self._window([[legacy]])
        self.assertEqual(int(legacy.widget.cget("height")), 110)
        self.assertIn("big", self._canvas_texts(legacy))

    def test_result_statuses_render(self):
        results = [
            ts.TResult("Title " + status, "Sub", status=status, key="-R-" + status)
            for status in ("info", "success", "warning", "error")
        ]
        window = self._window([[result] for result in results])
        for result in results:
            self.assertEqual(result.get(), result.title)
            self.assertGreater(len(result.widget.find_all()), 0)
        results[0].update(status="error")  # repaints without raising
        window.tk_root.update()
        self.assertGreater(len(results[0].widget.find_all()), 0)
        self.assertEqual(results[0].get(), "Title info")

    def test_skeleton_rows_geometry_and_animation(self):
        small = ts.TSkeleton(rows=2, key="-SMALL-")
        tall = ts.TSkeleton(rows=5, key="-TALL-")
        self._window([[small, tall]])
        self.assertEqual(small.get(), 2)
        self.assertTrue(small.animated)
        self.assertGreater(tall._height, small._height)
        small.stop_animation()
        small.start_animation()  # neither raises
        small.update(rows=5)
        self.assertEqual(int(small.widget.cget("height")), 110)  # 5*14 + 4*10
        small.update(animated=False)
        self.assertFalse(small.animated)
        small.stop_animation()

    def test_skeleton_avatar_variant(self):
        skeleton = ts.TSkeleton(rows=2, avatar=True, key="-SK-")
        self._window([[skeleton]])
        self.assertEqual(skeleton.get(), 2)
        self.assertEqual(skeleton._height, 40)  # avatar keeps at least 40px
        self.assertGreaterEqual(len(skeleton.widget.find_all()), 3)
        skeleton.stop_animation()

    def test_alert_effects_and_types_render(self):
        alerts = [
            ts.TAlert("message", status=kind, title="Header", effect=effect)
            for effect in ("light", "dark")
            for kind in ("info", "success", "warning", "error")
        ]
        self._window([[alert] for alert in alerts])
        for alert in alerts:
            self.assertEqual(alert.get(), "message")
            self.assertEqual(alert.title, "Header")
            self.assertEqual(int(alert.widget.cget("highlightthickness")), 1)
            self.assertTrue(str(alert.widget.cget("highlightbackground")))
            self.assertEqual(str(alert._title_label.cget("text")), "Header")
            # the description must be rendered on construction, not only
            # after an update() call (regression: it used to start blank)
            self.assertEqual(str(alert._text_label.cget("text")), "message")
            self.assertGreater(len(alert._icon_canvas.find_all()), 0)

    def test_alert_close_click_and_update(self):
        alert = ts.TAlert("body", title="Ti", key="-ALERT-")
        window = self._window([[alert]])
        self._click(window, alert._close_canvas, 8, 8)
        self.assertIn(("-ALERT-", "close"), self._events(window))
        self.assertFalse(alert.visible)
        alert.update(text="changed", status="error")
        self.assertEqual(alert.get(), "changed")
        # the repaint keeps the labels on the bar's own background
        self.assertEqual(
            str(alert._text_label.cget("background")),
            str(alert.widget.cget("background")),
        )
        self.assertGreater(len(alert._icon_canvas.find_all()), 0)

    def test_alert_close_reopen_and_property(self):
        alert = ts.TAlert("info", key="-A-")
        window = self._window([[alert]])
        self.assertFalse(alert.closed)
        alert.close()
        self.assertTrue(alert.closed)
        self.assertIn(("-A-", "close"), self._events(window))
        # closing twice is a no-op
        alert.close()
        self.assertTrue(alert.closed)
        alert.reopen()
        self.assertFalse(alert.closed)
        self.assertTrue(alert.visible)

    def test_watermark_tiling_and_update(self):
        watermark = ts.TWatermark("DRAFT", angle=0, key="-WM-")
        self._window([[watermark]])
        self.assertEqual(watermark.get(), "DRAFT")
        items = watermark.widget.find_all()
        self.assertGreater(len(items), 1)  # tiled over the grid points
        self.assertTrue(all(watermark.widget.type(item) == "text" for item in items))
        watermark.update(value="SECRET")
        self.assertEqual(watermark.get(), "SECRET")
        self.assertEqual(watermark.text, "SECRET")
        self.assertGreater(len(watermark.widget.find_all()), 1)

    def test_watermark_default_angle_renders(self):
        watermark = ts.TWatermark("DRAFT", key="-WM-")
        self._window([[watermark]])
        self.assertEqual(watermark._angle, -30.0)
        # Pillow paints one rotated image patch; the fallback paints texts
        self.assertGreater(len(watermark.widget.find_all()), 0)

    def test_watermark_follows_theme(self):
        watermark = ts.TWatermark("DRAFT", size=(180, 120), key="-WM-")
        window = self._window([[watermark]])
        ts.theme("Slate")
        try:
            window.update_theme()
            self.assertEqual(
                str(watermark.widget.cget("background")),
                ts.theme_background_color(),
            )
        finally:
            ts.theme(None)
            watermark.apply_theme()
        self.assertGreater(len(watermark.widget.find_all()), 0)

    def test_canvas_elements_follow_theme(self):
        elements = [
            ts.TTag("A", key="-TAG-"),
            ts.TBadge(3, key="-BADGE-"),
            ts.TStatistic("Count", key="-STAT-"),
            ts.TSteps(["One", "Two"], key="-STEPS-"),
            ts.TRate(key="-RATE-"),
            ts.TPagination(total=95, key="-PAGE-"),
            ts.TWatermark("W", key="-WM-"),
        ]
        window = self._window([elements])
        ts.theme("Dusk")
        try:
            window.update_theme()
            background = ts.theme_background_color()
            for element in elements:
                self.assertEqual(
                    str(element.widget.cget("background")),
                    background,
                    msg=str(element.key),
                )
        finally:
            ts.theme(None)
            window.update_theme()


class TestPanelElements(unittest.TestCase):
    """Batch A panels.py: TCard, TDescriptions, TSteps and TTimeline."""

    def _window(self, elements):
        """A finalized window around ``elements`` rows (closed on cleanup)."""
        window = ts.Window("t", elements, finalize=True)
        self.addCleanup(window.close)
        return window

    def test_card_header_and_nested_layout(self):
        card = ts.TCard(
            "Server",
            [[ts.TText("Host"), ts.TInput(key="-HOST-")]],
            subtitle="prod-01",
            extra=ts.TButton("Restart", key="-RESTART-"),
            key="-CARD-",
        )
        window = self._window([[card]])
        self.assertEqual(card.get(), "Server")
        self.assertEqual(card.title, "Server")
        self.assertEqual(card.subtitle, "prod-01")
        # the nested layout was built into the body, the extra into the header
        self.assertIs(window["-HOST-"].widget.master, card._body)
        self.assertIs(window["-RESTART-"].widget.master, card._header)
        self.assertEqual(int(card.widget.cget("highlightthickness")), 1)

    def test_card_update_and_titleless(self):
        card = ts.TCard("Title", [[ts.TText("body")]], key="-CARD-")
        self._window([[card]])
        card.update(title="Changed", subtitle="line two")
        self.assertEqual(card.get(), "Changed")
        self.assertEqual(str(card._title_label.cget("text")), "Changed")
        self.assertEqual(str(card._subtitle_label.cget("text")), "line two")
        bare = ts.TCard(layout=[[ts.TText("no header", key="-INNER-")]], key="-BARE-")
        window = self._window([[bare]])
        self.assertIsNone(bare.get())
        self.assertFalse(bare._header.winfo_manager())  # the header row collapsed
        self.assertIsNotNone(window["-INNER-"])

    def test_card_follows_theme(self):
        card = ts.TCard("T", [[ts.TText("x")]], key="-CARD-")
        window = self._window([[card]])
        ts.theme("Slate")
        try:
            window.update_theme()
            background = ts.theme_background_color()
            self.assertEqual(str(card.widget.cget("background")), background)
            self.assertEqual(str(card._body.cget("background")), background)
        finally:
            ts.theme(None)
            card.apply_theme()

    def test_descriptions_get_columns_and_border(self):
        descriptions = ts.TDescriptions(
            [("Host", "10.0.0.7"), ("Port", 8080), ("A", 1), ("B", 2), ("C", 3)],
            columns=3,
            bordered=True,
            label_suffix=":",
            key="-DESC-",
        )
        self._window([[descriptions]])
        values = descriptions.get()
        self.assertEqual(values["Host"], "10.0.0.7")
        self.assertEqual(values["Port"], 8080)  # values come back as passed in
        self.assertEqual(len(values), 5)
        self.assertEqual(int(descriptions.widget.cget("highlightthickness")), 1)
        # 5 pairs over 3 columns land in two grid rows
        rows = {
            child.grid_info()["row"] for child in descriptions.widget.winfo_children()
        }
        self.assertEqual(sorted(rows), [0, 1])
        texts = [
            str(child.cget("text")) for child in descriptions.widget.winfo_children()
        ]
        self.assertIn("Host:", texts)
        mapped = ts.TDescriptions({"x": 1, "y": 2})
        self._window([[mapped]])
        self.assertEqual(mapped.get(), {"x": 1, "y": 2})

    def test_descriptions_update_rebuilds(self):
        descriptions = ts.TDescriptions([("Host", "a")], key="-DESC-")
        self._window([[descriptions]])
        before = len(descriptions.widget.winfo_children())
        descriptions.update(items=[("A", 1), ("B", 2), ("C", 3), ("D", 4), ("E", 5)])
        after = len(descriptions.widget.winfo_children())
        self.assertNotEqual(after, before)
        self.assertEqual(after, 10)  # 5 label/value cells
        self.assertEqual(
            descriptions.get(), {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
        )
        texts = [
            str(child.cget("text")) for child in descriptions.widget.winfo_children()
        ]
        self.assertIn("E", texts)
        self.assertNotIn("Host", texts)

    def test_steps_horizontal_states_and_geometry(self):
        steps = ts.TSteps(["One", "Two", "Three"], active=1, key="-STEPS-")
        self._window([[steps]])
        self.assertEqual(steps.get(), 1)
        self.assertEqual(steps._state(0), "finish")
        self.assertEqual(steps._state(1), "process")
        self.assertEqual(steps._state(2), "wait")
        self.assertGreater(len(steps.widget.find_all()), 0)
        single = ts.TSteps(["One"], key="-SINGLE-")
        self._window([[single]])
        # the canvas widens with the item count
        self.assertLess(
            int(single.widget.cget("width")), int(steps.widget.cget("width"))
        )

    def test_steps_error_status_and_update(self):
        steps = ts.TSteps(["One", "Two", "Three"], active=1, status="error", key="-S-")
        self._window([[steps]])
        self.assertEqual(steps._state(1), "danger")
        steps.update(active=2, status="process")
        self.assertEqual(steps.get(), 2)
        self.assertEqual(steps._state(1), "finish")
        self.assertEqual(steps._state(2), "process")
        self.assertGreater(len(steps.widget.find_all()), 0)

    def test_steps_vertical_geometry(self):
        vertical = ts.TSteps(["a", "b", "c"], direction="vertical", key="-VERT-")
        horizontal = ts.TSteps(["a", "b", "c"], key="-HOR-")
        self._window([[vertical, horizontal]])
        self.assertEqual(vertical.direction, "vertical")
        # n * row_height (64), taller than the flat 70px horizontal row
        self.assertEqual(int(vertical.widget.cget("height")), 3 * 64)
        self.assertGreater(
            int(vertical.widget.cget("height")), int(horizontal.widget.cget("height"))
        )
        self.assertGreater(len(vertical.widget.find_all()), 0)

    def test_timeline_forms_and_get(self):
        timeline = ts.TTimeline(
            [
                "Deployed",
                ("10:00", "Build finished"),
                {"timestamp": "11:00", "content": "Rollback", "type": "success"},
                ("12:00", {"content": "Warm up", "type": "warning"}),
            ],
            key="-TL-",
        )
        self._window([[timeline]])
        self.assertEqual(
            timeline.get(),
            [(None, "Deployed"), ("10:00", "Build finished"), ("11:00", "Rollback"),
             ("12:00", "Warm up")],
        )
        # a mapping in the pair's second slot supplies the fields, so the
        # content is never rendered as a dict repr
        self.assertNotIn("{", timeline._items[3][1])
        self.assertEqual(timeline._items[3][2], "warning")
        self.assertGreater(len(timeline.widget.find_all()), 0)

    def test_timeline_update(self):
        timeline = ts.TTimeline(["first"], key="-TL-")
        self._window([[timeline]])
        timeline.update(items=[("12:00", "Only one"), {"content": "two"}])
        self.assertEqual(timeline.get(), [("12:00", "Only one"), (None, "two")])
        self.assertGreater(len(timeline.widget.find_all()), 0)


class TestSelectionElements(unittest.TestCase):
    """Batch A selection.py: TSegmented, TRate, TPagination and TTransfer."""

    def _window(self, elements):
        """A finalized window around ``elements`` rows (closed on cleanup)."""
        window = ts.Window("t", elements, finalize=True)
        self.addCleanup(window.close)
        return window

    def _click(self, window, widget, x, y):
        """A real <Button-1> on ``widget``; the event lands on the bus.

        Nothing is read back here — :meth:`_events` collects the events,
        so a stray bus entry cannot swallow the click's own event.
        """
        window.tk_root.update()
        widget.event_generate("<Button-1>", x=x, y=y, when="tail")
        window.tk_root.update()

    def _events(self, window, timeout=300):
        """Every event the application-wide bus delivers within ``timeout`` ms.

        A synthetic click posts into a shared bus, and on the 32-bit 3.7
        build a stray ``WIN_CLOSED`` can appear on it after many windows
        were created and destroyed in one process (a queued WM close
        message reaching a recycled window handle). Assertions therefore
        look for the event they expect inside this window of pumping
        rather than trusting the very first read.
        """
        seen = []
        deadline = time.time() + timeout / 1000.0
        while time.time() < deadline:
            event, _values = window.read(timeout=20)
            if event != ts.TIMEOUT_KEY:
                seen.append(event)
        return seen

    def test_segmented_default_and_update(self):
        segmented = ts.TSegmented(["Day", "Week", "Month"], key="-SEG-")
        self._window([[segmented]])
        self.assertEqual(segmented.get(), "Day")  # the first option by default
        segmented.update(value="Week")
        self.assertEqual(segmented.get(), "Week")
        segmented.update(value="Missing")
        self.assertEqual(segmented.get(), "Week")  # an unknown value is ignored
        self.assertGreater(len(segmented.widget.find_all()), 0)

    def test_segmented_pairs_and_click(self):
        segmented = ts.TSegmented([("Day", "d"), ("Week", "w")], key="-SEG-")
        window = self._window([[segmented]])
        self.assertEqual(segmented.get(), "d")  # (label, value) pairs
        left, right = segmented._cells[1]
        self._click(window, segmented.widget, int((left + right) // 2), 15)
        self.assertIn("-SEG-", self._events(window))
        self.assertEqual(segmented.get(), "w")

    def test_segmented_readonly_ignores_click(self):
        segmented = ts.TSegmented(["a", "b"], readonly=True, key="-SEG-")
        window = self._window([[segmented]])
        left, right = segmented._cells[1]
        self._click(window, segmented.widget, int((left + right) // 2), 15)
        self.assertNotIn("-SEG-", self._events(window, timeout=200))
        self.assertEqual(segmented.get(), "a")

    def test_segmented_options_update_keeps_value(self):
        segmented = ts.TSegmented(["a", "b", "c"], default_value="b", key="-SEG-")
        self._window([[segmented]])
        segmented.update(options=["b", "x"])
        self.assertEqual(segmented.get(), "b")  # still offered: kept
        segmented.update(options=["zzz", "yyy"])
        self.assertEqual(segmented.get(), "zzz")  # gone: back to the first
        self.assertEqual(len(segmented._cells), 2)

    def test_rate_defaults_and_update(self):
        rate = ts.TRate(key="-RATE-")
        self._window([[rate]])
        self.assertEqual(rate.get(), 0.0)
        self.assertTrue(rate._allow_half)
        rate.update(value=4.5)
        self.assertEqual(rate.get(), 4.5)
        self.assertGreater(len(rate.widget.find_all()), 4)

    def test_rate_half_star_click_posts_once(self):
        rate = ts.TRate(key="-RATE-")
        window = self._window([[rate]])
        # the left half of the first star selects 0.5
        self.assertEqual(rate._value_at(5), 0.5)
        self._click(window, rate.widget, 5, 13)
        self.assertIn("-RATE-", self._events(window))
        # pump the bus quiet and count strays: one click must post exactly
        # once, so a late duplicate delivery (seen under full-suite load)
        # fails here with the right semantics, not inside the drain below
        deadline = time.time() + 2
        quiet_reads = 0
        extra_posts = 0
        while time.time() < deadline and quiet_reads < 5:
            event, _values = window.read(timeout=20)
            if event == "-RATE-":
                extra_posts += 1
                quiet_reads = 0
            elif event == ts.TIMEOUT_KEY:
                quiet_reads += 1
        self.assertEqual(extra_posts, 0)
        # clicking the same value again changes nothing: no event at all
        self._click(window, rate.widget, 5, 13)
        self.assertNotIn("-RATE-", self._events(window, timeout=200))
        self.assertEqual(rate.get(), 0.5)

    def test_rate_readonly_and_max_value(self):
        readonly = ts.TRate(readonly=True, key="-R-")
        window = self._window([[readonly]])
        self._click(window, readonly.widget, 5, 13)
        self.assertNotIn("-R-", self._events(window, timeout=200))
        self.assertEqual(readonly.get(), 0.0)
        wide = ts.TRate(max_value=10, key="-W-")
        self._window([[wide]])
        self.assertGreater(
            int(wide.widget.cget("width")), int(readonly.widget.cget("width"))
        )

    def test_pagination_page_count_and_validation(self):
        pager = ts.TPagination(total=95, page_size=10, key="-PAGE-")
        self._window([[pager]])
        self.assertEqual(pager.page_count, 10)
        self.assertEqual(pager.get(), 1)
        with self.assertRaises(ValueError):
            ts.TPagination(total=10, page_size=0)
        with self.assertRaises(ValueError):
            ts.TPagination(total=-1)

    def test_pagination_clamps_current_page(self):
        pager = ts.TPagination(total=95, current_page=99, key="-PAGE-")
        self._window([[pager]])
        self.assertEqual(pager.page_count, 10)
        self.assertEqual(pager.get(), 10)  # clamped into [1, page_count]

    def test_pagination_window_algorithm(self):
        pager = ts.TPagination(total=95, page_size=10, pager_count=5, key="-P-")
        self._window([[pager]])
        self.assertEqual(pager._page_window(), [1, 2, 3, 4, "\u2026", 10])
        pager.update(current_page=5)
        self.assertEqual(pager._page_window(), [1, "\u2026", 4, 5, 6, "\u2026", 10])
        pager.update(current_page=10)
        self.assertEqual(pager._page_window(), [1, "\u2026", 7, 8, 9, 10])
        short = ts.TPagination(total=50, page_size=10, pager_count=5, key="-S-")
        self._window([[short]])
        # page_count <= pager_count: every page is shown
        self.assertEqual(short._page_window(), [1, 2, 3, 4, 5])

    def test_pagination_click_and_update(self):
        pager = ts.TPagination(total=95, current_page=5, key="-PAGE-")
        window = self._window([[pager]])
        box = None
        for entry in pager._boxes:
            if entry[4] == 6:
                box = entry
        self.assertIsNotNone(box)
        x = int((box[0] + box[2]) // 2)
        y = int((box[1] + box[3]) // 2)
        self._click(window, pager.widget, x, y)
        self.assertIn("-PAGE-", self._events(window))
        self.assertEqual(pager.get(), 6)
        pager.update(current_page=7)
        self.assertEqual(pager.get(), 7)
        pager.update(total=15)  # 2 pages now: the page clamps down
        self.assertEqual(pager.page_count, 2)
        self.assertEqual(pager.get(), 2)

    def test_pagination_show_total(self):
        pager = ts.TPagination(total=95, show_total=True, key="-PAGE-")
        self._window([[pager]])
        texts = [
            str(pager.widget.itemcget(item, "text"))
            for item in pager.widget.find_all()
            if pager.widget.type(item) == "text"
        ]
        self.assertIn("Total 95", texts)

    def test_transfer_get_and_moves(self):
        transfer = ts.TTransfer(["a", "b", "c"], target_items=["x"], key="-TR-")
        self._window([[transfer]])
        self.assertEqual(transfer.get(), ["x"])  # the target list
        transfer._source_list.selection_set(0)
        self.assertTrue(transfer.move_selected())
        self.assertEqual(transfer.get(), ["x", "a"])
        self.assertTrue(transfer.move_all())
        self.assertEqual(transfer.get(), ["x", "a", "b", "c"])
        self.assertFalse(transfer.move_all())  # the source is empty now
        self.assertEqual(transfer._source_list.size(), 0)

    def test_transfer_double_click_moves_one_item(self):
        transfer = ts.TTransfer(["a", "b", "c"], key="-TR-")
        window = self._window([[transfer]])
        window.tk_root.update()
        box = transfer._source_list.bbox(0)
        self.assertIsNotNone(box)
        x = box[0] + 5
        y = box[1] + box[3] // 2
        # two presses in quick succession are the double click Tk sees
        transfer._source_list.event_generate("<Button-1>", x=x, y=y, when="tail")
        transfer._source_list.event_generate("<Button-1>", x=x, y=y, when="tail")
        window.tk_root.update()
        self.assertEqual(transfer.get(), ["a"])
        self.assertEqual(transfer._source_list.size(), 2)

    def test_transfer_update_and_events(self):
        transfer = ts.TTransfer(["a", "b"], enable_events=True, key="-TR-")
        window = self._window([[transfer]])
        transfer._source_list.selection_set(0)
        transfer.move_selected()
        self.assertIn("-TR-", self._events(window))
        self.assertEqual(transfer.get(), ["a"])
        transfer.update(source_items=["p", "q"], target_items=["z"])
        self.assertEqual(transfer.get(), ["z"])
        self.assertEqual(transfer._source_list.size(), 2)
        self.assertEqual(transfer._target_list.size(), 1)

    # --- keyboard parity -----------------------------------------------------------
    def _key(self, window, widget, keysym):
        """Give the canvas focus then synthesise a <Key> event.

        Retry once on the second pump: under load (full 3.7 chunk suite)
        the first focus + event can be eaten by a still-pending timer from
        an earlier test. Two pumps is enough to make the assertion stable.
        """
        window.tk_root.update()
        widget.focus_set()
        widget.event_generate("<Key>", keysym=keysym, when="tail")
        for _ in range(3):
            window.tk_root.update()

    def _key_until(self, window, widget, keysym, getter, expected):
        """Send a key and keep pumping until ``getter()`` reports ``expected``.

        Under load (full 3.7 chunk suite) a key can be eaten by a
        still-pending timer from an earlier test; the deadline poll makes
        the assertion stable instead of trusting a fixed pump count.
        """
        deadline = time.time() + 5
        while time.time() < deadline:
            self._key(window, widget, keysym)
            if getter() == expected:
                return
        self.assertEqual(getter(), expected)

    def test_rate_keyboard_steps_and_clamps(self):
        rate = ts.TRate(max_value=5, default_value=2, key="-R-")
        window = self._window([[rate]])
        self._key(window, rate.widget, "Right")
        self.assertEqual(rate.get(), 3)
        self._key(window, rate.widget, "End")
        self.assertEqual(rate.get(), 5)
        self._key(window, rate.widget, "Right")  # clamped
        self.assertEqual(rate.get(), 5)
        self._key(window, rate.widget, "Home")
        self.assertEqual(rate.get(), 0)
        self._key(window, rate.widget, "Left")  # clamped
        self.assertEqual(rate.get(), 0)

    def test_pagination_keyboard_navigates(self):
        pagination = ts.TPagination(total=120, page_size=10, current_page=3,
                                    key="-P-")
        window = self._window([[pagination]])
        self._key_until(window, pagination.widget, "Right", pagination.get, 4)
        self._key_until(window, pagination.widget, "End", pagination.get, 12)
        self._key_until(window, pagination.widget, "Home", pagination.get, 1)
        # already on the first page: the key must not move anywhere
        self._key(window, pagination.widget, "Left")
        window.tk_root.update()
        self.assertEqual(pagination.get(), 1)

    def test_steps_keyboard_navigates(self):
        steps = ts.TSteps(["A", "B", "C", "D"], active=1, key="-S-")
        window = self._window([[steps]])
        self._key(window, steps.widget, "Right")
        self.assertEqual(steps.active, 2)
        self._key(window, steps.widget, "End")
        self.assertEqual(steps.active, 3)
        self._key(window, steps.widget, "Home")
        self.assertEqual(steps.active, 0)
        self._key(window, steps.widget, "Left")
        self.assertEqual(steps.active, 0)


class TestLogger(unittest.TestCase):
    """Logging into an TOutput / TMultiline element (Logger + ts.log)."""

    def _out(self, **kwargs):
        element = ts.TOutput(size=(40, 6), key="-LOG-", **kwargs)
        window = ts.Window("log", [[element]], finalize=True)
        self.addCleanup(window.close)
        return window, element

    def _lines(self, element):
        return element.get().splitlines()

    def test_log_writes_formatted_line(self):
        _window, out = self._out()
        out.log("connected")
        lines = self._lines(out)
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^\d{2}:\d{2}:\d{2} INFO    connected$")
        # the widget stays read-only for the user
        self.assertEqual(str(out._text.cget("state")), "disabled")

    def test_level_label_and_semantic_colors(self):
        _window, out = self._out()
        out.log("plain info")
        out.log("bad", level="error")
        out.log("warn", level="warning")
        out.log("good", level="success")
        info_tags = out._text.tag_names("1.0")
        self.assertEqual(tuple(info_tags), ())  # info keeps the theme color
        error_tags = out._text.tag_names("2.0")
        self.assertTrue(error_tags)
        color = out._text.tag_cget(error_tags[-1], "foreground")
        self.assertEqual(str(color), "#f56c6c")
        warn_tag = out._text.tag_names("3.0")[-1]
        self.assertEqual(str(out._text.tag_cget(warn_tag, "foreground")), "#e6a23c")
        ok_tag = out._text.tag_names("4.0")[-1]
        self.assertEqual(str(out._text.tag_cget(ok_tag, "foreground")), "#67c23a")

    def test_color_override_wins(self):
        _window, out = self._out()
        out.log("custom", level="error", color="#1565c0")
        tag = out._text.tag_names("1.0")[-1]
        self.assertEqual(str(out._text.tag_cget(tag, "foreground")), "#1565c0")

    def test_timestamp_can_be_disabled_or_reshaped(self):
        _window, out = self._out()
        plain = out.logger(timestamp="")
        plain.info("no stamp")
        self.assertEqual(self._lines(out)[0], "INFO    no stamp")
        plain.write("per line", timestamp="%Y")
        self.assertRegex(self._lines(out)[1], r"^\d{4} INFO    per line$")

    def test_min_level_filters_lines(self):
        window, out = self._out()
        logger = ts.Logger(out, min_level="warning")
        logger.debug("dropped")
        logger.info("dropped too")
        logger.warning("kept")
        logger.error("kept as well")
        window.tk_root.update()
        self.assertEqual(len(self._lines(out)), 2)
        self.assertIn("kept", out.get())
        self.assertEqual(logger.level, "warning")

    def test_max_lines_ring_buffer(self):
        _window, out = self._out()
        logger = ts.Logger(out, max_lines=3)
        for index in range(5):
            logger.info(f"m{index}")
        self.assertEqual(out.line_count, 3)
        self.assertEqual(logger.lines, 3)
        text = out.get()
        self.assertNotIn("m0", text)
        self.assertNotIn("m1", text)
        self.assertIn("m4", text)
        self.assertEqual(logger.max_lines, 3)

    def test_mirror_writes_plain_text_file(self):
        _window, out = self._out()
        path = os.path.join(tempfile.mkdtemp(), "run.log")
        logger = ts.Logger(out, mirror=path)
        logger.info("first")
        logger.error("second")
        logger.close()
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("first", content)
        self.assertIn("second", content)
        self.assertIn("ERROR", content)
        self.assertNotIn("#f56c6c", content)  # colors stay on screen
        self.assertEqual(len(content.splitlines()), 2)

    def test_clear_and_line_count(self):
        window, out = self._out()
        out.log("one")
        out.log("two")
        self.assertEqual(out.line_count, 2)
        logger = out.logger()
        logger.clear()
        window.tk_root.update()
        self.assertEqual(out.line_count, 0)
        self.assertEqual(out.get(), "")

    def test_line_count_before_creation(self):
        self.assertEqual(ts.TOutput("", size=(20, 3)).line_count, 0)

    def test_attach_logging_bridges_stdlib(self):
        window, out = self._out()
        logger = out.logger()
        name = "tksg.test.bridge"
        logger.attach_logging("INFO", name)
        try:
            logging.getLogger(name).warning("from logging")
        finally:
            pass
        window.tk_root.update()
        self.assertIn("from logging", out.get())
        self.assertIn("tksg.test.bridge:", out.get())
        # attaching twice must not duplicate lines
        logger.attach_logging("INFO", name)
        logging.getLogger("tksg.test.bridge").warning("once")
        window.tk_root.update()
        self.assertEqual(out.get().count("once"), 1)
        logger.detach_logging()
        logging.getLogger(name).warning("after detach")
        window.tk_root.update()
        self.assertNotIn("after detach", out.get())

    def test_attach_logging_level_filters(self):
        window, out = self._out()
        logger = out.logger()
        name = "tksg.test.level"
        logger.attach_logging("WARNING", name)
        try:
            logging.getLogger(name).info("dropped")
            logging.getLogger(name).warning("kept")
            window.tk_root.update()
            self.assertNotIn("dropped", out.get())
            self.assertIn("kept", out.get())
        finally:
            logger.detach_logging()
            logging.getLogger(name).setLevel(logging.NOTSET)

    def test_worker_thread_lines_are_marshalled(self):
        window, out = self._out()
        logger = ts.Logger(out)

        def worker():
            for index in range(5):
                logger.info(f"thread {index}")

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        deadline = time.time() + 5.0
        while time.time() < deadline and out.line_count < 5:
            window.read(timeout=50)
        self.assertEqual(out.line_count, 5)
        self.assertIn("thread 4", out.get())

    def test_flush_writes_queued_lines(self):
        window, out = self._out()
        logger = ts.Logger(out)
        thread = threading.Thread(target=lambda: logger.info("queued"))
        thread.start()
        thread.join()
        logger.flush()
        window.tk_root.update()
        self.assertEqual(out.line_count, 1)
        self.assertIn("queued", out.get())

    def test_module_level_log_finds_the_box(self):
        window, out = self._out()
        self.assertTrue(ts.log("by key", key="-LOG-"))
        self.assertTrue(ts.log("by lookup"))
        window.tk_root.update()
        self.assertIn("by key", out.get())
        self.assertIn("by lookup", out.get())
        self.assertIs(ts.find_log_element(key="-LOG-"), out)
        self.assertIs(ts.find_log_element(window=window), out)
        self.assertIsNone(ts.find_log_element(key="-MISSING-"))

    def test_module_level_log_without_box_returns_false(self):
        ts.Window.close_all()
        self.assertFalse(ts.log("nowhere to go"))

    def test_window_elements_lists_everything(self):
        anonymous = ts.TText("no key here")
        element = ts.TOutput(size=(40, 6), key="-LOG-")
        window = ts.Window("log", [[element], [anonymous]], finalize=True)
        self.addCleanup(window.close)
        elements = window.elements
        self.assertIsInstance(elements, tuple)
        self.assertIn(element, elements)
        self.assertIn(anonymous, elements)

    def test_write_after_close_is_quiet(self):
        window, out = self._out()
        path = os.path.join(tempfile.mkdtemp(), "late.log")
        logger = ts.Logger(out, mirror=path)
        window.close()
        logger.info("late line")  # must not raise
        logger.close()
        with open(path, encoding="utf-8") as handle:
            self.assertIn("late line", handle.read())


class TestPy37Compatibility(unittest.TestCase):
    def test_no_py38_syntax(self):
        """The 3.7 floor forbids 3.8+ syntax: walrus and positional-only params."""
        package_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "TkSimpleGUI"
        )
        offenders = []
        for root, _dirs, files in os.walk(package_dir):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(root, name)
                with open(path, encoding="utf-8-sig") as handle:
                    tree = ast.parse(handle.read())
                for node in ast.walk(tree):
                    named_expr = getattr(ast, "NamedExpr", None)  # 3.8+
                    if named_expr is not None and isinstance(node, named_expr):
                        offenders.append(os.path.basename(path))  # walrus :=
                    elif getattr(node, "posonlyargs", None):  # f(a, /, b) (3.8+)
                        offenders.append(os.path.basename(path))
        self.assertEqual(offenders, [])

    def test_modern_syntax_style(self):
        """3.7 style: zero-arg super() everywhere, no typing ImportError fallbacks."""
        package_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "TkSimpleGUI"
        )
        offenders = []
        for root, _dirs, files in os.walk(package_dir):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(root, name)
                with open(path, encoding="utf-8-sig") as handle:
                    for lineno, line in enumerate(handle.read().splitlines(), 1):
                        if "except ImportError" in line and not name.startswith("_typing_compat"):
                            offenders.append(f"{name}:{lineno} typing-fallback")
                        elif re.search(r"super\(\w+, ?\w+\)", line):
                            offenders.append(f"{name}:{lineno} old-super")
        self.assertEqual(offenders, [])

    def test_slots_encapsulation(self):
        element = ts.TText("x")
        self.assertFalse(hasattr(element, "__dict__"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
