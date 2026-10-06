"""メインウインドウ。すべての画面を1つのウインドウ内のタブで切り替える。"""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

from ..storage import Store
from . import theme
from .completed import CompletedPage
from .home import HomePage
from .memo_form import MemoFormPage
from .registered import RegisteredPage
from .task_form import TaskFormPage
from .theme import Fonts
from .widgets import CalendarPopup

STATUS_CLEAR_MS = 5000

TAB_HOME = "🏠 ホーム"
TAB_FORM = "➕ タスク登録"
TAB_MEMO = "📝 メモ登録"
TAB_COMPLETED = "✅ 完了済み"
TAB_REGISTERED = "📋 登録済み一覧"


class App(ctk.CTk):
    def __init__(self, store: Store):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=theme.BG)
        self.store = store
        self.fonts = Fonts()
        self.title("リマインダー")
        self.geometry("1100x780")
        self.minsize(860, 620)
        self._status_job = None

        # 上部: アプリ名とタブ
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(14, 6))
        ctk.CTkLabel(header, text="🗓 リマインダー", font=self.fonts.app_title, text_color=theme.TEXT).pack(side="left")
        self.tab_bar = ctk.CTkSegmentedButton(
            header,
            values=[TAB_HOME, TAB_FORM, TAB_MEMO, TAB_COMPLETED, TAB_REGISTERED],
            command=self.show_page,
            font=self.fonts.body_bold,
            height=36,
            corner_radius=18,
            fg_color=theme.GHOST,
            unselected_color=theme.GHOST,
            unselected_hover_color=theme.GHOST_HOVER,
            selected_color=theme.PRIMARY,
            selected_hover_color=theme.PRIMARY_HOVER,
            text_color=theme.TEXT,
        )
        self.tab_bar.pack(side="right")

        # 中央: 各画面を同じ場所に重ね、選ばれたものを前面に出す
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        self.home = HomePage(content, self)
        self.form = TaskFormPage(content, self)
        self.memo_form = MemoFormPage(content, self)
        self.completed = CompletedPage(content, self)
        self.registered = RegisteredPage(content, self)
        self.pages = {
            TAB_HOME: self.home,
            TAB_FORM: self.form,
            TAB_MEMO: self.memo_form,
            TAB_COMPLETED: self.completed,
            TAB_REGISTERED: self.registered,
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        # 下部: お知らせ
        self.status = ctk.CTkLabel(self, text="", font=self.fonts.small, text_color=theme.SUB, height=26)
        self.status.pack(fill="x", padx=20, pady=(2, 6))

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_page(TAB_HOME)
        if store.load_warning:
            self.set_status(store.load_warning, error=True, sticky=True)

    # ---- 画面遷移 ----

    def show_page(self, name: str):
        CalendarPopup.close_current()
        self.home.flush_memo()
        self.tab_bar.set(name)
        page = self.pages[name]
        if page is not self.form:
            page.refresh()
        page.tkraise()

    def show_home(self, d: date | None = None, focus_memo: bool = False):
        if d is not None:
            self.home.flush_memo()
            self.home.current = d
        self.show_page(TAB_HOME)
        if focus_memo:
            self.home.focus_memo()

    def open_new_task(self, start_date: date | None = None):
        self.form.load_new(start_date)
        self.show_page(TAB_FORM)
        self.form.focus_title()

    def open_memo(self, d: date | None = None):
        """メモ登録画面を開く。日付を指定すると、その日のメモを表示する。"""
        self.show_page(TAB_MEMO)
        if d is not None:
            self.memo_form.set_date(d)
        self.memo_form.focus_text()

    def open_edit_task(self, task_id: str):
        task = self.store.get_task(task_id)
        if task is None:
            return
        self.form.load_task(task)
        self.show_page(TAB_FORM)
        self.form.focus_title()

    def delete_task(self, task_id: str):
        task = self.store.get_task(task_id)
        if task is None:
            return
        self.store.delete_task(task_id)
        if self.form.editing is not None and self.form.editing.id == task_id:
            self.form.load_new()
        self.set_status(f"「{task.title}」を削除しました。")

    # ---- お知らせ ----

    def set_status(self, message: str, error: bool = False, sticky: bool = False):
        if self._status_job is not None:
            self.after_cancel(self._status_job)
            self._status_job = None
        self.status.configure(text=message, text_color=theme.DANGER if error else theme.SUB)
        if not sticky:
            self._status_job = self.after(STATUS_CLEAR_MS, lambda: self.status.configure(text=""))

    def _on_close(self):
        self.home.flush_memo()
        self.destroy()
