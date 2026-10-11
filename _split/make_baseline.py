# -*- coding: utf-8 -*-
"""Build the clean split baseline from ___PySimpleGUI4.py.

Applies the minimum required fixes:
1. remove `import webbrowser` (no external requests)
2. neutralize the single webbrowser.open_new_tab call in the SDK help window
3. convert the active f-string + commented f-strings to .format() (Python 3.4 rule)
"""
import io
import sys

SRC = "___PySimpleGUI4.py"
DST = "_split/baseline.py"

with open(SRC, "r", encoding="utf-8") as f:
    text = f.read()

REPLACEMENTS = [
    # (old, new)
    ("import webbrowser\n", ""),
    (
        "                if online_help_link:\n"
        "                    webbrowser.open_new_tab(online_help_link)\n",
        "                if online_help_link:\n"
        "                    pass  # webbrowser removed: no external requests\n",
    ),
    (
        '            f"+{event.x_root - self._mouse_offset_x}+{event.y_root - self._mouse_offset_y}"\n',
        '            "+{}+{}".format(event.x_root - self._mouse_offset_x, event.y_root - self._mouse_offset_y)\n',
    ),
    (
        '        # _logger.info(f"+{event.x_root}+{event.y_root}")',
        '        # _logger.info("+{}+{}".format(event.x_root, event.y_root))',
    ),
    (
        "# _logger.info(f'++++++ making a new SectionDict with name = {section_name}')",
        "# _logger.info('++++++ making a new SectionDict with name = {}'.format(section_name))",
    ),
    (
        "# _logger.info(f'** Section Dict deleting section = {self.section_name}')",
        "# _logger.info('** Section Dict deleting section = {}'.format(self.section_name))",
    ),
    (
        "# _logger.info(f'*** In SectionDict SET *** item = {item} value = {value}')",
        "# _logger.info('*** In SectionDict SET *** item = {} value = {}'.format(item, value))",
    ),
    (
        "# _logger.info(f'** In SectionDict delete! section name = {self.section_name} item = {item} ')",
        "# _logger.info('** In SectionDict delete! section name = {} item = {}'.format(self.section_name, item))",
    ),
    (
        "# _logger.info(f'** Trying to delete an entry with a config file in use ** id of section_dict = {id(section_dict)}')",
        "# _logger.info('** Trying to delete an entry with a config file in use ** id of section_dict = {}'.format(id(section_dict)))",
    ),
]

for old, new in REPLACEMENTS:
    count = text.count(old)
    if count != 1:
        print("FAIL: expected 1 occurrence, got {}: {!r}".format(count, old[:60]))
        sys.exit(1)
    text = text.replace(old, new)

with open(DST, "w", encoding="utf-8", newline="") as f:
    f.write(text)

# verify
import ast

ast.parse(text)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
print("BASELINE OK: {} lines".format(len(text.splitlines())))
print("webbrowser remaining:", text.count("webbrowser"))
print('f-string remaining:', text.count('f"'))
