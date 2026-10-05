"""完了済みタスクを完了した日ごとに表示する画面。"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

import customtkinter as ctk

from ..models import format_date_jp
from . import theme
from .widgets import badge, card, ghost_button, scroll_frame

if TYPE_CHECKING:
    from .app import App


class CompletedPage(ctk.CTkFrame):
    def __init__(self, master, app: App):
        super().__init__(master, fg_color=theme.BG)
        self.app = app
        self.fonts = app.fonts

        box = card(self)
        box.pack(fill="both", expand=True, pady=(4, 4))
        ctk.CTkLabel(box, text="✅ 完了済みタスク（完了した日ごと）", font=self.fonts.heading, text_color=theme.TEXT).pack(
            anchor="w", padx=20, pady=(14, 4)
        )
        self.list = scroll_frame(box)
        self.list.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        self.list.grid_columnconfigure(0, weight=1)

    def refresh(self):
        f = self.fonts
        for child in self.list.winfo_children():
            child.destroy()
        groups = self.app.store.completed_by_date()
        if not groups:
            ctk.CTkLabel(self.list, text="完了したタスクはまだありません。", font=f.body, text_color=theme.SUB).grid(
                row=0, column=0, pady=30
            )
            return
        row = 0
        for day, items in groups:
            header = ctk.CTkFrame(self.list, fg_color="transparent")
            header.grid(row=row, column=0, sticky="ew", padx=8, pady=(14, 4))
            ctk.CTkLabel(header, text=format_date_jp(day), font=f.subheading, text_color=theme.TEXT).pack(side="left")
            badge(header, f"{len(items)}件", theme.BADGE_DONE, f).pack(side="left", padx=(8, 0))
            ghost_button(header, "この日のホームを開く", lambda d=day: self.app.show_home(d), f, width=160).pack(side="right")
            row += 1

            for task, done_at in items:
                item = card(self.list)
                item.grid(row=row, column=0, sticky="ew", padx=8, pady=3)
                ctk.CTkLabel(item, text="✔", font=f.subheading, text_color=theme.SUCCESS).pack(side="left", padx=(14, 6), pady=8)
                ctk.CTkLabel(item, text=task.title, font=f.body, text_color=theme.TEXT).pack(side="left")
                ctk.CTkLabel(item, text=f"{_time_of(done_at)} 完了", font=f.small, text_color=theme.SUB).pack(
                    side="left", padx=(12, 0)
                )
                if task.keep_after_done:
                    badge(item, "🔁 毎日表示", theme.BADGE_DAILY, f).pack(side="left", padx=(10, 0))
                ghost_button(item, "未完了に戻す", lambda t=task, d=day: self._undo(t.id, d), f, width=110).pack(
                    side="right", padx=10
                )
                row += 1

    def _undo(self, task_id: str, day: date):
        self.app.store.set_task_done(task_id, day, False)
        self.refresh()


def _time_of(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%H:%M")
    except ValueError:
        return ""
