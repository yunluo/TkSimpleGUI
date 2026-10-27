#!/usr/bin/env python3
"""Actions: one command wired to buttons, menus, shortcuts (TActionList analog).

An :class:`Action` names a command once; the window turns its ``text`` into
its ``key`` wherever that text is posted (menu items, right-click menus)
and registers its ``shortcut`` as a keyboard binding. When the event fires,
``callback(window, values)`` runs automatically and ``read()`` still
returns the key::

    open_action = ts.Action("Open", key="-OPEN-", shortcut="<Control-o>",
                            callback=lambda w, v: do_open())
    window = ts.Window("App", layout, actions=[open_action])
"""



class Action:
    """A named command shared by several UI entry points."""

    __slots__ = ("text", "key", "shortcut", "callback", "enabled", "metadata")

    def __init__(self, text, key=None, shortcut=None, callback=None, enabled=True, metadata=None):
        self.text = str(text)
        self.key = key if key is not None else self.text
        self.shortcut = shortcut
        self.callback = callback
        self.enabled = bool(enabled)
        self.metadata = metadata

    def to_button(self, **kwargs):
        """A :class:`~TkSimpleGUI.elements.buttons.TButton` for this action."""
        from .elements.buttons import TButton

        return TButton(self.text, key=self.key, **kwargs)

    def to_menu_entry(self):
        """The menu definition label for this action (its text)."""
        return self.text

    def trigger(self, window, values):
        """Invoke the callback if the action is enabled."""
        if self.enabled and self.callback is not None:
            self.callback(window, values)
        return self

    def __repr__(self):
        return f"<Action {self.text!r} key={self.key!r}>"


class ActionList:
    """An ordered collection of :class:`Action` objects."""

    __slots__ = ("_actions",)

    def __init__(self, actions=()):
        self._actions = list(actions)

    def add(self, action):
        self._actions.append(action)
        return self

    def __iter__(self):
        return iter(self._actions)

    def __len__(self):
        return len(self._actions)

    def keys(self):
        """All action keys in order."""
        return [action.key for action in self._actions]

    def by_key(self, key):
        """The action with this key, or None."""
        for action in self._actions:
            if action.key == key:
                return action
        return None

    def by_text(self, text):
        """The action with this (menu) text, or None."""
        for action in self._actions:
            if action.text == text:
                return action
        return None

    def menu_definition(self, title):
        """A single-cascade menu definition built from these actions."""
        return [[str(title)] + [action.to_menu_entry() for action in self._actions]]
