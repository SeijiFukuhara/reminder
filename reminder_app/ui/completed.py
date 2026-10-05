"""完了済みタスクを完了した日ごとに表示する画面。"""

from __future__ import annotations

from datetime import datetime
from tkinter import ttk
from typing import TYPE_CHECKING

from ..models import format_date_jp
from .widgets import SUB_COLOR, ScrollableFrame

if TYPE_CHECKING:
    from .app import App


class CompletedTab(ttk.Frame):
    def __init__(self, master, app: App):
        super().__init__(master, padding=10)
        self.app = app
        ttk.Label(self, text="完了済みタスク（完了した日ごと）", style="Heading.TLabel").pack(anchor="w")
        self.list = ScrollableFrame(self)
        self.list.pack(fill="both", expand=True, pady=(10, 0))

    def refresh(self):
        self.list.clear()
        groups = self.app.store.completed_by_date()
        if not groups:
            ttk.Label(self.list.inner, text="完了したタスクはまだありません。", foreground=SUB_COLOR).pack(anchor="w")
            return
        for day, items in groups:
            header = ttk.Frame(self.list.inner)
            header.pack(fill="x", pady=(12, 4))
            ttk.Label(header, text=f"{format_date_jp(day)}　{len(items)}件", style="SubHeading.TLabel").pack(
                side="left"
            )
            ttk.Button(header, text="この日のホームを開く", command=lambda d=day: self.app.show_home(d)).pack(
                side="right"
            )
            ttk.Separator(self.list.inner).pack(fill="x")

            for task, done_at in items:
                row = ttk.Frame(self.list.inner, padding=(16, 3))
                row.pack(fill="x")
                ttk.Label(row, text="✓ " + task.title).pack(side="left")
                ttk.Label(row, text=f"{_time_of(done_at)} 完了", foreground=SUB_COLOR).pack(side="left", padx=(10, 0))
                if task.keep_after_done:
                    ttk.Label(row, text="毎日表示", style="Badge.TLabel").pack(side="left", padx=(10, 0))
                ttk.Button(
                    row, text="未完了に戻す", command=lambda t=task, d=day: self._undo(t.id, d)
                ).pack(side="right")

    def _undo(self, task_id, day):
        self.app.store.set_task_done(task_id, day, False)
        self.refresh()


def _time_of(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%H:%M")
    except ValueError:
        return ""
