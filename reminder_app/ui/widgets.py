"""複数の画面で使う共通の部品。"""

from __future__ import annotations

import tkinter as tk
import webbrowser
from datetime import date
from tkinter import ttk

from ..models import Link, parse_date

LINK_COLOR = "#1a62c7"
WARN_COLOR = "#c62828"
SUB_COLOR = "#666666"


class ScrollableFrame(ttk.Frame):
    """縦スクロールできるフレーム。中身は self.inner に配置する。"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width))
        self.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def clear(self):
        for child in self.inner.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0)


class DateField(ttk.Frame):
    """日付入力欄（YYYY-MM-DD）と「今日」ボタン。"""

    def __init__(self, master, width=12, **kwargs):
        super().__init__(master, **kwargs)
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side="left")
        self.today_button = ttk.Button(self, text="今日", width=5, command=lambda: self.set(date.today()))
        self.today_button.pack(side="left", padx=(4, 0))

    def set(self, d: date | None):
        self.var.set(d.isoformat() if d else "")

    def get(self) -> date | None:
        """空欄なら None。形式が正しくなければ ValueError。"""
        text = self.var.get().strip()
        return parse_date(text) if text else None

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.entry.configure(state=state)
        self.today_button.configure(state=state)


def make_link_label(master, link: Link) -> tk.Label:
    """クリックすると既定のブラウザで開くリンク表示。"""
    label = tk.Label(master, text="🔗 " + link.label, fg=LINK_COLOR, cursor="hand2", anchor="w")
    label.configure(font=("Yu Gothic UI", 9, "underline"))
    label.bind("<Button-1>", lambda e: webbrowser.open(link.url))
    return label


class ConfirmBar(ttk.Frame):
    """別ウインドウを開かずに確認を取るための帯。show() で表示する。"""

    def __init__(self, master, **kwargs):
        super().__init__(master, padding=(8, 6), style="Confirm.TFrame", **kwargs)
        self.message = ttk.Label(self, style="Confirm.TLabel")
        self.message.pack(side="left")
        ttk.Button(self, text="キャンセル", command=self.hide).pack(side="right")
        self.yes_button = ttk.Button(self, text="削除する")
        self.yes_button.pack(side="right", padx=(0, 6))
        self._pack_options: dict = {}

    def place_with(self, **pack_options):
        """show() で表示するときの pack オプションを決める。"""
        self._pack_options = pack_options

    def show(self, message: str, on_yes, yes_text="削除する"):
        self.message.configure(text=message)

        def run():
            self.hide()
            on_yes()

        self.yes_button.configure(text=yes_text, command=run)
        self.pack(**self._pack_options)

    def hide(self):
        self.pack_forget()
