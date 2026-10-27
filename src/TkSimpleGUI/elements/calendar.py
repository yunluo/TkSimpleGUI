#!/usr/bin/env python3
"""Embedded calendar element (Delphi TMonthCalendar equivalent)."""

import calendar as _calendar
import datetime as _datetime

import tkinter as tk
from tkinter import ttk

from .base import Element
from .. import _theming as theme_mod


_WEEKDAY_HEADERS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


class TCalendar(Element):
    """A month view with clickable days.

    Clicking a day selects it and posts the element's key. Navigate months
    with the built-in ``<``/``>`` buttons. ``get()`` returns the selected
    date formatted with ``dateformat`` (default ``"%Y-%m-%d"``)::

        cal = ts.TCalendar(key="-CAL-", default_date=datetime.date.today())
        event, values = window.read()
        print(values["-CAL-"])  # "2026-10-11"
    """

    __slots__ = (
        "_date",
        "_dateformat",
        "_enable_events",
        "_viewed",
        "_header",
        "_day_area",
    )

    # created together in _create_widget
    _header: ttk.Label
    _day_area: tk.Frame

    def __init__(
        self,
        default_date=None,
        dateformat="%Y-%m-%d",
        key=None,
        enable_events=True,
        tooltip=None,
        visible=True,
        pad=None,
        expand_x=False,
        expand_y=False,
        right_click_menu=None,
        metadata=None,
    ):
        super().__init__(
            key=key,
            tooltip=tooltip,
            visible=visible,
            pad=pad,
            expand_x=expand_x,
            expand_y=expand_y,
            right_click_menu=right_click_menu,
            metadata=metadata,
        )
        if default_date is None:
            default_date = _datetime.date.today()
        elif isinstance(default_date, tuple) and len(default_date) == 3:
            default_date = _datetime.date(*default_date)
        elif not isinstance(default_date, _datetime.date):
            raise TypeError(
                "default_date must be a datetime.date or (year, month, day) tuple"
            )
        self._date = default_date
        self._dateformat = dateformat or "%Y-%m-%d"
        self._enable_events = enable_events
        self._viewed = default_date.replace(day=1)
        self._header = None  # ty: ignore[invalid-assignment]
        self._day_area = None  # ty: ignore[invalid-assignment]

    # --- date state -------------------------------------------------------------
    @property
    def date(self):
        """The selected date as a :class:`datetime.date`."""
        return self._date

    def get(self):
        """The selected date formatted with ``dateformat``."""
        return self._date.strftime(self._dateformat)

    def update(self, value=None, visible=None):
        """Set the selected date (datetime.date, (y, m, d) or formatted str)."""
        if value is not None:
            self._date = self._coerce_date(value)
            self._viewed = self._date.replace(day=1)
            if self._widget is not None:
                self._draw_month()
        if visible is not None:
            self.unhide() if visible else self.hide()
        return self

    @staticmethod
    def _coerce_date(value):
        if isinstance(value, _datetime.date):
            return value
        if isinstance(value, tuple) and len(value) == 3:
            return _datetime.date(*value)
        return _datetime.datetime.strptime(str(value), "%Y-%m-%d").date()

    # --- widget construction ------------------------------------------------------
    def _create_widget(self, master):
        bg = self._surface_color(master)
        muted = theme_mod.theme_manager.muted_color()
        fg = theme_mod.theme_manager.text_color
        if muted is None or theme_mod._is_system_default(fg):
            muted = "#808080"  # native look
        frame = tk.Frame(master, background=bg)
        header = ttk.Label(
            frame,
            anchor="center",
            font=("Helvetica", 10, "bold"),
        )
        header.grid(row=0, column=0, columnspan=7, sticky="ew", pady=(2, 4))
        prev_button = ttk.Button(
            frame, text="<", width=3, command=lambda: self._shift(-1)
        )
        prev_button.grid(row=1, column=0, columnspan=2)
        next_button = ttk.Button(
            frame, text=">", width=3, command=lambda: self._shift(1)
        )
        next_button.grid(row=1, column=5, columnspan=2)
        # weekday headers get their own row: sharing row 1 with the nav
        # buttons made the labels overlap the buttons
        for column, name in enumerate(_WEEKDAY_HEADERS):
            weekday = tk.Label(
                frame, text=name, anchor="center",
                background=bg, foreground=muted,
            )
            weekday.grid(row=2, column=column, sticky="ew", padx=1)
        day_area = tk.Frame(frame, background=bg)
        day_area.grid(row=3, column=0, columnspan=7, sticky="nsew")
        self._header = header
        self._day_area = day_area
        frame.columnconfigure(2, weight=1)
        return frame

    @staticmethod
    def _surface_color(master):
        """The surface color to paint the calendar onto (theme aware)."""
        themed = theme_mod.theme_manager.effective_background()
        if themed is not None:
            return themed
        # ttk parents do not expose -background via cget; ask the toplevel
        widget = master
        while widget is not None:
            try:
                return str(widget.cget("background"))
            except (tk.TclError, AttributeError):
                widget = widget.master if hasattr(widget, "master") else None
        return "#f0f0f0"

    def _post_create(self):
        super()._post_create()
        self._draw_month()

    # --- month rendering -------------------------------------------------------------
    def _accent(self):
        """Selection color for the chosen day (theme accent / classic blue)."""
        accent = theme_mod.theme_manager.accent_color()
        return accent if accent is not None else "#3a7bd5"

    def _draw_month(self):
        self._header.configure(
            text=f"{_calendar.month_name[self._viewed.month]} {self._viewed.year}"
        )
        for child in self._day_area.winfo_children():
            child.destroy()
        background = self._day_area.cget("background")
        fg = theme_mod.theme_manager.text_color
        native = theme_mod._is_system_default(fg)
        accent = self._accent()
        accent_fg = theme_mod.contrast_on(accent)
        weeks = _calendar.Calendar(firstweekday=0).monthdayscalendar(
            self._viewed.year, self._viewed.month
        )
        selected = self._date
        for row_index, week in enumerate(weeks):
            for column, day in enumerate(week):
                if day == 0:
                    tk.Label(self._day_area, width=3, background=background).grid(
                        row=row_index, column=column, padx=1, pady=1
                    )
                    continue
                day_date = _datetime.date(
                    self._viewed.year, self._viewed.month, day
                )
                is_selected = day_date == selected
                button = tk.Button(
                    self._day_area,
                    text=str(day),
                    width=3,
                    relief="sunken" if is_selected else "flat",
                    bd=0,
                    highlightthickness=0,
                    background=accent if is_selected else background,
                    activebackground=accent,
                    activeforeground=accent_fg,
                    command=lambda d=day_date: self._choose_day(d),
                )
                if not native:
                    # classic tk.Button rejects "" — only pass themed colors
                    button.configure(foreground=accent_fg if is_selected else fg)
                button.grid(row=row_index, column=column, padx=1, pady=1)

    def apply_theme(self):
        """Repaint the calendar surface, weekday row and days."""
        if self._widget is None or self._day_area is None:
            return self
        bg = self._surface_color(self._widget.master)
        muted = theme_mod.theme_manager.muted_color()
        fg = theme_mod.theme_manager.text_color
        if theme_mod._is_system_default(fg):
            muted = theme_mod.native_widget_colors(
                tk.Label, self._widget, ("foreground",)
            )["foreground"]
        self._widget.configure(background=bg)
        self._day_area.configure(background=bg)
        for child in self._widget.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(background=bg, foreground=muted)
        self._draw_month()
        return self

    def _choose_day(self, day_date):
        self._date = day_date
        self._draw_month()
        if self._enable_events:
            self._post_event()

    def _shift(self, delta):
        month = self._viewed.month + delta
        year = self._viewed.year
        if month > 12:
            month, year = 1, year + 1
        elif month < 1:
            month, year = 12, year - 1
        self._viewed = self._viewed.replace(year=year, month=month, day=1)
        self._draw_month()
