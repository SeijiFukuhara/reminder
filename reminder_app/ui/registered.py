"""登録済みのタスクとメモを一覧表示する画面。"""

from __future__ import annotations

from datetime import date
from tkinter import ttk
from typing import TYPE_CHECKING

from ..models import END_DATE, END_DUE, Task, format_date_jp, format_date_short
from .widgets import ConfirmBar

if TYPE_CHECKING:
    from .app import App


def _period_text(task: Task) -> str:
    start = format_date_short(task.start_date)
    if task.end_mode == END_DUE:
        return f"{start} 〜 期日まで"
    if task.end_mode == END_DATE and task.display_until:
        return f"{start} 〜 {format_date_short(task.display_until)}"
    return f"{start} 〜 " + ("ずっと" if task.keep_after_done else "完了まで")


def _status_text(task: Task, today: date) -> str:
    last = task.last_visible_date()
    if task.keep_after_done:
        if last is not None and today > last:
            return "表示終了"
        return "今日完了" if task.is_done_on(today) else "表示中"
    done = task.completed_on()
    if done is not None:
        return f"完了（{format_date_short(done)}）"
    if last is not None and today > last:
        return "表示終了（未完了）"
    if task.is_overdue_on(today):
        return "期限切れ"
    if today < task.start_date:
        return "表示前"
    return "未完了"


class RegisteredTab(ttk.Frame):
    def __init__(self, master, app: App):
        super().__init__(master, padding=10)
        self.app = app
        inner = ttk.Notebook(self)
        inner.pack(fill="both", expand=True)
        inner.add(self._build_task_page(inner), text="タスク")
        inner.add(self._build_memo_page(inner), text="今日のメモ")

    # ---- タスク ----

    def _build_task_page(self, master) -> ttk.Frame:
        page = ttk.Frame(master, padding=8)
        bar = ttk.Frame(page)
        bar.pack(fill="x")
        ttk.Button(bar, text="＋ 新規登録", style="Accent.TButton", command=lambda: self.app.open_new_task()).pack(
            side="left"
        )
        ttk.Button(bar, text="編集", command=self._edit_selected).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="削除", command=self._delete_selected_task).pack(side="left", padx=(8, 0))

        self.task_confirm = ConfirmBar(page)
        self.task_confirm.place_with(fill="x", pady=(8, 0), after=bar)

        columns = ("title", "kind", "due", "period", "status", "links")
        self.task_tree = ttk.Treeview(page, columns=columns, show="headings", selectmode="browse")
        for col, text, width, stretch in [
            ("title", "タイトル", 260, True),
            ("kind", "種類", 80, False),
            ("due", "期日", 100, False),
            ("period", "表示する期間", 170, False),
            ("status", "状態", 130, False),
            ("links", "リンク", 60, False),
        ]:
            self.task_tree.heading(col, text=text)
            self.task_tree.column(col, width=width, stretch=stretch, anchor="w")
        scroll = ttk.Scrollbar(page, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scroll.set)
        self.task_tree.pack(side="left", fill="both", expand=True, pady=(8, 0))
        scroll.pack(side="right", fill="y", pady=(8, 0))
        self.task_tree.bind("<Double-1>", lambda e: self._edit_selected())
        return page

    def _selected_task(self) -> Task | None:
        selection = self.task_tree.selection()
        if not selection:
            self.app.set_status("タスクを選択してください。", error=True)
            return None
        return self.app.store.get_task(selection[0])

    def _edit_selected(self):
        task = self._selected_task()
        if task is not None:
            self.app.open_edit_task(task.id)

    def _delete_selected_task(self):
        task = self._selected_task()
        if task is None:
            return

        def delete():
            self.app.store.delete_task(task.id)
            self.app.on_task_deleted(task.id)
            self.app.set_status(f"「{task.title}」を削除しました。")
            self.refresh()

        self.task_confirm.show(f"「{task.title}」を削除しますか？（完了の記録も消えます）", delete)

    # ---- 今日のメモ ----

    def _build_memo_page(self, master) -> ttk.Frame:
        page = ttk.Frame(master, padding=8)
        bar = ttk.Frame(page)
        bar.pack(fill="x")
        ttk.Button(bar, text="この日のホームを開く", command=self._open_selected_memo).pack(side="left")
        ttk.Button(bar, text="削除", command=self._delete_selected_memo).pack(side="left", padx=(8, 0))

        self.memo_confirm = ConfirmBar(page)
        self.memo_confirm.place_with(fill="x", pady=(8, 0), after=bar)

        self.memo_tree = ttk.Treeview(page, columns=("date", "text"), show="headings", selectmode="browse")
        self.memo_tree.heading("date", text="日付")
        self.memo_tree.heading("text", text="内容")
        self.memo_tree.column("date", width=180, stretch=False)
        self.memo_tree.column("text", width=500, stretch=True)
        scroll = ttk.Scrollbar(page, orient="vertical", command=self.memo_tree.yview)
        self.memo_tree.configure(yscrollcommand=scroll.set)
        self.memo_tree.pack(side="left", fill="both", expand=True, pady=(8, 0))
        scroll.pack(side="right", fill="y", pady=(8, 0))
        self.memo_tree.bind("<Double-1>", lambda e: self._open_selected_memo())
        return page

    def _selected_memo_date(self) -> date | None:
        selection = self.memo_tree.selection()
        if not selection:
            self.app.set_status("メモを選択してください。", error=True)
            return None
        return date.fromisoformat(selection[0])

    def _open_selected_memo(self):
        d = self._selected_memo_date()
        if d is not None:
            self.app.show_home(d)

    def _delete_selected_memo(self):
        d = self._selected_memo_date()
        if d is None:
            return

        def delete():
            self.app.store.delete_memo(d)
            if self.app.home.current == d:
                self.app.home.refresh()
            self.app.set_status(f"{format_date_jp(d)} のメモを削除しました。")
            self.refresh()

        self.memo_confirm.show(f"{format_date_jp(d)} のメモを削除しますか？", delete)

    # ---- 再表示 ----

    def refresh(self):
        today = date.today()
        self.task_confirm.hide()
        self.memo_confirm.hide()

        self.task_tree.delete(*self.task_tree.get_children())
        tasks = sorted(self.app.store.tasks, key=lambda t: (t.start_date, t.created_at), reverse=True)
        for task in tasks:
            self.task_tree.insert(
                "",
                "end",
                iid=task.id,
                values=(
                    task.title,
                    "毎日表示" if task.keep_after_done else "通常",
                    format_date_short(task.due_date) if task.due_date else "なし",
                    _period_text(task),
                    _status_text(task, today),
                    f"{len(task.links)}件" if task.links else "",
                ),
            )

        self.memo_tree.delete(*self.memo_tree.get_children())
        for d in self.app.store.memo_dates():
            text = self.app.store.get_memo(d)
            first_line = text.strip().splitlines()[0] if text.strip() else ""
            preview = first_line + (" …" if len(text.strip().splitlines()) > 1 else "")
            self.memo_tree.insert("", "end", iid=d.isoformat(), values=(format_date_jp(d), preview))
