"""登録済みのタスクとメモを一覧表示する画面。"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import customtkinter as ctk

from ..models import END_DATE, END_DUE, Task, format_date_jp, format_date_short
from . import theme
from .widgets import DateField, DeleteButton, badge, bind_wraplength, card, ghost_button, primary_button, scroll_frame

if TYPE_CHECKING:
    from .app import App

VIEW_TASKS = "タスク"
VIEW_MEMOS = "今日のメモ"


def period_text(task: Task) -> str:
    start = format_date_short(task.start_date)
    if task.end_mode == END_DUE and task.due_date:
        return f"{start} 〜 {format_date_short(task.due_date)}（期日まで）"
    if task.end_mode == END_DATE and task.display_until:
        return f"{start} 〜 {format_date_short(task.display_until)}"
    return f"{start} 〜 " + ("ずっと" if task.keep_after_done else "完了まで")


def status_of(task: Task, today: date) -> tuple[str, tuple[str, str]]:
    """状態の表示名とバッジの色。"""
    last = task.last_visible_date()
    if task.keep_after_done:
        if last is not None and today > last:
            return "表示終了", theme.BADGE_INFO
        if today < task.start_date:
            return "表示前", theme.BADGE_INFO
        return ("今日は完了", theme.BADGE_DONE) if task.is_done_on(today) else ("表示中", theme.BADGE_DAILY)
    done = task.completed_on()
    if done is not None:
        return f"完了（{format_date_short(done)}）", theme.BADGE_DONE
    if last is not None and today > last:
        return "表示終了（未完了）", theme.BADGE_INFO
    if task.is_overdue_on(today):
        return "期限切れ", theme.BADGE_OVERDUE
    if today < task.start_date:
        return "表示前", theme.BADGE_INFO
    return "未完了", theme.BADGE_DAILY


class RegisteredPage(ctk.CTkFrame):
    def __init__(self, master, app: App):
        super().__init__(master, fg_color=theme.BG)
        self.app = app
        self.fonts = f = app.fonts

        box = card(self)
        box.pack(fill="both", expand=True, pady=(4, 4))
        head = ctk.CTkFrame(box, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(14, 4))
        ctk.CTkLabel(head, text="📋 登録済み一覧", font=f.heading, text_color=theme.TEXT).pack(side="left")
        self.view_button = ctk.CTkSegmentedButton(
            head, values=[VIEW_TASKS, VIEW_MEMOS], command=lambda v: self.refresh(), font=f.body_bold,
            selected_color=theme.PRIMARY, selected_hover_color=theme.PRIMARY_HOVER,
            unselected_color=theme.GHOST, unselected_hover_color=theme.GHOST_HOVER, text_color=theme.TEXT,
            fg_color=theme.GHOST, corner_radius=14, height=32,
        )
        self.view_button.set(VIEW_TASKS)
        self.view_button.pack(side="left", padx=(16, 0))

        # 操作バー（表示内容で切り替える）
        self.task_bar = ctk.CTkFrame(box, fg_color="transparent")
        primary_button(self.task_bar, "＋ 新規登録", lambda: self.app.open_new_task(), f, width=120).pack(side="left")

        self.memo_bar = ctk.CTkFrame(box, fg_color="transparent")
        ctk.CTkLabel(self.memo_bar, text="別の日のメモを書く：", font=f.body, text_color=theme.TEXT).pack(side="left")
        self.memo_date_field = DateField(self.memo_bar, f)
        self.memo_date_field.pack(side="left", padx=(4, 8))
        primary_button(self.memo_bar, "この日のメモを開く", self._open_memo_from_field, f, width=150).pack(side="left")
        self.bar_slot = ctk.CTkFrame(box, fg_color="transparent", height=0)
        self.bar_slot.pack(fill="x", padx=20)

        self.list = scroll_frame(box)
        self.list.pack(fill="both", expand=True, padx=8, pady=(6, 10))
        self.list.grid_columnconfigure(0, weight=1)

    def refresh(self):
        for child in self.list.winfo_children():
            child.destroy()
        self.task_bar.pack_forget()
        self.memo_bar.pack_forget()
        if self.view_button.get() == VIEW_TASKS:
            self.task_bar.pack(fill="x", padx=20, pady=(6, 0), before=self.bar_slot)
            self._render_tasks()
        else:
            self.memo_date_field.set(date.today())
            self.memo_bar.pack(fill="x", padx=20, pady=(6, 0), before=self.bar_slot)
            self._render_memos()

    def _empty(self, text: str):
        ctk.CTkLabel(self.list, text=text, font=self.fonts.body, text_color=theme.SUB).grid(row=0, column=0, pady=30)

    # ---- タスク ----

    def _render_tasks(self):
        f = self.fonts
        today = date.today()
        tasks = sorted(self.app.store.tasks, key=lambda t: (t.start_date, t.created_at), reverse=True)
        if not tasks:
            self._empty("登録済みのタスクはありません。")
            return
        for i, task in enumerate(tasks):
            item = card(self.list)
            item.grid(row=i, column=0, sticky="ew", padx=8, pady=4)
            item.grid_columnconfigure(0, weight=1)

            top = ctk.CTkFrame(item, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 2))
            ctk.CTkLabel(top, text=task.title, font=f.body_bold, text_color=theme.TEXT).pack(side="left")
            # 誤操作を防ぐため、削除は編集画面からのみ行う
            ghost_button(top, "編集", lambda t=task: self.app.open_edit_task(t.id), f).pack(side="right")

            info = ctk.CTkFrame(item, fg_color="transparent")
            info.grid(row=1, column=0, sticky="w", padx=14, pady=(2, 10))
            status, colors = status_of(task, today)
            badge(info, status, colors, f).pack(side="left", padx=(0, 6))
            if task.keep_after_done:
                badge(info, "🔁 毎日表示", theme.BADGE_DAILY, f).pack(side="left", padx=(0, 6))
            if task.due_date:
                badge(info, f"⏰ 期日 {format_date_short(task.due_date)}", theme.BADGE_INFO, f).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(info, text=f"表示期間：{period_text(task)}", font=f.small, text_color=theme.SUB).pack(
                side="left", padx=(4, 0)
            )
            if task.links:
                ctk.CTkLabel(info, text=f"🔗 {len(task.links)}件", font=f.small, text_color=theme.SUB).pack(
                    side="left", padx=(10, 0)
                )

    # ---- 今日のメモ ----

    def _render_memos(self):
        f = self.fonts
        dates = self.app.store.memo_dates()
        if not dates:
            self._empty("保存されたメモはありません。")
            return
        for i, d in enumerate(dates):
            item = card(self.list)
            item.grid(row=i, column=0, sticky="ew", padx=8, pady=4)
            item.grid_columnconfigure(0, weight=1)

            top = ctk.CTkFrame(item, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 2))
            ctk.CTkLabel(top, text="📝 " + format_date_jp(d), font=f.body_bold, text_color=theme.TEXT).pack(side="left")
            DeleteButton(top, f, lambda d=d: self._delete_memo(d), question="このメモを削除しますか？").pack(side="right")
            ghost_button(top, "開く", lambda d=d: self.app.show_home(d, focus_memo=True), f).pack(side="right", padx=(0, 6))

            lines = self.app.store.get_memo(d).strip().splitlines()
            preview = "\n".join(lines[:3]) + ("\n…" if len(lines) > 3 else "")
            text = ctk.CTkLabel(item, text=preview, font=f.body, text_color="#5d6778", justify="left", anchor="w")
            text.grid(row=1, column=0, sticky="ew", padx=(36, 14), pady=(0, 10))
            bind_wraplength(text)

    def _open_memo_from_field(self):
        try:
            d = self.memo_date_field.get()
        except ValueError:
            d = None
        if d is None:
            self.app.set_status("日付は 2026-10-05 のように入力するか、📅 から選んでください。", error=True)
            return
        self.app.show_home(d, focus_memo=True)

    def _delete_memo(self, d: date):
        self.app.store.delete_memo(d)
        if self.app.home.current == d:
            self.app.home.refresh()
        self.app.set_status(f"{format_date_jp(d)} のメモを削除しました。")
        self.refresh()
