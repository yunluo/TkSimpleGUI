#!/usr/bin/env python3
"""PySimpleGUI4 OO package test suite (unittest, headless friendly)."""

import ast
import os
import sys
import time
import tkinter as tk
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import PySimpleGUI4 as sg  # noqa: E402


class TestMeta(unittest.TestCase):
    def test_version(self):
        self.assertEqual(sg.__version__, "4.80.7")

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
        self.assertIs(sg.T, sg.Text)
        self.assertIs(sg.B, sg.Button)
        self.assertIs(sg.InputText, sg.Input)
        self.assertIs(sg.DD, sg.Combo)
        self.assertIs(sg.Col, sg.Column)
        self.assertIs(sg.ProgBar, sg.ProgressBar)

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
            [[sg.TabGroup([[sg.Tab("one", [[sg.Text("1", key="-1-")]]), sg.Tab("two", [[sg.Text("2", key="-2-")]])]])]],
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
        from PySimpleGUI4.elements.base import _parse_pad

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
                    [sg.Input("", key="-IN-"), sg.Combo(["a"], key="-CB-"), sg.Checkbox("c", key="-CK-")],
                    [sg.Button("B", key="-B-"), sg.Radio("r", 1, key="-R-"), sg.Slider((0, 10))],
                    [sg.Table([["a"]], headings=["H"], key="-TB-"), sg.Tree(headings=["H"], key="-TR-")],
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
        multiline.widget.insert("end", "extra")
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
        self.assertEqual(str(multiline.widget.cget("state")), "normal")
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


class TestFirstBatch(unittest.TestCase):
    """第一批：校验/日历/分栏/滚动容器/窗体右键/定时器/查找替换。"""

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
        rows = [[sg.Text("row {}".format(i))] for i in range(30)]
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
        from PySimpleGUI4.popup import _text_find, _text_replace_all

        multiline = sg.Multiline("alpha beta ALPHA end", key="-ML-")
        window = sg.Window("t", [[multiline]], finalize=True)
        widget = multiline.widget
        pos = _text_find(widget, "beta")
        self.assertEqual(pos, "1.6")
        pos = _text_find(widget, "BETA", case_sensitive=True)
        self.assertIsNone(pos)
        pos = _text_find(widget, "ALPHA", case_sensitive=True)
        self.assertEqual(pos, "1.11")
        # case insensitive search hits the earliest match ("beta" at col 6)
        pos = _text_find(widget, "BETA")
        self.assertEqual(pos, "1.6")
        self.assertIsNone(_text_find(widget, ""))
        count = _text_replace_all(widget, "alpha", "delta")
        self.assertEqual(count, 2)  # case insensitive: "alpha" AND "ALPHA"
        self.assertEqual(multiline.get(), "delta beta delta end")
        count = _text_replace_all(widget, "", "x")
        self.assertEqual(count, 0)
        window.close()


class TestEventManager(unittest.TestCase):
    def setUp(self):
        self.app = sg.PySimpleEvent()
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


class TestPy34Compatibility(unittest.TestCase):
    def test_no_fstrings(self):
        package_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "PySimpleGUI4"
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
                    if isinstance(node, ast.JoinedStr):
                        offenders.append(os.path.basename(path))
        self.assertEqual(offenders, [])

    def test_slots_encapsulation(self):
        element = sg.Text("x")
        self.assertFalse(hasattr(element, "__dict__"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
