"""ホーム画面: 指定した日のタスク一覧と今日のメモ。"""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk
from typing import TYPE_CHECKING

from ..models import Task, format_date_jp, format_date_short, parse_date
from .widgets import SUB_COLOR, WARN_COLOR, ScrollableFrame, make_link_label

if TYPE_CHECKING:
    from .app import App

MEMO_SAVE_DELAY_MS = 800


class HomeTab(ttk.Frame):
    def __init__(self, master, app: App):
        super().__init__(master, padding=10)
        self.app = app
        self.current = date.today()
        self._memo_date = self.current  # メモ欄に表示中のテキストがどの日のものか
        self._memo_job = None

        self._build_date_bar()

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, pady=(10, 0))

        # 左: タスク一覧
        task_box = ttk.LabelFrame(paned, text="タスク", padding=6)
        self.task_list = ScrollableFrame(task_box)
        self.task_list.pack(fill="both", expand=True)
        paned.add(task_box, weight=3)

        # 右: 今日のメモ
        self.memo_box = ttk.LabelFrame(paned, text="今日のメモ", padding=6)
        ttk.Label(
            self.memo_box, text="例）9:00- 会議　13:00- 資料作成（自動で保存されます）", foreground=SUB_COLOR
        ).pack(anchor="w")
        memo_frame = ttk.Frame(self.memo_box)
        memo_frame.pack(fill="both", expand=True, pady=(4, 0))
        self.memo_text = tk.Text(memo_frame, wrap="word", undo=True, font=("Yu Gothic UI", 11), padx=6, pady=6)
        memo_scroll = ttk.Scrollbar(memo_frame, orient="vertical", command=self.memo_text.yview)
        self.memo_text.configure(yscrollcommand=memo_scroll.set)
        self.memo_text.pack(side="left", fill="both", expand=True)
        memo_scroll.pack(side="right", fill="y")
        self.memo_text.bind("<<Modified>>", self._on_memo_modified)
        self.memo_status = ttk.Label(self.memo_box, foreground=SUB_COLOR)
        self.memo_status.pack(anchor="e")
        paned.add(self.memo_box, weight=2)

    def _build_date_bar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x")

        ttk.Button(bar, text="◀ 前日", command=lambda: self.set_date(self.current - timedelta(days=1))).pack(
            side="left"
        )
        self.date_label = ttk.Label(bar, style="Heading.TLabel", width=26, anchor="center")
        self.date_label.pack(side="left", padx=8)
        ttk.Button(bar, text="翌日 ▶", command=lambda: self.set_date(self.current + timedelta(days=1))).pack(
            side="left"
        )
        ttk.Button(bar, text="今日", command=lambda: self.set_date(date.today())).pack(side="left", padx=(8, 0))

        ttk.Label(bar, text="日付へ移動:").pack(side="left", padx=(20, 4))
        self.jump_var = tk.StringVar()
        jump_entry = ttk.Entry(bar, textvariable=self.jump_var, width=12)
        jump_entry.pack(side="left")
        jump_entry.bind("<Return>", lambda e: self._jump())
        ttk.Button(bar, text="移動", command=self._jump).pack(side="left", padx=(4, 0))

        ttk.Button(bar, text="＋ タスクを登録", style="Accent.TButton", command=self._new_task).pack(side="right")

    # ---- 日付の切り替え ----

    def set_date(self, d: date):
        self.flush_memo()
        self.current = d
        self.refresh()

    def _jump(self):
        try:
            d = parse_date(self.jump_var.get())
        except ValueError:
            self.app.set_status("日付は 2026-10-05 のような形式で入力してください。", error=True)
            return
        self.jump_var.set("")
        self.set_date(d)

    def refresh(self):
        today = date.today()
        suffix = "（今日）" if self.current == today else ""
        self.date_label.configure(text=format_date_jp(self.current) + suffix)
        self.memo_box.configure(
            text="今日のメモ" if self.current == today else f"{format_date_short(self.current)} のメモ"
        )
        self._render_tasks()
        self._load_memo()

    # ---- タスク一覧 ----

    def _render_tasks(self):
        self.task_list.clear()
        tasks = self.app.store.tasks_on(self.current)
        if not tasks:
            ttk.Label(self.task_list.inner, text="この日のタスクはありません。", foreground=SUB_COLOR).pack(
                anchor="w", pady=8
            )
            return
        for i, task in enumerate(tasks):
            if i > 0:
                ttk.Separator(self.task_list.inner).pack(fill="x", pady=4)
            self._build_task_row(task)

    def _build_task_row(self, task: Task):
        d = self.current
        done = task.is_done_on(d)
        row = ttk.Frame(self.task_list.inner, padding=(2, 2))
        row.pack(fill="x")

        head = ttk.Frame(row)
        head.pack(fill="x")
        var = tk.BooleanVar(value=done)
        ttk.Checkbutton(
            head,
            text=task.title,
            variable=var,
            style="Done.TCheckbutton" if done else "Task.TCheckbutton",
            command=lambda: self._on_check(task, var.get()),
        ).pack(side="left")
        ttk.Button(head, text="編集", width=5, command=lambda: self.app.open_edit_task(task.id)).pack(side="right")

        # 補足情報（継続タスク・期日）
        details = ttk.Frame(row)
        details.pack(fill="x", padx=(24, 0))
        if task.keep_after_done:
            ttk.Label(details, text="毎日表示", style="Badge.TLabel").pack(side="left", padx=(0, 6))
        if task.due_date:
            overdue = task.is_overdue_on(d)
            text = f"期日 {format_date_short(task.due_date)}" + ("　期限切れ" if overdue else "")
            ttk.Label(details, text=text, foreground=WARN_COLOR if overdue else SUB_COLOR).pack(side="left")

        if task.memo.strip():
            memo = ttk.Label(row, text=task.memo.strip(), foreground=SUB_COLOR, justify="left")
            memo.pack(fill="x", padx=(24, 0), pady=(2, 0))
            memo.bind("<Configure>", lambda e: memo.configure(wraplength=max(e.width - 4, 100)))
        for link in task.links:
            make_link_label(row, link).pack(anchor="w", padx=(24, 0))

    def _on_check(self, task: Task, done: bool):
        self.app.store.set_task_done(task.id, self.current, done)
        self._render_tasks()

    def _new_task(self):
        self.app.open_new_task(start_date=self.current)

    # ---- 今日のメモ ----

    def _load_memo(self):
        self._cancel_memo_job()
        self._memo_date = self.current
        self.memo_text.delete("1.0", "end")
        self.memo_text.insert("1.0", self.app.store.get_memo(self.current))
        self.memo_text.edit_reset()
        self.memo_text.edit_modified(False)
        self.memo_status.configure(text="")

    def _on_memo_modified(self, _event=None):
        if not self.memo_text.edit_modified():
            return
        self.memo_text.edit_modified(False)
        self._cancel_memo_job()
        self.memo_status.configure(text="編集中…")
        self._memo_job = self.after(MEMO_SAVE_DELAY_MS, self.flush_memo)

    def _cancel_memo_job(self):
        if self._memo_job is not None:
            self.after_cancel(self._memo_job)
            self._memo_job = None

    def flush_memo(self):
        """メモ欄の内容が変わっていれば保存する。"""
        self._cancel_memo_job()
        text = self.memo_text.get("1.0", "end-1c")
        if text != self.app.store.get_memo(self._memo_date):
            self.app.store.set_memo(self._memo_date, text)
            self.memo_status.configure(text="保存しました")
        elif self.memo_status.cget("text") == "編集中…":
            self.memo_status.configure(text="保存しました")
