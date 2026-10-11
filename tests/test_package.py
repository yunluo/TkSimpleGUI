#!/usr/bin/env python3
"""PySimpleGUI4 OO package test suite (unittest, headless friendly)."""

import ast
import os
import sys
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
