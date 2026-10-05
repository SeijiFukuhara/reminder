"""ホーム画面: 上1/3に今日のメモ、下2/3にその日のタスク。"""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from typing import TYPE_CHECKING

import customtkinter as ctk

from ..models import END_DATE, Task, format_date_jp, format_date_short
from . import theme
from .widgets import (
    CalendarPopup,
    badge,
    bind_wraplength,
    card,
    ghost_button,
    link_label,
    primary_button,
    scroll_frame,
)

if TYPE_CHECKING:
    from .app import App

MEMO_SAVE_DELAY_MS = 800


class HomePage(ctk.CTkFrame):
    def __init__(self, master, app: App):
        super().__init__(master, fg_color=theme.BG)
        self.app = app
        self.fonts = app.fonts
        self.current = date.today()
        self._memo_date = self.current  # メモ欄に表示中のテキストがどの日のものか
        self._memo_job = None
        self._memo_dirty = False  # メモ欄に未保存の入力があるか
        self._memo_loading = False

        self.grid_columnconfigure(0, weight=1)
        # メモ : タスク = 1 : 2
        self.grid_rowconfigure(1, weight=1, uniform="home")
        self.grid_rowconfigure(2, weight=2, uniform="home")

        self._build_date_bar().grid(row=0, column=0, sticky="ew", pady=(4, 10))
        self._build_memo_card().grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self._build_task_card().grid(row=2, column=0, sticky="nsew", pady=(0, 4))

    # ---- 日付の切り替え ----

    def _build_date_bar(self) -> ctk.CTkFrame:
        bar = card(self)
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)
        f = self.fonts

        ghost_button(inner, "◀", lambda: self.set_date(self.current - timedelta(days=1)), f, width=40, height=36).pack(side="left")
        self.date_label = ctk.CTkLabel(inner, font=f.date, text_color=theme.TEXT, width=260)
        self.date_label.pack(side="left", padx=6)
        ghost_button(inner, "▶", lambda: self.set_date(self.current + timedelta(days=1)), f, width=40, height=36).pack(side="left")
        self.today_badge = badge(inner, "今日", theme.BADGE_TODAY, f)
        self.today_button = ghost_button(inner, "今日に戻る", lambda: self.set_date(date.today()), f, width=96, height=36)
        self.calendar_button = ghost_button(inner, "📅 日付を選ぶ", self._open_calendar, f, width=120, height=36)
        self.calendar_button.pack(side="left", padx=(12, 0))

        primary_button(inner, "＋ タスクを登録", lambda: self.app.open_new_task(start_date=self.current), f, width=150).pack(
            side="right"
        )
        return bar

    def _open_calendar(self):
        CalendarPopup(self.calendar_button, self.fonts, self.current, self.set_date)

    def set_date(self, d: date):
        self.flush_memo()
        self.current = d
        self.refresh()

    def refresh(self):
        today = date.today()
        self.date_label.configure(text=format_date_jp(self.current))
        self.today_badge.pack_forget()
        self.today_button.pack_forget()
        if self.current == today:
            self.today_badge.pack(side="left", padx=(4, 0), before=self.calendar_button)
        else:
            self.today_button.pack(side="left", padx=(8, 0), before=self.calendar_button)
        self.memo_title.configure(
            text="📝 今日のメモ" if self.current == today else f"📝 {format_date_short(self.current)} のメモ"
        )
        self._render_tasks()
        self._load_memo()

    # ---- 今日のメモ ----

    def _build_memo_card(self) -> ctk.CTkFrame:
        box = card(self, fg_color=theme.MEMO_BG, border_color=theme.MEMO_BORDER)
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(box, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))
        self.memo_title = ctk.CTkLabel(head, font=self.fonts.heading, text_color=theme.MEMO_ACCENT)
        self.memo_title.pack(side="left")
        ctk.CTkLabel(
            head, text="日付を切り替えると、別の日のメモも書けます（自動で保存）", font=self.fonts.small, text_color=theme.SUB
        ).pack(side="left", padx=(12, 0))
        self.memo_status = ctk.CTkLabel(head, text="", font=self.fonts.small, text_color=theme.SUB)
        self.memo_status.pack(side="right")

        self.memo_text = ctk.CTkTextbox(
            box, font=self.fonts.memo, wrap="word", undo=True, corner_radius=10, border_width=1,
            fg_color=theme.MEMO_TEXT_BG, border_color=theme.MEMO_BORDER, text_color=theme.TEXT,
        )
        self.memo_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.memo_text.bind("<<Modified>>", self._on_memo_modified)
        return box

    def focus_memo(self):
        self.memo_text.focus_set()

    def _load_memo(self):
        self._cancel_memo_job()
        self._memo_date = self.current
        self._memo_loading = True
        self.memo_text.delete("1.0", "end")
        self.memo_text.insert("1.0", self.app.store.get_memo(self.current))
        self.memo_text.edit_reset()
        self.memo_text.edit_modified(False)
        self._memo_loading = False
        self._memo_dirty = False
        self.memo_status.configure(text="")

    def _on_memo_modified(self, _event=None):
        if self._memo_loading or not self.memo_text.edit_modified():
            return
        self.memo_text.edit_modified(False)
        self._memo_dirty = True
        self._cancel_memo_job()
        self.memo_status.configure(text="編集中…")
        self._memo_job = self.after(MEMO_SAVE_DELAY_MS, self.flush_memo)

    def _cancel_memo_job(self):
        if self._memo_job is not None:
            self.after_cancel(self._memo_job)
            self._memo_job = None

    def flush_memo(self):
        """メモ欄に入力があれば保存する。"""
        self._cancel_memo_job()
        if not (self._memo_dirty or self.memo_text.edit_modified()):
            return
        self.memo_text.edit_modified(False)
        self._memo_dirty = False
        text = self.memo_text.get("1.0", "end-1c")
        if text != self.app.store.get_memo(self._memo_date):
            self.app.store.set_memo(self._memo_date, text)
        self.memo_status.configure(text="✓ 保存しました")

    # ---- タスク ----

    def _build_task_card(self) -> ctk.CTkFrame:
        box = card(self)
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(box, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))
        ctk.CTkLabel(head, text="✅ タスク", font=self.fonts.heading, text_color=theme.TEXT).pack(side="left")
        self.task_count = ctk.CTkLabel(head, text="", font=self.fonts.small, text_color=theme.SUB)
        self.task_count.pack(side="left", padx=(12, 0))

        self.task_list = scroll_frame(box)
        self.task_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))
        self.task_list.grid_columnconfigure(0, weight=1)
        return box

    def _render_tasks(self):
        for child in self.task_list.winfo_children():
            child.destroy()
        tasks = self.app.store.tasks_on(self.current)
        open_count = sum(not t.is_done_on(self.current) for t in tasks)
        self.task_count.configure(text=f"未完了 {open_count}件 ／ 全 {len(tasks)}件" if tasks else "")
        if not tasks:
            ctk.CTkLabel(
                self.task_list, text="この日のタスクはありません 🎉\n「＋ タスクを登録」から追加できます。",
                font=self.fonts.body, text_color=theme.SUB, justify="center",
            ).grid(row=0, column=0, pady=30)
            return
        for i, task in enumerate(tasks):
            self._build_task_row(task).grid(row=i, column=0, sticky="ew", padx=6, pady=4)

    def _build_task_row(self, task: Task) -> ctk.CTkFrame:
        d = self.current
        f = self.fonts
        done = task.is_done_on(d)
        row = card(self.task_list, fg_color=theme.CARD_DONE if done else theme.CARD)
        row.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
        var = tk.IntVar(value=1 if done else 0)
        ctk.CTkCheckBox(
            top, text=task.title, variable=var, font=f.task_done if done else f.task,
            text_color=theme.SUB if done else theme.TEXT, corner_radius=8, border_width=2,
            fg_color=theme.SUCCESS, hover_color="#2f8f5b", checkbox_width=24, checkbox_height=24,
            command=lambda: self._on_check(task, bool(var.get())),
        ).pack(side="left")
        # 誤操作を防ぐため、削除は編集画面からのみ行う
        ghost_button(top, "編集", lambda: self.app.open_edit_task(task.id), f).pack(side="right")

        # バッジ（継続タスク・期日・表示終了日）
        badges = ctk.CTkFrame(row, fg_color="transparent")
        if task.keep_after_done:
            badge(badges, "🔁 毎日表示", theme.BADGE_DAILY, f).pack(side="left", padx=(0, 6))
        if task.due_date:
            if task.is_overdue_on(d):
                badge(badges, f"⚠ 期限切れ（{format_date_short(task.due_date)}）", theme.BADGE_OVERDUE, f).pack(side="left", padx=(0, 6))
            else:
                badge(badges, f"⏰ 期日 {format_date_short(task.due_date)}", theme.BADGE_INFO, f).pack(side="left", padx=(0, 6))
        if task.end_mode == END_DATE and task.display_until:
            badge(badges, f"〜{format_date_short(task.display_until)} まで表示", theme.BADGE_INFO, f).pack(side="left", padx=(0, 6))
        if badges.winfo_children():
            badges.grid(row=1, column=0, sticky="w", padx=(44, 12), pady=(2, 2))

        if task.memo.strip():
            memo = ctk.CTkLabel(row, text=task.memo.strip(), font=f.body, text_color="#5d6778", justify="left", anchor="w")
            memo.grid(row=2, column=0, sticky="ew", padx=(44, 12), pady=(2, 0))
            bind_wraplength(memo)
        if task.links:
            links = ctk.CTkFrame(row, fg_color="transparent")
            links.grid(row=3, column=0, sticky="w", padx=(44, 12))
            for link in task.links:
                link_label(links, link, f).pack(side="left", padx=(0, 12))

        row.grid_rowconfigure(4, minsize=10)  # 下の余白
        return row

    def _on_check(self, task: Task, done: bool):
        self.app.store.set_task_done(task.id, self.current, done)
        if done:
            self.app.set_status(f"「{task.title}」を完了にしました。おつかれさまです！")
        self._render_tasks()
