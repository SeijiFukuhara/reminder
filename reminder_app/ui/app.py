"""メインウインドウ。すべての画面を1つのウインドウ内のタブで切り替える。"""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import font as tkfont
from tkinter import ttk

from ..storage import Store
from .completed import CompletedTab
from .home import HomeTab
from .registered import RegisteredTab
from .task_form import TaskFormTab
from .widgets import SUB_COLOR, WARN_COLOR

FONT_FAMILY = "Yu Gothic UI"
STATUS_CLEAR_MS = 5000


class App(tk.Tk):
    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.title("リマインダー")
        self.geometry("1100x720")
        self.minsize(820, 520)
        self._setup_styles()
        self._status_job = None
        self.form = None

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        self.home = HomeTab(self.notebook, self)
        self.form = TaskFormTab(self.notebook, self)
        self.completed = CompletedTab(self.notebook, self)
        self.registered = RegisteredTab(self.notebook, self)
        self.notebook.add(self.home, text="ホーム")
        self.notebook.add(self.form, text="タスク登録")
        self.notebook.add(self.completed, text="完了済みタスク")
        self.notebook.add(self.registered, text="登録済みタスク・メモ")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.status = ttk.Label(self, padding=(10, 4), foreground=SUB_COLOR)
        self.status.pack(fill="x")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.home.refresh()
        if store.load_warning:
            self.set_status(store.load_warning, error=True, sticky=True)

    def _setup_styles(self):
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(name).configure(family=FONT_FAMILY, size=10)
        style = ttk.Style(self)
        style.configure("Heading.TLabel", font=(FONT_FAMILY, 14, "bold"))
        style.configure("SubHeading.TLabel", font=(FONT_FAMILY, 11, "bold"))
        style.configure("Task.TCheckbutton", font=(FONT_FAMILY, 11))
        style.configure("Done.TCheckbutton", font=(FONT_FAMILY, 11, "overstrike"), foreground="#999999")
        style.configure("Badge.TLabel", font=(FONT_FAMILY, 8), foreground="#ffffff", background="#5c7cfa", padding=(5, 0))
        style.configure("Accent.TButton", font=(FONT_FAMILY, 10, "bold"))
        style.configure("Confirm.TFrame", background="#fff3cd")
        style.configure("Confirm.TLabel", background="#fff3cd")
        style.configure("TNotebook.Tab", padding=(14, 5))
        style.configure("Treeview", rowheight=tkfont.nametofont("TkDefaultFont").metrics("linespace") + 10)

    # ---- 画面遷移 ----

    def show_home(self, d: date | None = None):
        if d is not None:
            self.home.set_date(d)
        else:
            self.home.refresh()
        self.notebook.select(self.home)

    def open_new_task(self, start_date: date | None = None):
        self.form.load_new(start_date)
        self.notebook.select(self.form)
        self.form.focus_title()

    def open_edit_task(self, task_id: str):
        task = self.store.get_task(task_id)
        if task is None:
            return
        self.form.load_task(task)
        self.notebook.select(self.form)
        self.form.focus_title()

    def set_form_tab_title(self, text: str):
        if self.form is not None and str(self.form) in self.notebook.tabs():
            self.notebook.tab(self.form, text=text)

    def on_task_deleted(self, task_id: str):
        if self.form.editing is not None and self.form.editing.id == task_id:
            self.form.load_new()

    def _on_tab_changed(self, _event=None):
        self.home.flush_memo()
        current = self.nametowidget(self.notebook.select())
        if current is not self.form and hasattr(current, "refresh"):
            current.refresh()

    # ---- ステータス表示 ----

    def set_status(self, message: str, error: bool = False, sticky: bool = False):
        if self._status_job is not None:
            self.after_cancel(self._status_job)
            self._status_job = None
        self.status.configure(text=message, foreground=WARN_COLOR if error else SUB_COLOR)
        if not sticky:
            self._status_job = self.after(STATUS_CLEAR_MS, lambda: self.status.configure(text=""))

    def _on_close(self):
        self.home.flush_memo()
        self.destroy()
