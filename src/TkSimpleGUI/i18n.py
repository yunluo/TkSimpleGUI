# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Dictionary based internationalization (Qt ``tr()`` analog).

Load a catalog (a flat ``{source: translated}`` dict or JSON file), then
wrap every UI string with :func:`_`::

    sg.set_translations({"Open": "Ouvert", "Save": "Sauve"})
    sg.Text(_("Open"))
"""

import json



class Translator(object):
    """A replaceable string catalog; unknown strings pass through."""

    __slots__ = ("_catalog",)

    def __init__(self, catalog=None):
        self._catalog = dict(catalog) if catalog else {}

    def set_catalog(self, catalog):
        """Replace the whole catalog (dict or JSON filename)."""
        self._catalog = self._load_catalog(catalog)
        return self

    def add(self, source, translated):
        """Add or override one translation."""
        self._catalog[str(source)] = str(translated)
        return self

    def _load_catalog(self, catalog):
        if isinstance(catalog, str):
            with open(catalog, "r") as handle:
                loaded = json.load(handle)
            return dict(loaded)
        return dict(catalog)

    def __call__(self, text):
        return self._catalog.get(text, text)

    def __repr__(self):
        return f"<Translator {len(self._catalog)} entries>"


_translator = Translator()


def _(text):
    """Translate ``text`` through the global catalog (identity when absent)."""
    return _translator(text)


def translate(text):
    """Alias of :func:`_` (for code that shadows ``_``)."""
    return _translator(text)


def set_translations(catalog):
    """Install a new global catalog (dict or JSON filename). Returns self."""
    _translator.set_catalog(catalog)


def add_translation(source, translated):
    """Add one entry to the global catalog."""
    _translator.add(source, translated)


def clear_translations():
    """Remove every global translation (identity mapping again)."""
    _translator.set_catalog({})
