#!/usr/bin/env python3
"""TkSimpleGUI OO package test suite (unittest, headless friendly)."""

import ast
import ctypes
import os
import queue
import re
import sys
import time
import tkinter as tk
import unittest
from tkinter import ttk

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import TkSimpleGUI as ts  # noqa: E402


class TestMeta(unittest.TestCase):
    def test_version(self):
        self.assertEqual(ts.__version__, "0.1.0")

    def test_author(self):
        self.assertEqual(ts.__author__, "yunluo")


class TestThemes(unittest.TestCase):
    def test_table_size(self):
        # 5 hand picked themes, see _theme_data.py
        self.assertEqual(len(ts.list_of_look_and_feel_values()), 5)

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
        from TkSimpleGUI._theme_data import LOOK_AND_FEEL_TABLE
        saved = dict(LOOK_AND_FEEL_TABLE)
        try:
            ts.theme_add_new(
                "__TestTheme__", {"BACKGROUND": "#123456", "TEXT": "#ffffff"}
            )
            self.assertIn("__TestTheme__", ts.list_of_look_and_feel_values())
            ts.theme("__TestTheme__")
            self.assertEqual(ts.theme_background_color(), "#123456")
            ts.theme(None)
        finally:
            LOOK_AND_FEEL_TABLE.clear()
            LOOK_AND_FEEL_TABLE.update(saved)

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
        from TkSimpleGUI._theming import theme_manager
        start = theme_manager.theme_version
        ts.theme("Slate")
        after_apply = theme_manager.theme_version
        ts.theme_background_color("#101010")
        after_bg = theme_manager.theme_version
        ts.theme(None)
        self.assertGreater(after_apply, start)
        self.assertGreater(after_bg, after_apply)

    def test_update_theme_repaints_live_window(self):
        """update_theme() repaints an already visible window immediately."""
        window = ts.Window(
            "live",
            [[ts.Text("t", key="-T-")], [ts.Input("i", key="-IN-")],
             [ts.Column([[ts.Text("inner")]], key="-COL-")]],
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
            [[ts.Multiline("m", key="-ML-")],
             [ts.Button("Toggle", toggle=True), ts.Button("Plain")],
             [ts.CheckList(["a", "b"]), ts.Listbox(["x"], key="-LB-")]],
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
            from TkSimpleGUI.elements.buttons import Button
            from TkSimpleGUI.elements.widgets import CheckList
            buttons = [e for e in window._elements if isinstance(e, Button)]
            checklists = [
                e for e in window._elements if isinstance(e, CheckList)
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
            [[ts.Column([[ts.Text("c")]]), ts.Frame("F", [[ts.Text("f")]])],
             [ts.TabGroup([[ts.Tab("T", [[ts.Text("t")]])]])],
             [ts.Canvas(size=(20, 20)), ts.Listbox(["i"]),
              ts.CheckList(["a"]), ts.Calendar()],
             [ts.LabeledEdit("L"), ts.LED(1), ts.RoundButton("R"),
              ts.TextProgressBar(10, current_value=5)]],
            finalize=True,
        )
        window.close()
        self.assertTrue(window.was_closed)

    def test_update_theme_back_to_native_restores(self):
        """A themed window switched back to System returns to native look."""
        window = ts.Window("revert", [[ts.Text("t", key="-T-")]], finalize=True)
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


class TestSettings(unittest.TestCase):
    def test_set_get(self):
        ts.set_options(border_width=7)
        self.assertEqual(ts.get_options()["border_width"], 7)
        ts.set_options(border_width=1)

    def test_validation(self):
        with self.assertRaises(TypeError):
            ts.set_options(no_such=1)


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
            ts.Text("t"),
            ts.Input("d"),
            ts.Combo(["a", "b"]),
            ts.Listbox(["a", "b"]),
            ts.Spin([1, 2, 3]),
            ts.Checkbox("c"),
            ts.Radio("r", group_id=1),
            ts.Slider((0, 10)),
            ts.Multiline("m"),
            ts.Output(),
            ts.ProgressBar(100),
            ts.Button("b"),
            ts.Image(),
            ts.Canvas((50, 50)),
            ts.Graph((100, 100), (0, 0), (10, 10)),
            ts.Frame("f", [[ts.Text("x")]]),
            ts.Column([[ts.Text("y")]]),
            ts.Tab("t", [[ts.Text("z")]]),
            ts.TabGroup([[ts.Tab("t1", [[ts.Text("w")]])]]),
            ts.Table([["a"]], headings=["H"]),
            ts.Tree(headings=["H"]),
            ts.StatusBar("s"),
            ts.VerticalSeparator(),
            ts.HorizontalSeparator(),
            ts.Menu([["&File", ["Open", "Exit"]]]),
        ]
        for element in elements:
            self.assertIsNotNone(element)

    def test_shortcuts(self):
        self.assertIs(ts.InputText, ts.Input)

    def test_t_prefixed_aliases(self):
        """Uniform T-prefix rule: T<Name> is the same class as <Name>."""
        pairs = [
            ("TText", "Text"), ("TInput", "Input"), ("TInputText", "InputText"),
            ("TCombo", "Combo"), ("TOptionMenu", "OptionMenu"),
            ("TListbox", "Listbox"), ("TSpin", "Spin"), ("TCheckbox", "Checkbox"),
            ("TCheckList", "CheckList"), ("TRadio", "Radio"), ("TSlider", "Slider"),
            ("TMultiline", "Multiline"), ("TOutput", "Output"),
            ("TProgressBar", "ProgressBar"), ("TButton", "Button"),
            ("TSubmit", "Submit"), ("TCloseButton", "CloseButton"),
            ("TImage", "Image"), ("TCanvas", "Canvas"), ("TGraph", "Graph"),
            ("TShape", "Shape"), ("TFrame", "Frame"), ("TColumn", "Column"),
            ("TSplitter", "Splitter"), ("TScrollableColumn", "ScrollableColumn"),
            ("TToolbar", "Toolbar"), ("TLabeledEdit", "LabeledEdit"),
            ("TKeyValueEditor", "KeyValueEditor"), ("TFlowPanel", "FlowPanel"),
            ("TCalendar", "Calendar"), ("TTab", "Tab"), ("TTabGroup", "TabGroup"),
            ("TMenu", "Menu"), ("TTable", "Table"), ("TTree", "Tree"),
            ("TStatusBar", "StatusBar"), ("TVerticalSeparator", "VerticalSeparator"),
            ("THorizontalSeparator", "HorizontalSeparator"), ("TSizegrip", "Sizegrip"),
            ("TMenubutton", "Menubutton"), ("TScrollbar", "Scrollbar"),
            ("TRoundButton", "RoundButton"), ("TImageButton", "ImageButton"),
            ("TTextProgressBar", "TextProgressBar"),
        ]
        for alias_name, original_name in pairs:
            self.assertIs(getattr(ts, alias_name), getattr(ts, original_name),
                          f"{alias_name} must alias {original_name}")
            self.assertIn(alias_name, ts.__all__)

    def test_t_aliases_construct(self):
        """T* aliases build working elements."""
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
        self.assertFalse(hasattr(ts.Text("x"), "__dict__"))
        self.assertFalse(hasattr(ts.Input("x"), "__dict__"))

    def test_key_property(self):
        element = ts.Text("x", key="-K-")
        self.assertEqual(element.key, "-K-")
        element.key = "-K2-"
        self.assertEqual(element.key, "-K2-")

    def test_input_get_before_build(self):
        element = ts.Input("default")
        self.assertEqual(element.default_text, "default")


class TestWindow(unittest.TestCase):
    def test_lifecycle(self):
        window = ts.Window(
            "t",
            [[ts.Text("hi", key="-T-")], [ts.Input("", key="-IN-")], [ts.Button("OK", key="-B-")]],
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
            ts.Window("t", [[ts.Text("a", key="-K-")], [ts.Text("b", key="-K-")]], finalize=True)

    def test_button_click(self):
        window = ts.Window("t", [[ts.Button("Go", key="-GO-")]], finalize=True)
        window["-GO-"].click()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-GO-")
        window.close()

    def test_context_manager(self):
        with ts.Window("t", [[ts.Text("x")]]) as window:
            self.assertTrue(window.finalized)
        self.assertTrue(window.was_closed)

    def test_container_recursion(self):
        window = ts.Window(
            "t",
            [[ts.Frame("F", [[ts.Column([[ts.Text("deep", key="-DEEP-")]])]])]],
            finalize=True,
        )
        self.assertIsNotNone(window["-DEEP-"].widget)
        window.close()

    def test_tab_group(self):
        window = ts.Window(
            "t",
            [[ts.TabGroup([[ts.Tab("one", [[ts.Text("1", key="-1-")]]),
                    ts.Tab("two", [[ts.Text("2", key="-2-")]])]])]],
            finalize=True,
        )
        self.assertIsNotNone(window["-1-"].widget)
        self.assertIsNotNone(window["-2-"].widget)
        window.close()

    def test_menu_bar(self):
        window = ts.Window(
            "t", [[ts.Menu([["&File", ["Open", "---", "Exit"]]])]], finalize=True
        )
        self.assertIsNotNone(window.tk_root.nametowidget(window.tk_root.cget("menu")))
        window.close()

    def test_fill(self):
        window = ts.Window(
            "t", [[ts.Input("", key="-IN-"), ts.Text("", key="-T-")]], finalize=True
        )
        window.fill({"-IN-": "abc", "-T-": "xyz"})
        self.assertEqual(window["-IN-"].get(), "abc")
        self.assertEqual(window["-T-"].get(), "xyz")
        window.close()

    def test_write_event_value(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.write_event_value("-CUSTOM-")
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-CUSTOM-")
        window.close()


class TestElementOptions(unittest.TestCase):
    """P0 element level options: metadata, pad/expand, right click menu."""

    def test_metadata(self):
        element = ts.Text("x", metadata={"answer": 42})
        self.assertEqual(element.metadata, {"answer": 42})
        self.assertIsNone(ts.Input("d").metadata)

    def test_pad_and_expand_stored(self):
        element = ts.Text("x", pad=(10, 5), expand_x=True)
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
        window = ts.Window("t", [[ts.Text("hi", tooltip="tip")]], finalize=True)
        self.assertIsNotNone(window.tk_root)
        window.close()

    def test_disabled_construction(self):
        window = ts.Window(
            "t",
            [[ts.Input("", key="-IN-", disabled=True), ts.Button("B", key="-B-", disabled=True)]],
            finalize=True,
        )
        self.assertEqual(str(window["-IN-"].widget.cget("state")), "disabled")
        self.assertTrue(window["-IN-"].disabled)
        self.assertEqual(str(window["-B-"].widget.cget("state")), "disabled")
        window.close()

    def test_right_click_menu_built(self):
        element = ts.Text(
            "x",
            right_click_menu=["&Menu", ["One", "---", "!Two", ["&Sub", ["Deep"]]]],
        )
        window = ts.Window("t", [[element]], finalize=True)
        menu = element._popup_menu
        self.assertIsNotNone(menu)
        # single cascade entry "Menu" wrapping the items
        self.assertEqual(menu.entrycget(0, "label"), "Menu")
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
                    ts.Input(
                        "",
                        key="-IN-",
                        text_color="#ff0000",
                        background_color="#101010",
                        font=("Courier", 10),
                    ),
                    ts.Button("B", key="-B-", button_color=("#ffffff", "#000080")),
                    ts.Checkbox("c", key="-CK-", text_color="#0000ff", font=("Arial", 12)),
                    ts.Combo(["a"], key="-CB-", background_color="#202020"),
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
                    [ts.Input("", key="-IN-"), ts.Combo(["a"],
                            key="-CB-"), ts.Checkbox("c", key="-CK-")],
                    [ts.Button("B", key="-B-"), ts.Radio("r", 1, key="-R-"), ts.Slider((0, 10))],
                    [ts.Table([["a"]], headings=["H"], key="-TB-"),
                            ts.Tree(headings=["H"], key="-TR-")],
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
        # Listbox map returns tk constants; Treeview map returns strings.
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
            [[ts.Text("left"), ts.Input("", key="-IN-", expand_x=True)]],
            finalize=True,
        )
        frame = window.tk_root.grid_slaves()[0]
        self.assertEqual(frame.columnconfigure(1)["weight"], 1)
        self.assertEqual(frame.columnconfigure(0)["weight"], 0)
        window.close()

    def test_justification_sticky(self):
        window = ts.Window(
            "t",
            [[ts.Text("r", justification="right")]],
            finalize=True,
        )
        widget = window.tk_root.grid_slaves()[0].grid_slaves()[0]
        info = widget.grid_info()
        self.assertEqual(info["sticky"], "e")
        window.close()

    def test_perform_long_operation(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        thread = window.perform_long_operation(lambda: "-RESULT-")
        self.assertTrue(thread.daemon)
        event, _values = window.read(timeout=3000)
        self.assertEqual(event, "-RESULT-")
        window.close()

    def test_perform_long_operation_window_arg(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)

        def worker(win):
            win.write_event_value("-FROM-WORKER-")

        window.perform_long_operation(worker, end_key=None)
        event, _values = window.read(timeout=3000)
        self.assertEqual(event, "-FROM-WORKER-")
        window.close()

    def test_window_management_api(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.set_size((320, 200))
        window.refresh()
        self.assertGreaterEqual(window.size[0], 300)
        window.set_alpha_channel(0.8)
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
        window = ts.Window("t", [[ts.Text("x")]], finalize=True, size=(10, 10))
        window.tk_root.update()
        self.assertGreaterEqual(window.tk_root.winfo_width(), 140)
        window.close()

    def test_disable_close(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True, disable_close=True)
        window.tk_root.protocol("WM_DELETE_WINDOW")  # handler exists, no crash
        window.close()
        self.assertTrue(window.was_closed)

    def test_resizable_option(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True, resizable=False)
        self.assertEqual(window.tk_root.resizable(), (False, False))
        window.close()


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
        graph = ts.Graph(
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
        graph = ts.Graph((50, 50), (0, 0), (50, 50))
        window = ts.Window("t", [[graph]], finalize=True)
        figure = graph.draw_image((5, 45), data_base64=ts.BLANK_BASE64)
        self.assertTrue(figure)
        self.assertEqual(len(graph._images), 1)  # photo kept alive
        graph.erase()
        self.assertEqual(len(graph._images), 0)
        window.close()

    def test_table_sorting(self):
        table = ts.Table(
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

    def test_multiline_undo_and_colored_print(self):
        multiline = ts.Multiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.print("line-one")
        multiline.print("bad", text_color="#cc0000")
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
        multiline = ts.Multiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.update("fresh text")
        self.assertEqual(str(multiline._text.cget("state")), "normal")
        window.close()

    def test_button_with_image(self):
        button = ts.Button("Go", key="-B-", image_data=ts.BLANK_BASE64)
        window = ts.Window("t", [[button]], finalize=True)
        self.assertTrue(button.widget.cget("image"))
        self.assertEqual(str(button.widget.cget("compound")), "left")
        window.close()

    def test_clipboard(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.clipboard_set("py-simple")
        self.assertEqual(window.clipboard_get(), "py-simple")
        window.clipboard_append("-gui")
        self.assertEqual(window.clipboard_get(), "py-simple-gui")
        window.clipboard_clear()
        window.close()

    def test_set_min_size(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.set_min_size((200, 100))
        self.assertEqual(window.tk_root.minsize(), (200, 100))
        window.close()

    def test_set_dpi_awareness(self):
        result = ts.set_dpi_awareness()
        self.assertIsInstance(result, bool)


class TestNativeCoverage(unittest.TestCase):
    """Per-widget coverage of the native Tk/ttk passthrough APIs."""

    def test_input_native_api(self):
        element = ts.Input("abc", justify="right", key="-IN-")
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
        combo = ts.Combo(["a", "b", "c"], key="-CB-")
        window = ts.Window("t", [[combo]], finalize=True)
        combo.set("b")
        self.assertEqual(combo.get(), "b")
        self.assertEqual(combo.current(), 1)
        combo.current(2)
        self.assertEqual(combo.get(), "c")
        window.close()

    def test_spin_numeric_range(self):
        spin = ts.Spin(range_=(0, 20), increment=5, initial_value=10, wrap=True)
        window = ts.Window("t", [[spin]], finalize=True)
        self.assertEqual(spin.get(), "10")
        spin.set(15)
        self.assertEqual(spin.get(), "15")
        # values were generated from the range with the increment
        self.assertEqual(spin.values, [0, 5, 10, 15, 20])
        window.close()
        with self.assertRaises(ValueError):
            ts.Spin([1, 2], range_=(0, 10))

    def test_checkbox_toggle(self):
        checkbox = ts.Checkbox("c", default=False)
        window = ts.Window("t", [[checkbox]], finalize=True)
        checkbox.toggle()
        self.assertTrue(checkbox.get())
        checkbox.select()
        checkbox.deselect()
        self.assertFalse(checkbox.get())
        window.close()

    def test_radio_select_helpers(self):
        first = ts.Radio("one", "g", key="-R1-")
        second = ts.Radio("two", "g", key="-R2-")
        window = ts.Window("t", [[first, second]], finalize=True)
        second.select()
        self.assertTrue(second.get())
        self.assertFalse(first.get())
        self.assertEqual(first.group_value(), "two")
        second.deselect()
        self.assertEqual(first.group_value(), "")
        window.close()

    def test_progressbar_indeterminate(self):
        bar = ts.ProgressBar(100, key="-PB-")
        window = ts.Window("t", [[bar]], finalize=True)
        bar.start_indeterminate(interval_ms=30)
        self.assertEqual(str(bar.widget.cget("mode")), "indeterminate")
        window.refresh()
        bar.stop_indeterminate()
        self.assertEqual(str(bar.widget.cget("mode")), "determinate")
        window.close()

    def test_multiline_passthrough(self):
        multiline = ts.Multiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.insert("1.0", "hello")
        multiline.insert("end", " world")
        self.assertEqual(multiline.get(), "hello world")
        multiline.delete("1.0", "1.6")  # removes "hello "
        self.assertEqual(multiline.get(), "world")
        multiline.see("end")  # must not raise
        window.close()

    def test_text_image_and_wrap(self):
        text = ts.Text("logo:", image_data=ts.DEFAULT_BASE64_ICON, wrap_length=200)
        window = ts.Window("t", [[text]], finalize=True)
        self.assertIsNotNone(text._photo)
        self.assertEqual(text._photo.width(), 64)
        self.assertEqual(int(text.widget.cget("wraplength")), 200)
        window.close()

    def test_listbox_see_size(self):
        listbox = ts.Listbox([f"item {i}" for i in range(30)], size=(10, 3))
        window = ts.Window("t", [[listbox]], finalize=True)
        self.assertEqual(listbox.size(), 30)
        listbox.see(25)  # must not raise
        window.close()

    def test_table_tree_see(self):
        table = ts.Table([[f"row {i}"] for i in range(50)], headings=["H"])
        window = ts.Window("t", [[table]], finalize=True)
        table.see(45)  # must not raise
        window.close()
        tree = ts.Tree()
        window2 = ts.Window("t2", [[tree]], finalize=True)
        tree.insert("", "k1", "visible")
        tree.see("k1")
        window2.close()

    def test_frame_label_anchor(self):
        frame = ts.Frame("Title", [[ts.Text("x")]], label_anchor="se")
        window = ts.Window("t", [[frame]], finalize=True)
        self.assertEqual(str(frame.widget.cget("labelanchor")), "se")
        window.close()

    def test_image_zoom_getters(self):
        image = ts.Image(data_base64=ts.DEFAULT_BASE64_ICON)
        window = ts.Window("t", [[image]], finalize=True)
        self.assertEqual((image.width, image.height), (64, 64))
        image.zoom(2)
        self.assertEqual((image.width, image.height), (128, 128))
        image.subsample(4)
        self.assertEqual((image.width, image.height), (32, 32))
        self.assertIsNotNone(image.photo)
        window.close()

    def test_canvas_passthrough(self):
        canvas = ts.Canvas((100, 100))
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
                [ts.Text("a", justification=ts.Justify.CENTER)],
                [ts.Input("", justify=ts.Justify.RIGHT, key="-IN-")],
                [ts.Frame("F", [[ts.Text("x")]], label_anchor=ts.LabelAnchor.SE,
                          key="-FRAME-")],
                [ts.Multiline("", wrap=ts.WrapMode.NONE, key="-ML-")],
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
        element = ts.Text("click", key="-T-")
        window = ts.Window("t", [[element]], finalize=True)
        element.bind(ts.EventType.RIGHT_CLICK)  # enum instead of "<Button-3>"
        element.widget.event_generate("<Button-3>", when="tail")
        window.tk_root.update()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-T-")
        window.close()

    def test_color_enum_in_widget(self):
        text = ts.Text("colored", text_color=ts.Color.RED,
                       background_color=ts.Color.NAVY)
        window = ts.Window("t", [[text]], finalize=True)
        self.assertEqual(str(text.widget.cget("foreground")), "red")
        window.close()

    def test_anchor_enum_in_text(self):
        text = ts.Text("anchored")
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
        window = ts.Window(layout=[[ts.Text("x")]], config=cfg, finalize=True)
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
            right_click_menu=["&Menu", ["Refresh"]],
            metadata={"tag": 1},
        )
        first = ts.Text("a", config=opts, key="-A-")
        second = ts.Input("", config=opts, key="-B-")
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
        element = ts.Text("a", config=opts, metadata="explicit")
        self.assertEqual(element.metadata, "explicit")

    def test_element_options_requires_type(self):
        with self.assertRaises(TypeError):
            ts.Text("a", config={"pad": 4})

    def test_window_config_carry_layout(self):
        cfg = ts.WindowConfig(title="LayoutInConfig",
                              layout=[[ts.Text("from cfg", key="-T-")]])
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
            [[ts.Input("", key="-IN-", validate="key", validate_command=ts.validate_integer)]],
            finalize=True,
        )
        widget = window["-IN-"].widget
        self.assertEqual(str(widget.cget("validate")), "key")
        self.assertTrue(widget.cget("validatecommand"))
        with self.assertRaises(TypeError):
            ts.Input(validate="key", validate_command="not-callable")
        window.close()

    def test_calendar_element(self):
        import datetime

        calendar_element = ts.Calendar(
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
        calendar_element = ts.Calendar(default_date=(2026, 2, 14), dateformat="%d.%m.%Y")
        self.assertEqual(calendar_element.get(), "14.02.2026")

    def test_splitter(self):
        splitter = ts.Splitter(
            [[[ts.Text("L", key="-L-")], [ts.Input(key="-LIN-")]],
             [[ts.Text("R", key="-R-")], [ts.Input(key="-RIN-")]]],
            orientation="h",
            key="-SP-",
        )
        window = ts.Window("t", [[splitter]], finalize=True)
        self.assertIsInstance(splitter.widget, tk.PanedWindow)
        self.assertIsNotNone(window["-LIN-"].widget)
        self.assertIsNotNone(window["-RIN-"].widget)
        self.assertEqual(len(splitter.widget.panes()), 2)
        with self.assertRaises(TypeError):
            ts.Splitter([[[ts.Text("only")]]])
        window.close()

    def test_scrollable_column(self):
        rows = [[ts.Text(f"row {i}")] for i in range(30)]
        scroll = ts.ScrollableColumn(rows, size=(200, 100), key="-SC-")
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
            [[ts.Text("x")]],
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
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
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
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        calls = []
        window.after(50, lambda: calls.append(1))
        deadline = time.time() + 2.0
        while not calls and time.time() < deadline:
            window.read(timeout=20)
        self.assertEqual(len(calls), 1)
        window.close()

    def test_text_find_and_replace_helpers(self):
        from TkSimpleGUI.popup import _text_find, _text_replace_all

        multiline = ts.Multiline("alpha beta ALPHA end", key="-ML-")
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
    """Batch 2: CheckList, Toolbar, toggle, LabeledEdit, KV editor,
            FlowPanel, icons, editing, Shape."""

    def test_checklist(self):
        checklist = ts.CheckList(
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
        toolbar = ts.Toolbar(
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
        first = ts.Button("B1", key="-B1-", toggle=True, group_id="g")
        second = ts.Button("B2", key="-B2-", toggle=True, group_id="g")
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
        labeled = ts.LabeledEdit("Name", "world", key="-NAME-")
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
        editor = ts.KeyValueEditor(
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
        flow = ts.FlowPanel(
            [ts.Text("one"), ts.Text("two"), ts.Text("three")], key="-FLOW-"
        )
        window = ts.Window("t", [[flow]], finalize=True)
        window.refresh()
        first = flow._children[0].widget
        self.assertTrue(first.place_info()["x"])
        flow._reflow()  # resize reflow must not crash
        self.assertEqual(len(flow._children), 3)
        window.close()

    def test_tree_row_icons(self):
        tree = ts.Tree(headings=["H"], key="-TR-")
        window = ts.Window("t", [[tree]], finalize=True)
        tree.insert("", "item1", "Root", image_data=ts.BLANK_BASE64)
        item = tree.widget.item("item1")
        self.assertTrue(item.get("image"))
        self.assertEqual(len(tree._images), 1)  # photo retained
        window.close()

    def test_table_row_icons(self):
        table = ts.Table(
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
        table = ts.Table(
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
        shape = ts.Shape("oval", size=(60, 30), fill_color="red", key="-S-")
        window = ts.Window("t", [[shape]], finalize=True)
        self.assertEqual(len(shape.widget.find_all()), 1)
        shape.update(fill_color="blue", line_color="green")
        with self.assertRaises(ValueError):
            ts.Shape("hexagon")
        window.close()


class TestThirdBatch(unittest.TestCase):
    """Batch 3: Action, UserSettings, data binding, i18n, animation, tray, CLI."""

    def test_action_normalization_and_callback(self):
        fired = []
        open_action = ts.Action(
            "Open", key="-OPEN-", callback=lambda w, v: fired.append("open")
        )
        menu_item = ts.Text("menu", key="Open")  # posting text "Open"
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
        window = ts.Window("t", [[ts.Text("x")]], finalize=True, actions=[save_action])
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
        table = ts.Table([], headings=[], key="-TB-")
        window = ts.Window("t", [[table]], finalize=True)
        table.bind(records)
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

    def test_i18n(self):
        import json
        import shutil
        import tempfile

        directory = tempfile.mkdtemp()
        try:
            catalog_path = f"{directory}fr.json"
            with open(catalog_path, "w") as handle:
                json.dump({"Open": "Ouvert", "Save": "Sauve"}, handle)
            ts.set_translations(catalog_path)
            self.assertEqual(ts.translate("Open"), "Ouvert")
            self.assertEqual(ts._("Save"), "Sauve")
            self.assertEqual(ts._("Unknown"), "Unknown")
            ts.add_translation("Close", "Ferme")
            self.assertEqual(ts._("Close"), "Ferme")
            ts.clear_translations()
            self.assertEqual(ts._("Open"), "Open")
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_animation_fade_and_progress(self):
        bar = ts.ProgressBar(100, key="-BAR-")
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
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
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
        # dbg formats args and delegates to the quick popup
        self.assertTrue(callable(ts.dbg))
        self.assertTrue(callable(ts.popup_quick))


class TestLineA(unittest.TestCase):
    """Line A: full coverage of the native Tk/ttk API surface."""

    def test_element_bind_and_unbind(self):
        element = ts.Text("click me", key="-T-")
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
        element = ts.Text("x")
        with self.assertRaises(RuntimeError):
            element.bind("<Button-1>")

    def test_multiline_scrollbar_wrap(self):
        multiline = ts.Multiline(
            "\n".join(f"line {i}" for i in range(50)),
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
        multiline = ts.Multiline("", key="-ML-")
        window = ts.Window("t", [[multiline]], finalize=True)
        multiline.print("Visit ")
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
        image = ts.Image(data_base64=ts.DEFAULT_BASE64_ICON, zoom=2)
        window = ts.Window("t", [[image]], finalize=True)
        self.assertEqual(image._photo.width(), 128)
        window.close()
        image = ts.Image(data_base64=ts.DEFAULT_BASE64_ICON, subsample=2)
        window = ts.Window("t", [[image]], finalize=True)
        self.assertEqual(image._photo.width(), 32)
        window.close()

    def test_spin_is_ttk(self):
        spin = ts.Spin([1, 2, 3], initial_value=2)
        window = ts.Window("t", [[spin]], finalize=True)
        self.assertIsInstance(spin.widget, ttk.Spinbox)
        self.assertEqual(spin.get(), "2")
        window.close()

    def test_ttk_theme_switch(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
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
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.set_fullscreen(True)
        window.refresh()
        self.assertEqual(int(window.tk_root.attributes("-fullscreen")), 1)
        window.set_fullscreen(False)
        window.make_toolwindow(False)
        window.set_max_size((800, 600))
        window.bell()
        child = ts.Window("child", [[ts.Text("c")]], finalize=True)
        child.transient(window)
        child.stack_above(window)
        child.close()
        window.close()

    def test_window_selection(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.selection_set("primary-data")
        window.refresh()
        self.assertEqual(window.selection_get(), "primary-data")
        window.close()

    def test_window_style_hooks(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.configure_style("TButton", padding=(16, 8))
        window.map_style("TButton", background=[("active", "#3a7bd5")])
        window.close()

    def test_font_tools(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        families = ts.font_families()
        self.assertTrue(families)
        width = ts.font_measure("hello", ("Helvetica", 10))
        self.assertGreater(width, 0)
        actual = ts.font_actual(("Helvetica", 12, "bold"))
        self.assertEqual(actual["size"], 12)
        self.assertEqual(actual["weight"], "bold")
        window.close()

    def test_menubutton_element(self):
        menu_button = ts.Menubutton("Options", ["One", "---", "Two"], key="-MB-")
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
        multiline = ts.Multiline("\n".join(f"line {i}" for i in range(60)),
                                 size=(20, 3), key="-ML-")
        scrollbar = ts.Scrollbar(multiline, orientation="v")
        window = ts.Window("t", [[multiline, scrollbar]], finalize=True)
        self.assertIsNotNone(scrollbar.widget)
        with self.assertRaises(TypeError):
            ts.Window("t2", [[ts.Scrollbar(ts.Text("not scrollable"))]], finalize=True)
        window.close()

    def test_tabgroup_enhancements(self):
        tab_group = ts.TabGroup(
            [[ts.Tab("one", [[ts.Text("1")]]), ts.Tab("two", [[ts.Text("2")]])]],
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
    """TChart: 8 chart types on the Graph coordinate system."""

    def _chart(self, kind, **kwargs):
        chart = ts.TChart((300, 180), chart_type=kind, key="-C-",
                          background_color="#ffffff", **kwargs)
        window = ts.Window("t", [[chart]], finalize=True)
        self.addCleanup(window.close)
        return chart

    def test_invalid_type_rejected(self):
        with self.assertRaises(ValueError):
            ts.TChart(chart_type="radar")

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
        button = ts.RoundButton("Go", size=(90, 30), radius=14,
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
        button = ts.RoundButton("Go", key="-RB-")
        button.set_click_handler(calls.append)
        window = ts.Window("t", [[button]], finalize=True)
        window.tk_root.update()
        button.widget.event_generate("<Button-1>", x=45, y=15, when="tail")
        window.tk_root.update()
        self.assertEqual(calls, [button])
        window.close()

    def test_image_button(self):
        button = ts.ImageButton(data_base64=ts.DEFAULT_BASE64_ICON, key="-IB-")
        window = ts.Window("t", [[button]], finalize=True)
        window.tk_root.update()
        self.assertEqual(button._photo.width(), 64)  # sized from the image
        button.widget.event_generate("<Button-1>", x=10, y=10, when="tail")
        window.tk_root.update()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-IB-")
        window.close()

    def test_text_progress_bar(self):
        bar = ts.TextProgressBar(100, current_value=42, key="-TPB-")
        window = ts.Window("t", [[bar]], finalize=True)
        self.assertEqual(bar.get(), 42)
        label = bar._widget.itemconfigure(bar._label_id, "text")
        self.assertEqual(str(label[-1]), "42%")
        bar.update(current_value=100)
        label = bar._widget.itemconfigure(bar._label_id, "text")
        self.assertEqual(str(label[-1]), "100%")
        window.close()

    def test_toast(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
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
        table = ts.Table([["a", "b"]], headings=["H1", "H2"], key="-TB-")
        window = ts.Window("t", [[table]], finalize=True)
        width = table.column_width(0)
        self.assertGreater(width, 0)
        table.set_column_width(0, 150)
        self.assertEqual(table.column_width(0), 150)
        window.close()

    def test_slider_value_bubble(self):
        slider = ts.Slider((0, 100), default_value=30, show_value=True,
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
        tree = ts.Tree(key="-TR-")
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
        tab_group = ts.TabGroup(
            [[ts.Tab("one", [[ts.Text("1")]]), ts.Tab("two", [[ts.Text("2")]])]],
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
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        progress = ts.taskbar_progress(window)
        if ts.running_windows():
            self.assertIsNotNone(progress)
        else:
            self.assertIsNone(progress)
        window.close()


class TestUnifiedLoop(unittest.TestCase):
    """Single event loop: global bus + main_loop, multi-window by design."""

    def tearDown(self):
        ts.Window.close_all()

    def test_cross_window_events(self):
        """Any window read() receives events from other windows (bus order)."""
        first = ts.Window("one", [[ts.Button("ping", key="-PING-")]], finalize=True)
        second = ts.Window("two", [[ts.Button("pong", key="-PONG-")]], finalize=True)
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
        first = ts.Window("one", [[ts.Text("x")]], finalize=True)
        second = ts.Window("two", [[ts.Text("y")]], finalize=True)
        second.write_event_value("-TWO-EVENT-")
        window, event, _values = ts.Window.read_all_windows(timeout=500)
        self.assertIs(window, second)
        self.assertEqual(event, "-TWO-EVENT-")
        first.close()
        second.close()

    def test_winclosed_removes_window_from_registry(self):
        first = ts.Window("one", [[ts.Text("x")]], finalize=True)
        second = ts.Window("two", [[ts.Text("y")]], finalize=True)
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
        first = ts.Window("one", [[ts.Text("x")]], finalize=True)
        second = ts.Window("two", [[ts.Text("y")]], finalize=True)
        first.close()
        event, _values = second.read(timeout=200)
        self.assertEqual(event, ts.TIMEOUT_KEY)
        second.close()

    def test_main_loop_exits_when_all_closed(self):
        app = ts.TkSimpleEvent()
        window = ts.Window("one", [[ts.Button("quit", key="-QUIT-")]], finalize=True)
        seen = []

        @app.bind_event("-QUIT-")
        def on_quit(window, values):
            seen.append("quit")
            window.close()  # last window gone -> loop ends

        window.write_event_value("-QUIT-")  # fires once the loop pumps
        ts.main_loop(window, app)
        self.assertEqual(seen, ["quit"])
        self.assertEqual(ts.Window.active_windows(), [])

    def test_main_loop_dispatches_to_on_handlers(self):
        app = ts.TkSimpleEvent()
        main = ts.Window("main", [[ts.Button("open", key="-OPEN-")]], finalize=True)
        received = []

        @app.bind_event("-OPEN-")
        def on_open(window, values):
            child = ts.Window("child", [[ts.Text("hi", key="-HI-")]], finalize=True)
            child.write_event_value("-CHILD-READY-")

        @app.bind_event("-CHILD-READY-")
        def on_child_ready(window, values):
            received.append(window.title)
            ts.Window.close_all()

        main.write_event_value("-OPEN-")  # fires inside the loop
        ts.main_loop(main, app)
        self.assertEqual(received, ["child"])  # handler got the CHILD window
        self.assertEqual(ts.Window.active_windows(), [])

    def test_main_loop_with_action_callbacks(self):
        calls = []
        app = ts.TkSimpleEvent()
        ok_action = ts.Action("OK", key="OK",
                              callback=lambda window, values: calls.append("ok"))
        window = ts.Window("t", [[ts.Button("OK", key="OK")]],
                           finalize=True, actions=[ok_action])

        @app.bind_event("OK")
        def on_ok(window, values):
            calls.append("handler")
            ts.Window.close_all()

        window.write_event_value("OK")  # fires inside the loop
        ts.main_loop(window, app)
        self.assertEqual(calls, ["ok", "handler"])

    def test_close_all_drops_stale_events(self):
        first = ts.Window("one", [[ts.Text("x")]], finalize=True)
        first.write_event_value("-STALE-")
        ts.Window.close_all()
        second = ts.Window("two", [[ts.Text("y")]], finalize=True)
        event, _values = second.read(timeout=200)
        self.assertEqual(event, ts.TIMEOUT_KEY)  # stale event was dropped
        second.close()


class TestWindowHierarchy(unittest.TestCase):
    """Window hierarchy: parent/children/ancestors + cascading close."""

    def test_parent_link_and_query(self):
        main = ts.Window("main", [[ts.Text("m")]], finalize=True)
        child = ts.Window("child", [[ts.Text("c")]], finalize=True, parent=main)
        grandchild = ts.Window("grand", [[ts.Text("g")]], finalize=True, parent=child)
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
        main = ts.Window("main", [[ts.Text("m")]], finalize=True)
        child = ts.Window("child", [[ts.Text("c")]], parent=main)  # not finalized yet
        self.assertIs(child.parent, main)
        child.finalize()  # link established at finalize
        self.assertIn(child, main.children)
        child.close()
        self.assertEqual(main.children, [])
        main.close()

    def test_transient_sets_parent(self):
        main = ts.Window("main", [[ts.Text("m")]], finalize=True)
        dialog = ts.Window("dialog", [[ts.Text("d")]], finalize=True)
        dialog.transient(main)
        self.assertIs(dialog.parent, main)
        self.assertIn(dialog, main.children)
        dialog.transient(None)  # detach
        self.assertIsNone(dialog.parent)
        self.assertEqual(main.children, [])
        dialog.close()
        main.close()

    def test_child_close_keeps_parent(self):
        main = ts.Window("main", [[ts.Text("m")]], finalize=True)
        child = ts.Window("child", [[ts.Text("c")]], finalize=True, parent=main)
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
            "t", [[ts.Text("x")]], finalize=True, disable_esc=True
        )
        window.tk_root.event_generate("<Escape>")
        window.tk_root.update()
        # the break handler swallows the key: no WIN_CLOSED event was posted
        with self.assertRaises(queue.Empty):
            window._event_queue.get_nowait()
        window.close()

    def test_esc_without_flag_reaches_window(self):
        window = ts.Window("t", [[ts.Text("x")]], finalize=True)
        window.tk_root.event_generate("<Escape>")
        window.tk_root.update()
        # without disable_esc the key press is not swallowed; the window
        # stays open and its queue simply receives no forced break
        self.assertFalse(window.was_closed)
        window.close()

    def test_disable_close_blocks_frame_and_modal_implies_it(self):
        window = ts.Window(
            "t", [[ts.Text("x")]], finalize=True, disable_close=True
        )
        # simulate the frame close button: the protocol handler is a no-op
        window.tk_root.protocol("WM_DELETE_WINDOW")() if False else None
        window.tk_root.update()
        self.assertFalse(window.was_closed)
        window.close()

    def test_modal_sets_grab_and_blocks_frame_close(self):
        main = ts.Window("main", [[ts.Text("m")]], finalize=True)
        dialog = ts.Window(
            "dialog", [[ts.Button("OK", key="-OK-")]],
            finalize=True, modal=True,
        )
        self.assertEqual(dialog.tk_root.grab_current(), dialog.tk_root)
        # modal implies disable_close: no WIN_CLOSED can be posted by the frame
        self.assertFalse(dialog.was_closed)
        dialog.close()
        main.close()

    def test_system_block_released_on_close(self):
        window = ts.Window(
            "t", [[ts.Text("x")]], finalize=True, system_block=True
        )
        self.assertTrue(window._system_block)
        self.assertTrue(window._want_system_block)
        window.close()
        self.assertFalse(window._system_block)
        self.assertFalse(window._want_system_block)

    def test_system_block_hide_releases_and_unhide_rearms(self):
        window = ts.Window(
            "t", [[ts.Text("x")]], finalize=True, system_block=True
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
        first = ts.Window("a", [[ts.Text("x")]], finalize=True, system_block=True)
        second = ts.Window("b", [[ts.Text("x")]], finalize=True, system_block=True)
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
        window = ts.Window(config=cfg, layout=[[ts.Text("x")]], finalize=True)
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
        window = ts.Window("one", [[ts.Button("quit", key="-QUIT-")]], finalize=True)
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

        window = ts.Window("one", [[ts.Text("x")]], finalize=True)
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

        window = ts.Window("idle", [[ts.Text("x")]], finalize=True)
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

        window = ts.Window("one", [[ts.Text("x")]], finalize=True)
        window.write_event_value("-PKG-LEVEL-EVENT-")
        window.run()  # default_app must see the handler above
        self.assertEqual(fired, ["one"])

        ts.default_app()._event_handlers.pop("-PKG-LEVEL-EVENT-", None)

    def test_run_without_finalize_finalizes(self):
        app = ts.TkSimpleEvent()
        window = ts.Window("one", [[ts.Text("x")]])  # NOT finalized

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
            [[ts.Text("x")]],
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
        window = ts.Window("late", [[ts.Text("y")]], finalize=True)
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
            msg=f"showcase --smoke failed:\nstdout={result.stdout}\n"
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

        window = ts.Window("evt", [[ts.Text("x")]], finalize=True)
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
            return ts.Window(title, [[ts.Text("x")]], finalize=True)

        first = make_window("single")
        second = make_window("single")
        self.assertIs(first, second)
        first.close()

    def test_singleton_window_evicts_closed(self):
        """Closed windows must not pin memory in the registry."""
        import gc

        @ts.singleton_window
        def make_window(title):
            return ts.Window(title, [[ts.Text("x")]], finalize=True)

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
        element = ts.Text("x")
        self.assertFalse(hasattr(element, "__dict__"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
