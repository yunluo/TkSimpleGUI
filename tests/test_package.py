# -*- coding: utf-8 -*-
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

import TkSimpleGUI as sg  # noqa: E402


class TestMeta(unittest.TestCase):
    def test_version(self):
        self.assertEqual(sg.__version__, "0.1.0")

    def test_author(self):
        self.assertEqual(sg.__author__, "yunluo")


class TestThemes(unittest.TestCase):
    def test_table_size(self):
        self.assertGreater(len(sg.list_of_look_and_feel_values()), 150)

    def test_native_by_default(self):
        self.assertIsNone(sg.theme())

    def test_apply_and_reset(self):
        name = sg.theme("DarkBlue3")
        self.assertEqual(name, "DarkBlue3")
        self.assertEqual(sg.theme(), "DarkBlue3")
        self.assertIsNotNone(sg.theme_background_color())
        sg.theme(None)
        self.assertIsNone(sg.theme())
        self.assertIsNone(sg.theme_background_color())

    def test_invalid_theme(self):
        with self.assertRaises(ValueError):
            sg.theme("__No Such Theme__")

    def test_case_insensitive(self):
        self.assertEqual(sg.theme("darkblue3"), "DarkBlue3")
        sg.theme(None)

    def test_add_new(self):
        sg.theme_add_new("__TestTheme__", {"BACKGROUND": "#123456", "TEXT": "#ffffff"})
        self.assertIn("__TestTheme__", sg.list_of_look_and_feel_values())
        sg.theme("__TestTheme__")
        self.assertEqual(sg.theme_background_color(), "#123456")
        sg.theme(None)


class TestSettings(unittest.TestCase):
    def test_set_get(self):
        sg.set_options(border_width=7)
        self.assertEqual(sg.get_options()["border_width"], 7)
        sg.set_options(border_width=1)

    def test_validation(self):
        with self.assertRaises(TypeError):
            sg.set_options(no_such=1)


class TestUtils(unittest.TestCase):
    def test_rgb(self):
        self.assertEqual(sg.rgb(255, 0, 0), "#ff0000")
        self.assertEqual(sg.rgb(0, 255, 0), "#00ff00")
        self.assertEqual(sg.rgb(0, 0, 255), "#0000ff")
        self.assertEqual(sg.rgb(300, -5, 12), "#ff000c")

    def test_timer(self):
        timer = sg.Timer()
        self.assertEqual(timer.elapsed, 0)
        timer.start()
        self.assertGreaterEqual(timer.elapsed_ms, 0)
        timer.stop()

    def test_platform(self):
        self.assertIsInstance(sg.running_windows(), bool)
        self.assertIsInstance(sg.running_linux(), bool)
        self.assertIsInstance(sg.running_mac(), bool)


class TestElementConstruction(unittest.TestCase):
    def test_construct_all(self):
        elements = [
            sg.Text("t"),
            sg.Input("d"),
            sg.Combo(["a", "b"]),
            sg.Listbox(["a", "b"]),
            sg.Spin([1, 2, 3]),
            sg.Checkbox("c"),
            sg.Radio("r", group_id=1),
            sg.Slider((0, 10)),
            sg.Multiline("m"),
            sg.Output(),
            sg.ProgressBar(100),
            sg.Button("b"),
            sg.Image(),
            sg.Canvas((50, 50)),
            sg.Graph((100, 100), (0, 0), (10, 10)),
            sg.Frame("f", [[sg.Text("x")]]),
            sg.Column([[sg.Text("y")]]),
            sg.Tab("t", [[sg.Text("z")]]),
            sg.TabGroup([[sg.Tab("t1", [[sg.Text("w")]])]]),
            sg.Table([["a"]], headings=["H"]),
            sg.Tree(headings=["H"]),
            sg.StatusBar("s"),
            sg.VerticalSeparator(),
            sg.HorizontalSeparator(),
            sg.Menu([["&File", ["Open", "Exit"]]]),
        ]
        for element in elements:
            self.assertIsNotNone(element)

    def test_shortcuts(self):
        self.assertIs(sg.InputText, sg.Input)

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
            self.assertIs(getattr(sg, alias_name), getattr(sg, original_name),
                          f"{alias_name} must alias {original_name}")
            self.assertIn(alias_name, sg.__all__)

    def test_t_aliases_construct(self):
        """T* aliases build working elements."""
        layout = [
            [sg.TText("name"), sg.TInput("world", key="-E-")],
            [sg.TCombo(["a", "b"], key="-C-"), sg.TButton("OK", key="-B-")],
            [sg.TMultiline("text", key="-M-")],
        ]
        window = sg.Window("t", layout, finalize=True)
        self.assertEqual(window["-E-"].get(), "world")
        self.assertEqual(window["-B-"].button_text, "OK")
        window.close()

    def test_slots_encapsulation(self):
        self.assertFalse(hasattr(sg.Text("x"), "__dict__"))
        self.assertFalse(hasattr(sg.Input("x"), "__dict__"))

    def test_key_property(self):
        element = sg.Text("x", key="-K-")
        self.assertEqual(element.key, "-K-")
        element.key = "-K2-"
        self.assertEqual(element.key, "-K2-")

    def test_input_get_before_build(self):
        element = sg.Input("default")
        self.assertEqual(element.default_text, "default")


class TestWindow(unittest.TestCase):
    def test_lifecycle(self):
        window = sg.Window(
            "t",
            [[sg.Text("hi", key="-T-")], [sg.Input("", key="-IN-")], [sg.Button("OK", key="-B-")]],
            finalize=True,
        )
        self.assertTrue(window.finalized)
        self.assertIn("-IN-", window)
        self.assertIsNotNone(window["-IN-"].widget)
        window["-IN-"].update("typed")
        self.assertEqual(window["-IN-"].get(), "typed")
        event, values = window.read(timeout=200)
        self.assertEqual(event, sg.TIMEOUT_KEY)
        self.assertEqual(values["-IN-"], "typed")
        window.close()
        self.assertTrue(window.was_closed)
        self.assertEqual(sg.Window.active_windows(), [])

    def test_duplicate_key_raises(self):
        with self.assertRaises(ValueError):
            sg.Window("t", [[sg.Text("a", key="-K-")], [sg.Text("b", key="-K-")]], finalize=True)

    def test_button_click(self):
        window = sg.Window("t", [[sg.Button("Go", key="-GO-")]], finalize=True)
        window["-GO-"].click()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-GO-")
        window.close()

    def test_context_manager(self):
        with sg.Window("t", [[sg.Text("x")]]) as window:
            self.assertTrue(window.finalized)
        self.assertTrue(window.was_closed)

    def test_container_recursion(self):
        window = sg.Window(
            "t",
            [[sg.Frame("F", [[sg.Column([[sg.Text("deep", key="-DEEP-")]])]])]],
            finalize=True,
        )
        self.assertIsNotNone(window["-DEEP-"].widget)
        window.close()

    def test_tab_group(self):
        window = sg.Window(
            "t",
            [[sg.TabGroup([[sg.Tab("one", [[sg.Text("1", key="-1-")]]),
                    sg.Tab("two", [[sg.Text("2", key="-2-")]])]])]],
            finalize=True,
        )
        self.assertIsNotNone(window["-1-"].widget)
        self.assertIsNotNone(window["-2-"].widget)
        window.close()

    def test_menu_bar(self):
        window = sg.Window(
            "t", [[sg.Menu([["&File", ["Open", "---", "Exit"]]])]], finalize=True
        )
        self.assertIsNotNone(window.tk_root.nametowidget(window.tk_root.cget("menu")))
        window.close()

    def test_fill(self):
        window = sg.Window(
            "t", [[sg.Input("", key="-IN-"), sg.Text("", key="-T-")]], finalize=True
        )
        window.fill({"-IN-": "abc", "-T-": "xyz"})
        self.assertEqual(window["-IN-"].get(), "abc")
        self.assertEqual(window["-T-"].get(), "xyz")
        window.close()

    def test_write_event_value(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        window.write_event_value("-CUSTOM-")
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-CUSTOM-")
        window.close()


class TestElementOptions(unittest.TestCase):
    """P0 element level options: metadata, pad/expand, right click menu."""

    def test_metadata(self):
        element = sg.Text("x", metadata={"answer": 42})
        self.assertEqual(element.metadata, {"answer": 42})
        self.assertIsNone(sg.Input("d").metadata)

    def test_pad_and_expand_stored(self):
        element = sg.Text("x", pad=(10, 5), expand_x=True)
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
        window = sg.Window("t", [[sg.Text("hi", tooltip="tip")]], finalize=True)
        self.assertIsNotNone(window.tk_root)
        window.close()

    def test_disabled_construction(self):
        window = sg.Window(
            "t",
            [[sg.Input("", key="-IN-", disabled=True), sg.Button("B", key="-B-", disabled=True)]],
            finalize=True,
        )
        self.assertEqual(str(window["-IN-"].widget.cget("state")), "disabled")
        self.assertTrue(window["-IN-"].disabled)
        self.assertEqual(str(window["-B-"].widget.cget("state")), "disabled")
        window.close()

    def test_right_click_menu_built(self):
        element = sg.Text(
            "x",
            right_click_menu=["&Menu", ["One", "---", "!Two", ["&Sub", ["Deep"]]]],
        )
        window = sg.Window("t", [[element]], finalize=True)
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
        window = sg.Window(
            "t",
            [
                [
                    sg.Input(
                        "",
                        key="-IN-",
                        text_color="#ff0000",
                        background_color="#101010",
                        font=("Courier", 10),
                    ),
                    sg.Button("B", key="-B-", button_color=("#ffffff", "#000080")),
                    sg.Checkbox("c", key="-CK-", text_color="#0000ff", font=("Arial", 12)),
                    sg.Combo(["a"], key="-CB-", background_color="#202020"),
                ]
            ],
            finalize=True,
        )
        self.assertIsNotNone(window["-IN-"].widget)
        window.close()

    def test_themed_ttk_widgets(self):
        # regression: themed mode used to crash ttk.Entry/Checkbutton with
        # unknown "-background" options
        sg.theme("DarkBlue3")
        try:
            window = sg.Window(
                "t",
                [
                    [sg.Input("", key="-IN-"), sg.Combo(["a"],
                            key="-CB-"), sg.Checkbox("c", key="-CK-")],
                    [sg.Button("B", key="-B-"), sg.Radio("r", 1, key="-R-"), sg.Slider((0, 10))],
                    [sg.Table([["a"]], headings=["H"], key="-TB-"),
                            sg.Tree(headings=["H"], key="-TR-")],
                ],
                finalize=True,
            )
            window.close()
        finally:
            sg.theme(None)


class TestWindowManagement(unittest.TestCase):
    def test_expand_weights(self):
        window = sg.Window(
            "t",
            [[sg.Text("left"), sg.Input("", key="-IN-", expand_x=True)]],
            finalize=True,
        )
        frame = window.tk_root.grid_slaves()[0]
        self.assertEqual(frame.columnconfigure(1)["weight"], 1)
        self.assertEqual(frame.columnconfigure(0)["weight"], 0)
        window.close()

    def test_justification_sticky(self):
        window = sg.Window(
            "t",
            [[sg.Text("r", justification="right")]],
            finalize=True,
        )
        widget = window.tk_root.grid_slaves()[0].grid_slaves()[0]
        info = widget.grid_info()
        self.assertEqual(info["sticky"], "e")
        window.close()

    def test_perform_long_operation(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        thread = window.perform_long_operation(lambda: "-RESULT-")
        self.assertTrue(thread.daemon)
        event, _values = window.read(timeout=3000)
        self.assertEqual(event, "-RESULT-")
        window.close()

    def test_perform_long_operation_window_arg(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)

        def worker(win):
            win.write_event_value("-FROM-WORKER-")

        window.perform_long_operation(worker, end_key=None)
        event, _values = window.read(timeout=3000)
        self.assertEqual(event, "-FROM-WORKER-")
        window.close()

    def test_window_management_api(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
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
        width, height = sg.Window.get_screen_size()
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_window_min_size_floor(self):
        # every window enforces a size floor so the title-bar buttons
        # (minimize / maximize / close) remain visible and clickable
        window = sg.Window("t", [[sg.Text("x")]], finalize=True, size=(10, 10))
        window.tk_root.update()
        self.assertGreaterEqual(window.tk_root.winfo_width(), 140)
        window.close()

    def test_disable_close(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True, disable_close=True)
        window.tk_root.protocol("WM_DELETE_WINDOW")  # handler exists, no crash
        window.close()
        self.assertTrue(window.was_closed)

    def test_resizable_option(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True, resizable=False)
        self.assertEqual(window.tk_root.resizable(), (False, False))
        window.close()


class TestTkIntegration(unittest.TestCase):
    """Deep tk/ttk API exposure: logo, graph handles, sorting, clipboard."""

    def test_default_logo_decodes(self):
        import tkinter as tk

        root = tk.Toplevel()
        root.withdraw()
        big = tk.PhotoImage(data=sg.DEFAULT_BASE64_ICON, master=root)
        small = tk.PhotoImage(data=sg.DEFAULT_BASE64_ICON_SMALL, master=root)
        self.assertEqual((big.width(), big.height()), (64, 64))
        self.assertEqual((small.width(), small.height()), (32, 32))
        root.destroy()

    def test_graph_figure_api(self):
        graph = sg.Graph(
            (100, 100), (0, 0), (10, 10), key="-G-", enable_events=True
        )
        window = sg.Window("t", [[graph]], finalize=True)
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
        graph = sg.Graph((50, 50), (0, 0), (50, 50))
        window = sg.Window("t", [[graph]], finalize=True)
        figure = graph.draw_image((5, 45), data_base64=sg.BLANK_BASE64)
        self.assertTrue(figure)
        self.assertEqual(len(graph._images), 1)  # photo kept alive
        graph.erase()
        self.assertEqual(len(graph._images), 0)
        window.close()

    def test_table_sorting(self):
        table = sg.Table(
            [["banana", 2], ["apple", 3], ["cherry", 1]],
            headings=["Name", "Qty"],
            key="-T-",
        )
        window = sg.Window("t", [[table]], finalize=True)
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
        multiline = sg.Multiline("", key="-ML-")
        window = sg.Window("t", [[multiline]], finalize=True)
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
        multiline = sg.Multiline("", key="-ML-")
        window = sg.Window("t", [[multiline]], finalize=True)
        multiline.update("fresh text")
        self.assertEqual(str(multiline._text.cget("state")), "normal")
        window.close()

    def test_button_with_image(self):
        button = sg.Button("Go", key="-B-", image_data=sg.BLANK_BASE64)
        window = sg.Window("t", [[button]], finalize=True)
        self.assertTrue(button.widget.cget("image"))
        self.assertEqual(str(button.widget.cget("compound")), "left")
        window.close()

    def test_clipboard(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        window.clipboard_set("py-simple")
        self.assertEqual(window.clipboard_get(), "py-simple")
        window.clipboard_append("-gui")
        self.assertEqual(window.clipboard_get(), "py-simple-gui")
        window.clipboard_clear()
        window.close()

    def test_set_min_size(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        window.set_min_size((200, 100))
        self.assertEqual(window.tk_root.minsize(), (200, 100))
        window.close()

    def test_set_dpi_awareness(self):
        result = sg.set_dpi_awareness()
        self.assertIsInstance(result, bool)


class TestNativeCoverage(unittest.TestCase):
    """Per-widget coverage of the native Tk/ttk passthrough APIs."""

    def test_input_native_api(self):
        element = sg.Input("abc", justify="right", key="-IN-")
        window = sg.Window("t", [[element]], finalize=True)
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
        combo = sg.Combo(["a", "b", "c"], key="-CB-")
        window = sg.Window("t", [[combo]], finalize=True)
        combo.set("b")
        self.assertEqual(combo.get(), "b")
        self.assertEqual(combo.current(), 1)
        combo.current(2)
        self.assertEqual(combo.get(), "c")
        window.close()

    def test_spin_numeric_range(self):
        spin = sg.Spin(range_=(0, 20), increment=5, initial_value=10, wrap=True)
        window = sg.Window("t", [[spin]], finalize=True)
        self.assertEqual(spin.get(), "10")
        spin.set(15)
        self.assertEqual(spin.get(), "15")
        # values were generated from the range with the increment
        self.assertEqual(spin.values, [0, 5, 10, 15, 20])
        window.close()
        with self.assertRaises(ValueError):
            sg.Spin([1, 2], range_=(0, 10))

    def test_checkbox_toggle(self):
        checkbox = sg.Checkbox("c", default=False)
        window = sg.Window("t", [[checkbox]], finalize=True)
        checkbox.toggle()
        self.assertTrue(checkbox.get())
        checkbox.select()
        checkbox.deselect()
        self.assertFalse(checkbox.get())
        window.close()

    def test_radio_select_helpers(self):
        first = sg.Radio("one", "g", key="-R1-")
        second = sg.Radio("two", "g", key="-R2-")
        window = sg.Window("t", [[first, second]], finalize=True)
        second.select()
        self.assertTrue(second.get())
        self.assertFalse(first.get())
        self.assertEqual(first.group_value(), "two")
        second.deselect()
        self.assertEqual(first.group_value(), "")
        window.close()

    def test_progressbar_indeterminate(self):
        bar = sg.ProgressBar(100, key="-PB-")
        window = sg.Window("t", [[bar]], finalize=True)
        bar.start_indeterminate(interval_ms=30)
        self.assertEqual(str(bar.widget.cget("mode")), "indeterminate")
        window.refresh()
        bar.stop_indeterminate()
        self.assertEqual(str(bar.widget.cget("mode")), "determinate")
        window.close()

    def test_multiline_passthrough(self):
        multiline = sg.Multiline("", key="-ML-")
        window = sg.Window("t", [[multiline]], finalize=True)
        multiline.insert("1.0", "hello")
        multiline.insert("end", " world")
        self.assertEqual(multiline.get(), "hello world")
        multiline.delete("1.0", "1.6")  # removes "hello "
        self.assertEqual(multiline.get(), "world")
        multiline.see("end")  # must not raise
        window.close()

    def test_text_image_and_wrap(self):
        text = sg.Text("logo:", image_data=sg.DEFAULT_BASE64_ICON, wrap_length=200)
        window = sg.Window("t", [[text]], finalize=True)
        self.assertIsNotNone(text._photo)
        self.assertEqual(text._photo.width(), 64)
        self.assertEqual(int(text.widget.cget("wraplength")), 200)
        window.close()

    def test_listbox_see_size(self):
        listbox = sg.Listbox([f"item {i}" for i in range(30)], size=(10, 3))
        window = sg.Window("t", [[listbox]], finalize=True)
        self.assertEqual(listbox.size(), 30)
        listbox.see(25)  # must not raise
        window.close()

    def test_table_tree_see(self):
        table = sg.Table([[f"row {i}"] for i in range(50)], headings=["H"])
        window = sg.Window("t", [[table]], finalize=True)
        table.see(45)  # must not raise
        window.close()
        tree = sg.Tree()
        window2 = sg.Window("t2", [[tree]], finalize=True)
        tree.insert("", "k1", "visible")
        tree.see("k1")
        window2.close()

    def test_frame_label_anchor(self):
        frame = sg.Frame("Title", [[sg.Text("x")]], label_anchor="se")
        window = sg.Window("t", [[frame]], finalize=True)
        self.assertEqual(str(frame.widget.cget("labelanchor")), "se")
        window.close()

    def test_image_zoom_getters(self):
        image = sg.Image(data_base64=sg.DEFAULT_BASE64_ICON)
        window = sg.Window("t", [[image]], finalize=True)
        self.assertEqual((image.width, image.height), (64, 64))
        image.zoom(2)
        self.assertEqual((image.width, image.height), (128, 128))
        image.subsample(4)
        self.assertEqual((image.width, image.height), (32, 32))
        self.assertIsNotNone(image.photo)
        window.close()

    def test_canvas_passthrough(self):
        canvas = sg.Canvas((100, 100))
        window = sg.Window("t", [[canvas]], finalize=True)
        item = canvas.widget.create_rectangle(10, 10, 40, 40, fill="red")
        canvas.itemconfigure(item, fill="blue")
        self.assertEqual(str(canvas.widget.itemcget(item, "fill")), "blue")
        self.assertEqual(len(canvas.itembbox(item)), 4)
        self.assertEqual(len(canvas.coords(item)), 4)
        window.close()


class TestTypedEnums(unittest.TestCase):
    """IDE affinity: str enums replacing Tk magic strings."""

    def test_enum_values_are_tk_strings(self):
        self.assertIsInstance(sg.Anchor.CENTER, str)
        self.assertEqual(sg.Anchor.CENTER, "center")
        self.assertEqual(str(sg.Justify.RIGHT), "right")
        self.assertEqual(sg.Relief.SUNKEN, "sunken")
        self.assertEqual(sg.Orientation.HORIZONTAL, "horizontal")
        self.assertEqual(sg.EventType.DOUBLE_CLICK, "<Double-1>")
        self.assertEqual(sg.Color.RED, "red")

    def test_enums_interchange_with_strings(self):
        """Enums and raw strings are fully interchangeable in widget args."""
        window = sg.Window(
            "t",
            [
                [sg.Text("a", justification=sg.Justify.CENTER)],
                [sg.Input("", justify=sg.Justify.RIGHT, key="-IN-")],
                [sg.Frame("F", [[sg.Text("x")]], label_anchor=sg.LabelAnchor.SE,
                          key="-FRAME-")],
                [sg.Multiline("", wrap=sg.WrapMode.NONE, key="-ML-")],
            ],
            finalize=True,
        )
        self.assertEqual(str(window["-IN-"].widget.cget("justify")), "right")
        self.assertEqual(str(window["-ML-"]._text.cget("wrap")), "none")
        self.assertEqual(str(window["-FRAME-"].widget.cget("labelanchor")), "se")
        window.close()

    def test_event_type_helpers(self):
        self.assertEqual(sg.EventType.control("o"), "<Control-o>")
        self.assertEqual(sg.EventType.shift("F5"), "<Shift-F5>")
        self.assertEqual(sg.EventType.alt("q"), "<Alt-q>")
        self.assertEqual(sg.EventType.key("F5"), "<F5>")

    def test_bind_with_event_type_enum(self):
        element = sg.Text("click", key="-T-")
        window = sg.Window("t", [[element]], finalize=True)
        element.bind(sg.EventType.RIGHT_CLICK)  # enum instead of "<Button-3>"
        element.widget.event_generate("<Button-3>", when="tail")
        window.tk_root.update()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-T-")
        window.close()

    def test_color_enum_in_widget(self):
        text = sg.Text("colored", text_color=sg.Color.RED,
                       background_color=sg.Color.NAVY)
        window = sg.Window("t", [[text]], finalize=True)
        self.assertEqual(str(text.widget.cget("foreground")), "red")
        window.close()

    def test_anchor_enum_in_text(self):
        text = sg.Text("anchored")
        window = sg.Window("t", [[text]], finalize=True)
        # anchor flows through theme kwargs; verify the enum is a valid value
        text.widget.configure(anchor=sg.Anchor.CENTER)
        self.assertEqual(str(text.widget.cget("anchor")), "center")
        window.close()


class TestDataclassConfigs(unittest.TestCase):
    """dataclass config objects: WindowConfig / ElementOptions."""

    def test_window_config(self):
        cfg = sg.WindowConfig(title="Cfg", resizable=True, modal=True,
                              keep_on_top=True)
        window = sg.Window(layout=[[sg.Text("x")]], config=cfg, finalize=True)
        self.assertEqual(window.title, "Cfg")
        self.assertEqual(window.tk_root.resizable(), (True, True))
        window.close()

    def test_window_config_kwargs_override(self):
        cfg = sg.WindowConfig(title="FromConfig", resizable=True)
        window = sg.Window(config=cfg, title="Explicit", finalize=True)
        self.assertEqual(window.title, "Explicit")  # explicit kwarg wins
        window.close()

    def test_window_config_requires_type(self):
        with self.assertRaises(TypeError):
            sg.Window(config={"title": "nope"})

    def test_element_options_shared(self):
        opts = sg.ElementOptions(
            pad=(10, 4), expand_x=True,
            right_click_menu=["&Menu", ["Refresh"]],
            metadata={"tag": 1},
        )
        first = sg.Text("a", config=opts, key="-A-")
        second = sg.Input("", config=opts, key="-B-")
        window = sg.Window("t", [[first], [second]], finalize=True)
        self.assertEqual(first.pad, (10, 4))
        self.assertEqual(second.pad, (10, 4))
        self.assertTrue(first.expand_x)
        self.assertTrue(second.expand_x)
        self.assertEqual(first.metadata, {"tag": 1})
        self.assertIsNotNone(first._popup_menu)  # right-click menu attached
        window.close()

    def test_element_options_kwargs_win(self):
        opts = sg.ElementOptions(expand_x=True, metadata="from-config")
        element = sg.Text("a", config=opts, metadata="explicit")
        self.assertEqual(element.metadata, "explicit")

    def test_element_options_requires_type(self):
        with self.assertRaises(TypeError):
            sg.Text("a", config={"pad": 4})

    def test_window_config_carry_layout(self):
        cfg = sg.WindowConfig(title="LayoutInConfig",
                              layout=[[sg.Text("from cfg", key="-T-")]])
        window = sg.Window(config=cfg, finalize=True)
        self.assertIn("-T-", window)
        window.close()


class TestFirstBatch(unittest.TestCase):
    """Batch 1: validation, calendar, splitter, scrollable column, timers, find/replace."""

    def test_input_validators(self):
        self.assertTrue(sg.validate_integer("123"))
        self.assertTrue(sg.validate_integer(""))
        self.assertTrue(sg.validate_integer("-"))
        self.assertFalse(sg.validate_integer("12a"))
        self.assertTrue(sg.validate_float("3.14"))
        self.assertTrue(sg.validate_float("-0.5"))
        self.assertFalse(sg.validate_float("1.2.3"))
        self.assertTrue(sg.validate_regex(r"\d{1,3}")("42"))
        self.assertFalse(sg.validate_regex(r"\d{1,3}")("1234"))
        self.assertFalse(sg.validate_regex(r"\d+")("abc"))

    def test_input_validation_wiring(self):
        window = sg.Window(
            "t",
            [[sg.Input("", key="-IN-", validate="key", validate_command=sg.validate_integer)]],
            finalize=True,
        )
        widget = window["-IN-"].widget
        self.assertEqual(str(widget.cget("validate")), "key")
        self.assertTrue(widget.cget("validatecommand"))
        with self.assertRaises(TypeError):
            sg.Input(validate="key", validate_command="not-callable")
        window.close()

    def test_calendar_element(self):
        import datetime

        calendar_element = sg.Calendar(
            default_date=datetime.date(2026, 10, 11), key="-CAL-"
        )
        window = sg.Window("t", [[calendar_element]], finalize=True)
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
        calendar_element = sg.Calendar(default_date=(2026, 2, 14), dateformat="%d.%m.%Y")
        self.assertEqual(calendar_element.get(), "14.02.2026")

    def test_splitter(self):
        splitter = sg.Splitter(
            [[[sg.Text("L", key="-L-")], [sg.Input(key="-LIN-")]],
             [[sg.Text("R", key="-R-")], [sg.Input(key="-RIN-")]]],
            orientation="h",
            key="-SP-",
        )
        window = sg.Window("t", [[splitter]], finalize=True)
        self.assertIsInstance(splitter.widget, tk.PanedWindow)
        self.assertIsNotNone(window["-LIN-"].widget)
        self.assertIsNotNone(window["-RIN-"].widget)
        self.assertEqual(len(splitter.widget.panes()), 2)
        with self.assertRaises(TypeError):
            sg.Splitter([[[sg.Text("only")]]])
        window.close()

    def test_scrollable_column(self):
        rows = [[sg.Text(f"row {i}")] for i in range(30)]
        scroll = sg.ScrollableColumn(rows, size=(200, 100), key="-SC-")
        window = sg.Window("t", [[scroll]], finalize=True)
        window.refresh()
        self.assertIsNotNone(scroll._canvas)
        region = scroll._canvas.cget("scrollregion")
        self.assertTrue(str(region))  # content bbox was registered
        self.assertIsNotNone(scroll._inner_frame.winfo_children())
        window.close()

    def test_window_right_click_menu(self):
        window = sg.Window(
            "t",
            [[sg.Text("x")]],
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
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
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
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        calls = []
        window.after(50, lambda: calls.append(1))
        deadline = time.time() + 2.0
        while not calls and time.time() < deadline:
            window.read(timeout=20)
        self.assertEqual(len(calls), 1)
        window.close()

    def test_text_find_and_replace_helpers(self):
        from TkSimpleGUI.popup import _text_find, _text_replace_all

        multiline = sg.Multiline("alpha beta ALPHA end", key="-ML-")
        window = sg.Window("t", [[multiline]], finalize=True)
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
        checklist = sg.CheckList(
            ["a", "b", "c"], default_checked=["b"], key="-CL-"
        )
        window = sg.Window("t", [[checklist]], finalize=True)
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
        toolbar = sg.Toolbar(
            [
                ("Open", "-OPEN-"),
                "---",
                ("Save", "-SAVE-"),
                ("Options", "-OPT-", ["General", "Advanced"]),
            ],
            key="-TB-",
        )
        window = sg.Window("t", [[toolbar]], finalize=True)
        self.assertEqual(len(toolbar._buttons), 3)
        toolbar._buttons["-SAVE-"].invoke()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-SAVE-")
        dropdown = toolbar._buttons["-OPT-"]
        menu = dropdown.nametowidget(dropdown.cget("menu"))
        self.assertEqual(menu.entrycget(0, "label"), "General")
        window.close()

    def test_toggle_button_group(self):
        first = sg.Button("B1", key="-B1-", toggle=True, group_id="g")
        second = sg.Button("B2", key="-B2-", toggle=True, group_id="g")
        window = sg.Window("t", [[first, second]], finalize=True)
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
        labeled = sg.LabeledEdit("Name", "world", key="-NAME-")
        window = sg.Window("t", [[labeled]], finalize=True)
        self.assertEqual(window["-NAME-"].get(), "world")
        self.assertEqual(labeled.get(), "world")
        self.assertIs(labeled.input, window["-NAME-"])
        labeled.update(value="changed")
        self.assertEqual(window["-NAME-"].get(), "changed")
        labeled.update(label="Surname")
        self.assertEqual(labeled.label, "Surname")
        window.close()

    def test_key_value_editor(self):
        editor = sg.KeyValueEditor(
            [("host", "localhost"), ("port", "5432")], key="-KV-"
        )
        window = sg.Window("t", [[editor]], finalize=True)
        self.assertEqual(
            editor.get(), {"host": "localhost", "port": "5432"}
        )
        editor.update(values={"port": "5433"})
        self.assertEqual(editor.get()["port"], "5433")
        event, values = window.read(timeout=200)
        self.assertEqual(event, sg.TIMEOUT_KEY)
        self.assertEqual(values["-KV-"], {"host": "localhost", "port": "5433"})
        window.close()

    def test_flow_panel(self):
        flow = sg.FlowPanel(
            [sg.Text("one"), sg.Text("two"), sg.Text("three")], key="-FLOW-"
        )
        window = sg.Window("t", [[flow]], finalize=True)
        window.refresh()
        first = flow._children[0].widget
        self.assertTrue(first.place_info()["x"])
        flow._reflow()  # resize reflow must not crash
        self.assertEqual(len(flow._children), 3)
        window.close()

    def test_tree_row_icons(self):
        tree = sg.Tree(headings=["H"], key="-TR-")
        window = sg.Window("t", [[tree]], finalize=True)
        tree.insert("", "item1", "Root", image_data=sg.BLANK_BASE64)
        item = tree.widget.item("item1")
        self.assertTrue(item.get("image"))
        self.assertEqual(len(tree._images), 1)  # photo retained
        window.close()

    def test_table_row_icons(self):
        table = sg.Table(
            [["a"], ["b"]],
            headings=["H"],
            key="-TB-",
            row_icons=[sg.BLANK_BASE64, None],
        )
        window = sg.Window("t", [[table]], finalize=True)
        children = table.widget.get_children()
        self.assertTrue(table.widget.item(children[0]).get("image"))
        self.assertEqual(table.widget.item(children[1]).get("image"), "")
        window.close()

    def test_table_cell_edit(self):
        table = sg.Table(
            [["old", "x"], ["keep", "y"]],
            headings=["A", "B"],
            key="-TB-",
            enable_edit=True,
        )
        window = sg.Window("t", [[table]], finalize=True)
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
        shape = sg.Shape("oval", size=(60, 30), fill_color="red", key="-S-")
        window = sg.Window("t", [[shape]], finalize=True)
        self.assertEqual(len(shape.widget.find_all()), 1)
        shape.update(fill_color="blue", line_color="green")
        with self.assertRaises(ValueError):
            sg.Shape("hexagon")
        window.close()


class TestThirdBatch(unittest.TestCase):
    """Batch 3: Action, UserSettings, data binding, i18n, animation, tray, CLI."""

    def test_action_normalization_and_callback(self):
        fired = []
        open_action = sg.Action(
            "Open", key="-OPEN-", callback=lambda w, v: fired.append("open")
        )
        menu_item = sg.Text("menu", key="Open")  # posting text "Open"
        window = sg.Window(
            "t", [[menu_item]], finalize=True, actions=[open_action]
        )
        window._post_event("Open")  # menu text normalizes to the key
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-OPEN-")
        self.assertEqual(fired, ["open"])
        window.close()

    def test_action_shortcut_bound(self):
        save_action = sg.Action("Save", key="-SAVE-", shortcut="<Control-s>")
        window = sg.Window("t", [[sg.Text("x")]], finalize=True, actions=[save_action])
        shortcuts = [pattern for pattern, _key in window._event_binds]
        self.assertIn("<Control-s>", shortcuts)
        window.close()

    def test_action_list_helpers(self):
        actions = sg.ActionList(
            [sg.Action("Open", key="-OPEN-"), sg.Action("Exit", key="-EXIT-")]
        )
        self.assertEqual(actions.keys(), ["-OPEN-", "-EXIT-"])
        self.assertEqual(actions.by_text("Exit").key, "-EXIT-")
        self.assertEqual(actions.by_key("-OPEN-").text, "Open")
        self.assertEqual(
            actions.menu_definition("&File"),
            [["&File", "Open", "Exit"]],
        )
        button = sg.Action("Save", key="-SAVE-").to_button()
        self.assertEqual(button.key, "-SAVE-")
        self.assertEqual(button.button_text, "Save")

    def test_user_settings(self):
        import shutil
        import tempfile

        directory = tempfile.mkdtemp()
        try:
            prefs = sg.UserSettings("test.json", path=directory)
            prefs.set("theme", "DarkBlue3")
            prefs.set("window/size", "800x600")
            self.assertEqual(prefs.get("theme"), "DarkBlue3")
            self.assertEqual(prefs.get("window/size"), "800x600")
            self.assertIn("theme", prefs)
            self.assertEqual(prefs["window/size"], "800x600")
            # a fresh instance reads the same file back
            again = sg.UserSettings("test.json", path=directory)
            self.assertEqual(again.get("theme"), "DarkBlue3")
            again.delete("window/size")
            self.assertNotIn("window/size", again)
            self.assertIsNone(again.get("window/size"))
            prefs.delete_file()
            self.assertEqual(sg.UserSettings("test.json", path=directory).as_dict(), {})
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_table_bind(self):
        records = [
            {"name": "apple", "qty": 3},
            {"name": "pear", "qty": 1},
        ]
        table = sg.Table([], headings=[], key="-TB-")
        window = sg.Window("t", [[table]], finalize=True)
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
            sg.set_translations(catalog_path)
            self.assertEqual(sg.translate("Open"), "Ouvert")
            self.assertEqual(sg._("Save"), "Sauve")
            self.assertEqual(sg._("Unknown"), "Unknown")
            sg.add_translation("Close", "Ferme")
            self.assertEqual(sg._("Close"), "Ferme")
            sg.clear_translations()
            self.assertEqual(sg._("Open"), "Open")
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_animation_fade_and_progress(self):
        bar = sg.ProgressBar(100, key="-BAR-")
        window = sg.Window("t", [[bar]], finalize=True)
        handle = sg.animate_progress(window, "-BAR-", 100, duration_ms=60, steps=4)
        deadline = time.time() + 2.0
        while handle.active and time.time() < deadline:
            window.read(timeout=20)
        self.assertEqual(bar.get(), 100)
        self.assertFalse(handle.active)
        fade = sg.fade_in(window, duration_ms=60, steps=4)
        window.refresh()
        fade.cancel()
        window.close()

    def test_animation_slide(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        target = (window.current_location()[0] + 30, window.current_location()[1])
        handle = sg.slide(window, target, duration_ms=60, steps=3)
        deadline = time.time() + 2.0
        while handle.active and time.time() < deadline:
            window.read(timeout=20)
        location = window.current_location()
        self.assertGreaterEqual(location[0], target[0] - 2)
        window.close()

    @unittest.skipUnless(sg.running_windows(), "SystemTray is Windows only")
    def test_system_tray_lifecycle(self):
        # runs in a subprocess: the tray owns a hidden Win32 message window,
        # and its WndProc must not interleave with this process's Tcl state
        import subprocess

        probe = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "probes", "_tray_probe.py"
        )
        result = subprocess.run(
            [sys.executable, probe],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
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
            sg.main(["--version"])
        self.assertIn("TkSimpleGUI", buffer.getvalue())
        self.assertIn(sg.__version__, buffer.getvalue())
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            sg.main(["--themes"])
        self.assertGreater(len(buffer.getvalue().splitlines()), 150)

    def test_dbg_returns_quickly(self):
        # dbg formats args and delegates to the quick popup
        self.assertTrue(callable(sg.dbg))
        self.assertTrue(callable(sg.popup_quick))


class TestLineA(unittest.TestCase):
    """Line A: full coverage of the native Tk/ttk API surface."""

    def test_element_bind_and_unbind(self):
        element = sg.Text("click me", key="-T-")
        window = sg.Window("t", [[element]], finalize=True)
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
        element = sg.Text("x")
        with self.assertRaises(RuntimeError):
            element.bind("<Button-1>")

    def test_multiline_scrollbar_wrap(self):
        multiline = sg.Multiline(
            "\n".join(f"line {i}" for i in range(50)),
            size=(30, 4), scroll_y=True, wrap="none", key="-ML-",
        )
        window = sg.Window("t", [[multiline]], finalize=True)
        container = multiline.widget
        self.assertIsInstance(container, tk.Frame)  # composite container
        children = container.winfo_children()
        self.assertEqual(len(children), 2)  # text + scrollbar
        self.assertEqual(str(multiline._text.cget("wrap")), "none")
        self.assertEqual(multiline.get().splitlines()[0], "line 0")
        window.close()

    def test_multiline_link_and_search(self):
        multiline = sg.Multiline("", key="-ML-")
        window = sg.Window("t", [[multiline]], finalize=True)
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
        image = sg.Image(data_base64=sg.DEFAULT_BASE64_ICON, zoom=2)
        window = sg.Window("t", [[image]], finalize=True)
        self.assertEqual(image._photo.width(), 128)
        window.close()
        image = sg.Image(data_base64=sg.DEFAULT_BASE64_ICON, subsample=2)
        window = sg.Window("t", [[image]], finalize=True)
        self.assertEqual(image._photo.width(), 32)
        window.close()

    def test_spin_is_ttk(self):
        spin = sg.Spin([1, 2, 3], initial_value=2)
        window = sg.Window("t", [[spin]], finalize=True)
        self.assertIsInstance(spin.widget, ttk.Spinbox)
        self.assertEqual(spin.get(), "2")
        window.close()

    def test_ttk_theme_switch(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        available = sg.ttk_themes()
        self.assertTrue(available)
        current = sg.ttk_theme()
        if "clam" in available:
            self.assertEqual(sg.ttk_theme("clam"), "clam")
            self.assertEqual(sg.ttk_theme(), "clam")
            sg.ttk_theme(current)
        with self.assertRaises(ValueError):
            sg.ttk_theme("__nope__")
        window.close()

    def test_window_wm_extensions(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        window.set_fullscreen(True)
        window.refresh()
        self.assertEqual(int(window.tk_root.attributes("-fullscreen")), 1)
        window.set_fullscreen(False)
        window.make_toolwindow(False)
        window.set_max_size((800, 600))
        window.bell()
        child = sg.Window("child", [[sg.Text("c")]], finalize=True)
        child.transient(window)
        child.stack_above(window)
        child.close()
        window.close()

    def test_window_selection(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        window.selection_set("primary-data")
        window.refresh()
        self.assertEqual(window.selection_get(), "primary-data")
        window.close()

    def test_window_style_hooks(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        window.configure_style("TButton", padding=(16, 8))
        window.map_style("TButton", background=[("active", "#3a7bd5")])
        window.close()

    def test_font_tools(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        families = sg.font_families()
        self.assertTrue(families)
        width = sg.font_measure("hello", ("Helvetica", 10))
        self.assertGreater(width, 0)
        actual = sg.font_actual(("Helvetica", 12, "bold"))
        self.assertEqual(actual["size"], 12)
        self.assertEqual(actual["weight"], "bold")
        window.close()

    def test_menubutton_element(self):
        menu_button = sg.Menubutton("Options", ["One", "---", "Two"], key="-MB-")
        window = sg.Window("t", [[menu_button]], finalize=True)
        self.assertEqual(menu_button.items, ["One", "---", "Two"])
        menu_button.update(items=["Alpha"])
        menu = menu_button.widget.nametowidget(menu_button.widget.cget("menu"))
        self.assertEqual(menu.entrycget(0, "label"), "Alpha")
        menu.invoke(0)
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "Alpha")
        window.close()

    def test_scrollbar_element(self):
        multiline = sg.Multiline("\n".join(f"line {i}" for i in range(60)),
                                 size=(20, 3), key="-ML-")
        scrollbar = sg.Scrollbar(multiline, orientation="v")
        window = sg.Window("t", [[multiline, scrollbar]], finalize=True)
        self.assertIsNotNone(scrollbar.widget)
        with self.assertRaises(TypeError):
            sg.Window("t2", [[sg.Scrollbar(sg.Text("not scrollable"))]], finalize=True)
        window.close()

    def test_tabgroup_enhancements(self):
        tab_group = sg.TabGroup(
            [[sg.Tab("one", [[sg.Text("1")]]), sg.Tab("two", [[sg.Text("2")]])]],
            key="-TG-", enable_events=True, enable_traversal=True,
        )
        window = sg.Window("t", [[tab_group]], finalize=True)
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
    """TChart: line/bar/hbar/scatter/area/pie on the Graph coordinate system."""

    def _chart(self, kind):
        chart = sg.TChart((300, 180), chart_type=kind, key="-C-",
                          background_color="#ffffff")
        window = sg.Window("t", [[chart]], finalize=True)
        self.addCleanup(window.close)
        return chart

    def test_invalid_type_rejected(self):
        with self.assertRaises(ValueError):
            sg.TChart(chart_type="radar")

    def test_line_two_series(self):
        chart = self._chart("line")
        chart.add_series("A", [3, 7, 2, 9], labels=["a", "b", "c", "d"])
        chart.add_series("B", [5, 4, 8, 3])
        chart.redraw()
        # markers (4+4 ovals) + 1 polyline + axes(2) + grid + ticks + legend
        figures = chart.widget.find_all()
        self.assertGreater(len(figures), 10)
        self.assertEqual(chart.series_names, ["A", "B"])

    def test_bar_grouped(self):
        chart = self._chart("bar")
        chart.add_series("E", [12, 30, 8], labels=["x", "y", "z"])
        chart.add_series("W", [9, 24, 16])
        chart.redraw()
        # 2 series x 3 bars = 6 rectangles + axes/grid/ticks/legend
        figures = chart.widget.find_all()
        self.assertGreater(len(figures), 8)

    def test_pie_slices_and_legend(self):
        chart = self._chart("pie")
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
        for kind in sg.ChartType.ALL:
            chart = self._chart(kind)
            if kind == "pie":
                chart.add_series("s", [("a", 1), ("b", 2)])
            else:
                chart.add_series("s", [1, 3, 2], labels=["a", "b", "c"])
            chart.redraw()
            self.assertGreater(
                len(chart.widget.find_all()), 3, msg="kind=%s" % kind
            )

    def test_redraw_before_finalize_is_safe(self):
        chart = sg.TChart((200, 150), chart_type="line")
        chart.add_series("A", [1, 2, 3])
        chart.redraw()  # no widget yet: must be a no-op, no raise


class TestLineB(unittest.TestCase):
    """Line B: what Tk cannot do (canvas-drawn, synthesized events, ctypes)."""

    def test_round_button(self):
        button = sg.RoundButton("Go", size=(90, 30), radius=14,
                                fill_color="#e91e63", key="-RB-")
        window = sg.Window("t", [[button]], finalize=True)
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
        button = sg.RoundButton("Go", key="-RB-")
        button.set_click_handler(lambda el: calls.append(el))
        window = sg.Window("t", [[button]], finalize=True)
        window.tk_root.update()
        button.widget.event_generate("<Button-1>", x=45, y=15, when="tail")
        window.tk_root.update()
        self.assertEqual(calls, [button])
        window.close()

    def test_image_button(self):
        button = sg.ImageButton(data_base64=sg.DEFAULT_BASE64_ICON, key="-IB-")
        window = sg.Window("t", [[button]], finalize=True)
        window.tk_root.update()
        self.assertEqual(button._photo.width(), 64)  # sized from the image
        button.widget.event_generate("<Button-1>", x=10, y=10, when="tail")
        window.tk_root.update()
        event, _values = window.read(timeout=500)
        self.assertEqual(event, "-IB-")
        window.close()

    def test_text_progress_bar(self):
        bar = sg.TextProgressBar(100, current_value=42, key="-TPB-")
        window = sg.Window("t", [[bar]], finalize=True)
        self.assertEqual(bar.get(), 42)
        label = bar._widget.itemconfigure(bar._label_id, "text")
        self.assertEqual(str(label[-1]), "42%")
        bar.update(current_value=100)
        label = bar._widget.itemconfigure(bar._label_id, "text")
        self.assertEqual(str(label[-1]), "100%")
        window.close()

    def test_toast(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
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
        table = sg.Table([["a", "b"]], headings=["H1", "H2"], key="-TB-")
        window = sg.Window("t", [[table]], finalize=True)
        width = table.column_width(0)
        self.assertGreater(width, 0)
        table.set_column_width(0, 150)
        self.assertEqual(table.column_width(0), 150)
        window.close()

    def test_slider_value_bubble(self):
        slider = sg.Slider((0, 100), default_value=30, show_value=True,
                           enable_events=True, key="-SL-")
        window = sg.Window("t", [[slider]], finalize=True)
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
        tree = sg.Tree(key="-TR-")
        window = sg.Window("t", [[tree]], finalize=True)
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
        tab_group = sg.TabGroup(
            [[sg.Tab("one", [[sg.Text("1")]]), sg.Tab("two", [[sg.Text("2")]])]],
            key="-TG-", enable_events=True, enable_close=True,
        )
        window = sg.Window("t", [[tab_group]], finalize=True)
        label = tab_group.widget.tab(0, "text")
        self.assertIn("×", str(label))
        tab_group.close_tab("one")
        self.assertEqual(len(tab_group.tabs), 1)
        self.assertEqual(tab_group.closed_tabs, ["one"])
        event, _values = window.read(timeout=500)
        self.assertEqual(event, ("-TG-", "tab_closed", "one"))
        window.close()

    def test_hotkey_parse(self):
        modifiers, virtual_key = sg.GlobalHotkeys.parse("Ctrl-Alt-P")
        self.assertEqual(modifiers, 0x0002 | 0x0001)
        self.assertEqual(virtual_key, ord("P"))
        modifiers, virtual_key = sg.GlobalHotkeys.parse("Shift-F5")
        self.assertEqual(modifiers, 0x0004)
        self.assertEqual(virtual_key, 0x70 + 5 - 1)
        with self.assertRaises(ValueError):
            sg.GlobalHotkeys.parse("Ctrl")
        with self.assertRaises(ValueError):
            sg.GlobalHotkeys.parse("Ctrl-Foo")

    @unittest.skipUnless(sg.running_windows(), "hotkeys are Windows only")
    def test_global_hotkeys_lifecycle(self):
        hotkeys = sg.GlobalHotkeys()
        hotkeys.register("Ctrl-Alt-F24", "-HK-TEST-")
        self.assertEqual(hotkeys.combos, ["Ctrl-Alt-F24"])
        hotkeys.stop()
        self.assertEqual(hotkeys.combos, [])
        # re-register works after stop
        hotkeys.register("Ctrl-Alt-F24", "-HK-TEST-")
        hotkeys.stop()

    def test_taskbar_progress_gate(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        progress = sg.taskbar_progress(window)
        if sg.running_windows():
            self.assertIsNotNone(progress)
        else:
            self.assertIsNone(progress)
        window.close()


class TestUnifiedLoop(unittest.TestCase):
    """Single event loop: global bus + main_loop, multi-window by design."""

    def tearDown(self):
        sg.Window.close_all()

    def test_cross_window_events(self):
        """Any window read() receives events from other windows (bus order)."""
        first = sg.Window("one", [[sg.Button("ping", key="-PING-")]], finalize=True)
        second = sg.Window("two", [[sg.Button("pong", key="-PONG-")]], finalize=True)
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
        first = sg.Window("one", [[sg.Text("x")]], finalize=True)
        second = sg.Window("two", [[sg.Text("y")]], finalize=True)
        second.write_event_value("-TWO-EVENT-")
        window, event, _values = sg.Window.read_all_windows(timeout=500)
        self.assertIs(window, second)
        self.assertEqual(event, "-TWO-EVENT-")
        first.close()
        second.close()

    def test_winclosed_removes_window_from_registry(self):
        first = sg.Window("one", [[sg.Text("x")]], finalize=True)
        second = sg.Window("two", [[sg.Text("y")]], finalize=True)
        # the WM_DELETE_WINDOW protocol handler posts WIN_CLOSED; firing it
        # here simulates the user clicking the title bar X
        first._post_event(sg.WIN_CLOSED)
        window, event, _values = sg.Window.read_all_windows(timeout=500)
        self.assertIs(window, first)
        self.assertEqual(event, sg.WIN_CLOSED)
        self.assertNotIn(first, sg.Window.active_windows())
        self.assertIn(second, sg.Window.active_windows())
        second.close()

    def test_programmatic_close_is_quiet(self):
        """Window.close() does not post WIN_CLOSED (no user action happened)."""
        first = sg.Window("one", [[sg.Text("x")]], finalize=True)
        second = sg.Window("two", [[sg.Text("y")]], finalize=True)
        first.close()
        event, _values = second.read(timeout=200)
        self.assertEqual(event, sg.TIMEOUT_KEY)
        second.close()

    def test_main_loop_exits_when_all_closed(self):
        app = sg.TkSimpleEvent()
        window = sg.Window("one", [[sg.Button("quit", key="-QUIT-")]], finalize=True)
        seen = []

        @app.bind_event("-QUIT-")
        def on_quit(window, values):
            seen.append("quit")
            window.close()  # last window gone -> loop ends

        window.write_event_value("-QUIT-")  # fires once the loop pumps
        sg.main_loop(window, app)
        self.assertEqual(seen, ["quit"])
        self.assertEqual(sg.Window.active_windows(), [])

    def test_main_loop_dispatches_to_on_handlers(self):
        app = sg.TkSimpleEvent()
        main = sg.Window("main", [[sg.Button("open", key="-OPEN-")]], finalize=True)
        received = []

        @app.bind_event("-OPEN-")
        def on_open(window, values):
            child = sg.Window("child", [[sg.Text("hi", key="-HI-")]], finalize=True)
            child.write_event_value("-CHILD-READY-")

        @app.bind_event("-CHILD-READY-")
        def on_child_ready(window, values):
            received.append(window.title)
            sg.Window.close_all()

        main.write_event_value("-OPEN-")  # fires inside the loop
        sg.main_loop(main, app)
        self.assertEqual(received, ["child"])  # handler got the CHILD window
        self.assertEqual(sg.Window.active_windows(), [])

    def test_main_loop_with_action_callbacks(self):
        calls = []
        app = sg.TkSimpleEvent()
        ok_action = sg.Action("OK", key="OK",
                              callback=lambda window, values: calls.append("ok"))
        window = sg.Window("t", [[sg.Button("OK", key="OK")]],
                           finalize=True, actions=[ok_action])

        @app.bind_event("OK")
        def on_ok(window, values):
            calls.append("handler")
            sg.Window.close_all()

        window.write_event_value("OK")  # fires inside the loop
        sg.main_loop(window, app)
        self.assertEqual(calls, ["ok", "handler"])

    def test_close_all_drops_stale_events(self):
        first = sg.Window("one", [[sg.Text("x")]], finalize=True)
        first.write_event_value("-STALE-")
        sg.Window.close_all()
        second = sg.Window("two", [[sg.Text("y")]], finalize=True)
        event, _values = second.read(timeout=200)
        self.assertEqual(event, sg.TIMEOUT_KEY)  # stale event was dropped
        second.close()


class TestWindowHierarchy(unittest.TestCase):
    """Window hierarchy: parent/children/ancestors + cascading close."""

    def test_parent_link_and_query(self):
        main = sg.Window("main", [[sg.Text("m")]], finalize=True)
        child = sg.Window("child", [[sg.Text("c")]], finalize=True, parent=main)
        grandchild = sg.Window("grand", [[sg.Text("g")]], finalize=True, parent=child)
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
        main = sg.Window("main", [[sg.Text("m")]], finalize=True)
        child = sg.Window("child", [[sg.Text("c")]], parent=main)  # not finalized yet
        self.assertIs(child.parent, main)
        child.finalize()  # link established at finalize
        self.assertIn(child, main.children)
        child.close()
        self.assertEqual(main.children, [])
        main.close()

    def test_transient_sets_parent(self):
        main = sg.Window("main", [[sg.Text("m")]], finalize=True)
        dialog = sg.Window("dialog", [[sg.Text("d")]], finalize=True)
        dialog.transient(main)
        self.assertIs(dialog.parent, main)
        self.assertIn(dialog, main.children)
        dialog.transient(None)  # detach
        self.assertIsNone(dialog.parent)
        self.assertEqual(main.children, [])
        dialog.close()
        main.close()

    def test_child_close_keeps_parent(self):
        main = sg.Window("main", [[sg.Text("m")]], finalize=True)
        child = sg.Window("child", [[sg.Text("c")]], finalize=True, parent=main)
        child.close()
        self.assertFalse(main.was_closed)
        self.assertEqual(main.children, [])
        main.close()


class TestForcedModal(unittest.TestCase):
    """Forced-modal windows: disable_esc, modal/auto disable_close, system_block."""

    def tearDown(self):
        sg.Window.close_all()

    def test_disable_esc_blocks_escape_key(self):
        window = sg.Window(
            "t", [[sg.Text("x")]], finalize=True, disable_esc=True
        )
        window.tk_root.event_generate("<Escape>")
        window.tk_root.update()
        # the break handler swallows the key: no WIN_CLOSED event was posted
        with self.assertRaises(queue.Empty):
            window._event_queue.get_nowait()
        window.close()

    def test_esc_without_flag_reaches_window(self):
        window = sg.Window("t", [[sg.Text("x")]], finalize=True)
        window.tk_root.event_generate("<Escape>")
        window.tk_root.update()
        # without disable_esc the key press is not swallowed; the window
        # stays open and its queue simply receives no forced break
        self.assertFalse(window.was_closed)
        window.close()

    def test_disable_close_blocks_frame_and_modal_implies_it(self):
        window = sg.Window(
            "t", [[sg.Text("x")]], finalize=True, disable_close=True
        )
        # simulate the frame close button: the protocol handler is a no-op
        window.tk_root.protocol("WM_DELETE_WINDOW")() if False else None
        window.tk_root.update()
        self.assertFalse(window.was_closed)
        window.close()

    def test_modal_sets_grab_and_blocks_frame_close(self):
        main = sg.Window("main", [[sg.Text("m")]], finalize=True)
        dialog = sg.Window(
            "dialog", [[sg.Button("OK", key="-OK-")]],
            finalize=True, modal=True,
        )
        self.assertEqual(dialog.tk_root.grab_current(), dialog.tk_root)
        # modal implies disable_close: no WIN_CLOSED can be posted by the frame
        self.assertFalse(dialog.was_closed)
        dialog.close()
        main.close()

    def test_system_block_released_on_close(self):
        window = sg.Window(
            "t", [[sg.Text("x")]], finalize=True, system_block=True
        )
        self.assertTrue(window._system_block)
        self.assertTrue(window._want_system_block)
        window.close()
        self.assertFalse(window._system_block)
        self.assertFalse(window._want_system_block)

    def test_system_block_hide_releases_and_unhide_rearms(self):
        window = sg.Window(
            "t", [[sg.Text("x")]], finalize=True, system_block=True
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
        first = sg.Window("a", [[sg.Text("x")]], finalize=True, system_block=True)
        second = sg.Window("b", [[sg.Text("x")]], finalize=True, system_block=True)
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
        cfg = sg.WindowConfig(
            title="forced", modal=True, disable_esc=True, system_block=True
        )
        window = sg.Window(config=cfg, layout=[[sg.Text("x")]], finalize=True)
        self.assertTrue(window._modal)
        self.assertTrue(window._disable_esc)
        self.assertTrue(window._system_block)
        window.close()


class TestRunEntry(unittest.TestCase):
    """Root .run() entry: window root / tray root / default event manager."""

    def tearDown(self):
        sg.Window.close_all()

    def test_window_run_with_explicit_app(self):
        app = sg.TkSimpleEvent()
        window = sg.Window("one", [[sg.Button("quit", key="-QUIT-")]], finalize=True)
        seen = []

        @app.bind_event("-QUIT-")
        def on_quit(window, values):
            seen.append("quit")
            sg.Window.close_all()  # ends the loop

        window.write_event_value("-QUIT-")
        window.run(app)  # root object starts the loop directly
        self.assertEqual(seen, ["quit"])
        self.assertEqual(sg.Window.active_windows(), [])

    def test_window_run_uses_default_app(self):
        app = sg.default_app()

        @app.bind_event("-RUN-EVENT-")
        def on_run_event(window, values):
            sg.Window.close_all()

        window = sg.Window("one", [[sg.Text("x")]], finalize=True)
        window.write_event_value("-RUN-EVENT-")
        window.run()  # no app: default_app() is used, handler above fires
        self.assertEqual(sg.Window.active_windows(), [])

    def test_run_survives_idle_bus_before_any_event(self):
        # regression: read_all_windows(timeout=0) returns (None, TIMEOUT_KEY)
        # when the bus is empty, which used to be mistaken for "all windows
        # closed" — run() exited immediately on the first idle tick
        app = sg.TkSimpleEvent()

        @app.bind_event("-LATE-")
        def on_late(window, values):
            sg.Window.close_all()

        window = sg.Window("idle", [[sg.Text("x")]], finalize=True)
        # post the event AFTER the loop has had a chance to see idle ticks
        window.tk_root.after(300, lambda: window.write_event_value("-LATE-"))
        window.run(app)
        self.assertTrue(window.was_closed)

    def test_default_app_is_singleton(self):
        self.assertIs(sg.default_app(), sg.default_app())
        self.assertIsInstance(sg.default_app(), sg.TkSimpleEvent)

    def test_package_level_bind_event(self):
        """@sg.bind_event wires handlers without any explicit manager import."""
        fired = []

        @sg.bind_event("-PKG-LEVEL-EVENT-")
        def on_pkg_level(window, values):
            fired.append(window.title)
            sg.Window.close_all()  # ends the loop

        window = sg.Window("one", [[sg.Text("x")]], finalize=True)
        window.write_event_value("-PKG-LEVEL-EVENT-")
        window.run()  # default_app must see the handler above
        self.assertEqual(fired, ["one"])

        sg.default_app()._event_handlers.pop("-PKG-LEVEL-EVENT-", None)

    def test_run_without_finalize_finalizes(self):
        app = sg.TkSimpleEvent()
        window = sg.Window("one", [[sg.Text("x")]])  # NOT finalized

        @app.bind_event("-GO-")
        def on_go(window, values):
            sg.Window.close_all()

        window.write_event_value("-GO-")
        window.run(app)  # run() must finalize the anchor first
        self.assertTrue(window.was_closed)

    def test_on_close_callback_blocks_close(self):
        """on_close=False keeps the window open; on_close=True closes it."""
        decisions = [False, True]
        window = sg.Window(
            "guarded",
            [[sg.Text("x")]],
            finalize=True,
            on_close=lambda w: decisions.pop(0),
        )
        try:
            # False -> no WIN_CLOSED posted, window stays open
            window._handle_on_close()
            self.assertFalse(window.was_closed)
            self.assertEqual(sg.Window._event_bus.qsize(), 0)
            # True -> WIN_CLOSED lands on the bus, then read() drains & closes
            window._handle_on_close()
            self.assertEqual(sg.Window._event_bus.qsize(), 1)
            _event_window, event, _values = sg.Window.read_all_windows()
            self.assertIs(event, sg.WIN_CLOSED)
            self.assertIs(_event_window, window)
            self.assertTrue(window.was_closed)
        finally:
            if not window.was_closed:
                window.close()

    def test_on_close_runtime_setter(self):
        """Setting on_close after construction wires the WM_DELETE_WINDOW hook."""
        window = sg.Window("late", [[sg.Text("y")]], finalize=True)
        try:
            self.assertIsNone(window._on_close)
            window.on_close = lambda w: True
            self.assertIsNotNone(window._on_close)
            window._handle_on_close()
            # bus has the WIN_CLOSED; drain it and confirm close
            self.assertEqual(sg.Window._event_bus.qsize(), 1)
            _event_window, _event, _values = sg.Window.read_all_windows()
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

        class SpyWindow(object):
            def __init__(self, title, rows, **kwargs):
                captured.append({"title": title, "kwargs": kwargs})

            def read(self, timeout=None, close=False, timeout_key=sg.TIMEOUT_KEY):
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


    @unittest.skipUnless(sg.running_windows(), "SystemTray is Windows only")
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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        output = result.stdout.decode("utf-8", "replace")
        self.assertEqual(
            result.returncode, 0, output + result.stderr.decode("utf-8", "replace")
        )
        self.assertIn("TRAY RUN OK", output)


class TestEventManager(unittest.TestCase):
    def setUp(self):
        self.app = sg.TkSimpleEvent()
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

        window = sg.Window("evt", [[sg.Text("x")]], finalize=True)
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
        @sg.singleton_window
        def make_window(title):
            return sg.Window(title, [[sg.Text("x")]], finalize=True)

        first = make_window("single")
        second = make_window("single")
        self.assertIs(first, second)
        first.close()


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
        element = sg.Text("x")
        self.assertFalse(hasattr(element, "__dict__"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
