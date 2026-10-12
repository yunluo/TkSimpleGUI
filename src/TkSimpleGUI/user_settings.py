#!/usr/bin/env python3
"""Persistent user settings (QSettings / TIniFile analog).

Settings live in a JSON file (default ``~/.tksimplegui4/settings.json``)
and every :meth:`~UserSettings.set` writes through to disk immediately::

    prefs = sg.UserSettings("myapp.json")
    prefs.set("window/size", "800x600")
    prefs["theme"] = "Slate"
    print(prefs.get("theme"))

Keys may contain ``/`` to address nested sections ("window/size").
"""

import json
import os


_DEFAULT_DIR_NAME = ".tksimplegui"


def _default_directory():
    override = os.environ.get("TKSIMPLEGUI_HOME")
    if override:
        return override
    return os.path.join(os.path.expanduser("~"), _DEFAULT_DIR_NAME)


class UserSettings(object):
    """A JSON backed key/value store with immediate persistence."""

    __slots__ = ("_path", "_root", "_data")

    def __init__(self, filename="settings.json", path=None, root=None):
        """``path`` overrides the storage directory; ``root`` namespaces
        this instance inside a shared file."""
        directory = path if path is not None else _default_directory()
        self._path = os.path.join(directory, filename)
        self._root = root
        self._data = self._load()

    # --- persistence --------------------------------------------------------
    def _load(self):
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, "r") as handle:
                data = json.load(handle)
        except (IOError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def save(self):
        """Write the settings to disk (also done automatically on set)."""
        directory = os.path.dirname(self._path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(self._path, "w") as handle:
            json.dump(self._data, handle, indent=2, sort_keys=True)
        return self

    def reload(self):
        """Discard in-memory changes and re-read the file."""
        self._data = self._load()
        return self

    def delete_file(self):
        """Remove the backing file and clear every value."""
        self._data = {}
        if os.path.exists(self._path):
            os.remove(self._path)
        return self

    # --- section access -------------------------------------------------------
    def _section(self):
        if self._root is None:
            return self._data
        return self._data.setdefault(self._root, {})

    # --- key API -----------------------------------------------------------------
    def get(self, key, default=None):
        """The stored value for ``key`` (``/``-separated paths allowed)."""
        node = self._section()
        for part in str(key).split("/"):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key, value):
        """Store ``value`` and persist to disk."""
        node = self._section()
        parts = str(key).split("/")
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child
        node[parts[-1]] = value
        self.save()
        return self

    def delete(self, key):
        """Remove ``key`` (and empty parent sections) and persist."""
        node = self._section()
        parts = str(key).split("/")
        trail = []
        for part in parts[:-1]:
            if not isinstance(node, dict) or part not in node:
                return self
            trail.append(node)
            node = node[part]
        if isinstance(node, dict) and parts[-1] in node:
            del node[parts[-1]]
            for parent in reversed(trail):
                for child_key, child in list(parent.items()):
                    if child == {}:
                        del parent[child_key]
        self.save()
        return self

    def keys(self):
        """Top level keys of this instance's section."""
        section = self._section()
        return list(section.keys()) if isinstance(section, dict) else []

    def as_dict(self):
        """A snapshot of this instance's section."""
        section = self._section()
        return json.loads(json.dumps(section)) if isinstance(section, dict) else {}

    # --- mapping sugar -------------------------------------------------------------
    def __getitem__(self, key):
        value = self.get(key)
        if value is None and key not in self:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def __contains__(self, key):
        node = self._section()
        for part in str(key).split("/"):
            if not isinstance(node, dict) or part not in node:
                return False
            node = node[part]
        return True

    def __repr__(self):
        return f"<UserSettings {self._path!r} root={self._root!r}>"
