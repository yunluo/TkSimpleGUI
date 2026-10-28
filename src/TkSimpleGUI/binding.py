#!/usr/bin/env python3
"""Two-way data binding: a :class:`Var` value holder mirrored by elements.

Create a var, hand it to :meth:`Window.bind_var` for every element key that
should mirror it, then treat ``var.value`` as the single source of truth::

    count = ts.Var(0)
    window.bind_var("-ENTRY-", count)
    window.bind_var("-ECHO-", count)

    count.value = 1   # entry and echo both show "1"
    # ...and typing into the entry updates ``count.value`` on the next
    # event-loop tick, which also copies the text into the echo element

Writes fan out to every live binding, so one var may be bound in several
windows at once (multi-window apps share it naturally).
"""

from typing import Any, List, Optional, Tuple

from .constants import ElementKey


class Var:
    """Observable value holder bridged to element keys by ``bind_var``.

    Like a tk ``Variable``, the var's value wins at bind time: it is
    pushed into the freshly bound element. ``Var()``'s ``None`` default
    is a no-op at bind time instead — the element keeps its layout value
    and the var adopts it on the first event-loop tick. After binding,
    ``value`` may be read and written freely.
    """

    def __init__(self, value: Any = None):
        self._value = value
        # (window, key) pairs currently bound to this var
        self._bindings: List[Tuple[Any, ElementKey]] = []

    @property
    def value(self) -> Any:
        """The current value; assigning it pushes into every bound element."""
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        self._set(new_value, source=None)

    # --- internals ---------------------------------------------------------
    def _set(self, new_value: Any, source: Optional[Tuple[Any, ElementKey]]):
        """Store ``new_value`` and push it into every bound element except
        ``source`` (the binding it came from, so an editor is not rewritten
        while the user types into it)."""
        self._value = new_value
        for window, key in list(self._bindings):
            if source is not None and window is source[0] and key == source[1]:
                continue
            element = window.find_element(key)
            if element is None:
                continue
            element.update(value=new_value)

    def _attach(self, window: Any, key: ElementKey) -> None:
        self._bindings.append((window, key))

    def _detach(self, window: Any, key: ElementKey) -> None:
        self._bindings = [
            pair for pair in self._bindings
            if not (pair[0] is window and pair[1] == key)
        ]

    def _detach_window(self, window: Any) -> None:
        self._bindings = [pair for pair in self._bindings if pair[0] is not window]
