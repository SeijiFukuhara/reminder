"""複数の画面で使う共通の部品。"""

from __future__ import annotations

import tkinter as tk
import webbrowser
from datetime import date, timedelta
from typing import Callable

import customtkinter as ctk

from ..models import Link, parse_date
from . import theme
from .theme import Fonts


def card(master, fg_color=theme.CARD, border_color=theme.BORDER, **kwargs) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        master, fg_color=fg_color, corner_radius=14, border_width=1, border_color=border_color, **kwargs
    )


def scroll_frame(master, **kwargs) -> ctk.CTkScrollableFrame:
    return ctk.CTkScrollableFrame(
        master, fg_color="transparent", corner_radius=0,
        scrollbar_button_color="#d3d9e6", scrollbar_button_hover_color="#b9c2d4", **kwargs,
    )


def primary_button(master, text, command, fonts: Fonts, **kwargs) -> ctk.CTkButton:
    return ctk.CTkButton(
        master, text=text, command=command, font=fonts.body_bold, corner_radius=18, height=34,
        fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER, **kwargs,
    )


def ghost_button(master, text, command, fonts: Fonts, **kwargs) -> ctk.CTkButton:
    options = dict(
        font=fonts.body, corner_radius=16, height=30, width=60,
        fg_color=theme.GHOST, hover_color=theme.GHOST_HOVER, text_color=theme.TEXT,
    )
    options.update(kwargs)
    return ctk.CTkButton(master, text=text, command=command, **options)


def danger_button(master, text, command, fonts: Fonts, **kwargs) -> ctk.CTkButton:
    options = dict(
        font=fonts.body_bold, corner_radius=16, height=30, width=70,
        fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER, text_color="#ffffff",
    )
    options.update(kwargs)
    return ctk.CTkButton(master, text=text, command=command, **options)


def badge(master, text, colors, fonts: Fonts) -> ctk.CTkLabel:
    bg, fg = colors
    return ctk.CTkLabel(
        master, text=f" {text} ", fg_color=bg, text_color=fg, font=fonts.small_bold, corner_radius=8, height=22
    )


def link_label(master, link: Link, fonts: Fonts) -> ctk.CTkLabel:
    """クリックすると既定のブラウザで開くリンク。"""
    label = ctk.CTkLabel(master, text="🔗 " + link.label, text_color=theme.PRIMARY, font=fonts.link, cursor="hand2", height=22)
    label.bind("<Button-1>", lambda e: webbrowser.open(link.url))
    return label


def bind_wraplength(label: ctk.CTkLabel, margin: int = 8):
    """ラベルの幅に合わせて文字を折り返す。"""

    def update(event):
        scale = ctk.ScalingTracker.get_widget_scaling(label)
        label.configure(wraplength=max(int((event.width - margin) / scale), 80))

    label.bind("<Configure>", update)


class DeleteButton(ctk.CTkFrame):
    """押すとその場で「削除しますか？」の確認に切り替わる削除ボタン（別ウインドウは開かない）。"""

    def __init__(self, master, fonts: Fonts, on_confirm: Callable[[], None], text="削除", question="削除しますか？", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_confirm = on_confirm
        self.button = ghost_button(
            self, text, self._ask, fonts, text_color=theme.DANGER, fg_color=theme.DANGER_LIGHT, hover_color="#f9d6d3",
        )
        self.button.pack()

        self.confirm = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(self.confirm, text=question, font=fonts.small_bold, text_color=theme.DANGER).pack(side="left", padx=(0, 6))
        danger_button(self.confirm, "削除する", self._yes, fonts).pack(side="left")
        ghost_button(self.confirm, "やめる", self.reset, fonts).pack(side="left", padx=(6, 0))

    def _ask(self):
        self.button.pack_forget()
        self.confirm.pack()

    def reset(self):
        """確認表示をやめて、元の削除ボタンに戻す。"""
        self.confirm.pack_forget()
        self.button.pack()

    def _yes(self):
        self.on_confirm()


class CalendarPopup(ctk.CTkFrame):
    """日付を選ぶカレンダー。別ウインドウではなく、メインウインドウの上に重ねて表示する。"""

    _current: CalendarPopup | None = None

    def __init__(self, anchor, fonts: Fonts, selected: date | None, on_pick: Callable[[date], None]):
        CalendarPopup.close_current()
        root = anchor.winfo_toplevel()
        super().__init__(root, fg_color=theme.CARD, corner_radius=14, border_width=2, border_color=theme.BORDER)
        CalendarPopup._current = self
        self.fonts = fonts
        self.selected = selected
        self.on_pick = on_pick
        self.month = (selected or date.today()).replace(day=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))
        ghost_button(header, "◀", self._prev_month, fonts, width=34).pack(side="left")
        self.month_label = ctk.CTkLabel(header, font=fonts.subheading, text_color=theme.TEXT)
        self.month_label.pack(side="left", expand=True)
        ghost_button(header, "▶", self._next_month, fonts, width=34).pack(side="left")
        ghost_button(header, "✕", self.close, fonts, width=34).pack(side="left", padx=(6, 0))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=10)
        for col, name in enumerate("月火水木金土日"):
            color = "#3867d6" if col == 5 else theme.DANGER if col == 6 else theme.SUB
            ctk.CTkLabel(grid, text=name, font=fonts.small_bold, text_color=color, width=36).grid(row=0, column=col)
        self.day_buttons = []
        for i in range(42):
            button = ctk.CTkButton(grid, width=36, height=30, corner_radius=15, font=fonts.body)
            button.grid(row=1 + i // 7, column=i % 7, padx=1, pady=1)
            self.day_buttons.append(button)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=(4, 10))
        ghost_button(footer, "今日", lambda: self._pick(date.today()), fonts).pack(side="right")

        self._render()
        self._place_near(anchor, root)

    def _place_near(self, anchor, root):
        root.update_idletasks()
        width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        x = anchor.winfo_rootx() - root.winfo_rootx()
        y = anchor.winfo_rooty() - root.winfo_rooty() + anchor.winfo_height() + 4
        x = max(8, min(x, root.winfo_width() - width - 8))
        if y + height > root.winfo_height() - 8:
            y = max(8, anchor.winfo_rooty() - root.winfo_rooty() - height - 4)
        # CTk の place は座標を拡大率で変換してしまうので、tkinter の place を直接使う
        tk.Place.place_configure(self, x=x, y=y)
        self.lift()

    def _render(self):
        self.month_label.configure(text=f"{self.month.year}年 {self.month.month}月")
        start = self.month - timedelta(days=self.month.weekday())
        today = date.today()
        for i, button in enumerate(self.day_buttons):
            d = start + timedelta(days=i)
            in_month = d.month == self.month.month
            if d == self.selected:
                fg, hover, text_color = theme.PRIMARY, theme.PRIMARY_HOVER, "#ffffff"
            elif d == today:
                fg, hover, text_color = theme.BADGE_TODAY[0], theme.GHOST_HOVER, theme.PRIMARY
            else:
                fg, hover = "transparent", theme.GHOST
                text_color = theme.TEXT if in_month else "#c3c9d4"
            button.configure(
                text=str(d.day), fg_color=fg, hover_color=hover, text_color=text_color,
                command=lambda d=d: self._pick(d),
            )

    def _prev_month(self):
        self.month = (self.month - timedelta(days=1)).replace(day=1)
        self._render()

    def _next_month(self):
        self.month = (self.month + timedelta(days=32)).replace(day=1)
        self._render()

    def _pick(self, d: date):
        self.close()
        self.on_pick(d)

    def close(self):
        if CalendarPopup._current is self:
            CalendarPopup._current = None
        self.destroy()

    @classmethod
    def close_current(cls):
        if cls._current is not None and cls._current.winfo_exists():
            cls._current.close()
        cls._current = None


class DateField(ctk.CTkFrame):
    """日付入力欄（YYYY-MM-DD）と、カレンダーを開くボタン。"""

    def __init__(self, master, fonts: Fonts, width=120, on_change: Callable[[date], None] | None = None):
        super().__init__(master, fg_color="transparent")
        self.fonts = fonts
        self.on_change = on_change
        self.var = tk.StringVar()
        self.entry = ctk.CTkEntry(self, textvariable=self.var, width=width, font=fonts.body, corner_radius=10)
        self.entry.pack(side="left")
        self.button = ghost_button(self, "📅", self._open_calendar, fonts, width=40)
        self.button.pack(side="left", padx=(4, 0))

    def _open_calendar(self):
        try:
            selected = self.get()
        except ValueError:
            selected = None
        CalendarPopup(self, self.fonts, selected, self._picked)

    def _picked(self, d: date):
        self.set(d)
        if self.on_change:
            self.on_change(d)

    def set(self, d: date | None):
        self.var.set(d.isoformat() if d else "")

    def get(self) -> date | None:
        """空欄なら None。形式が正しくなければ ValueError。"""
        text = self.var.get().strip()
        return parse_date(text) if text else None

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.entry.configure(state=state, text_color=theme.TEXT if enabled else "#b8bfcc")
        self.button.configure(state=state)
