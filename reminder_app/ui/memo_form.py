"""今日のメモの登録画面。日付を選んで、その日のメモを書く。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import customtkinter as ctk

from ..models import format_date_jp
from . import theme
from .widgets import DateField, card, ghost_button, primary_button

if TYPE_CHECKING:
    from .app import App


class MemoFormPage(ctk.CTkFrame):
    def __init__(self, master, app: App):
        super().__init__(master, fg_color=theme.BG)
        self.app = app
        self.fonts = f = app.fonts
        self.memo_date = date.today()  # 入力欄のテキストがどの日のものか
        self._dirty = False
        self._loading = False

        box = card(self, fg_color=theme.MEMO_BG, border_color=theme.MEMO_BORDER)
        box.pack(fill="both", expand=True, pady=(4, 4))
        ctk.CTkLabel(box, text="📝 今日のメモを登録", font=f.heading, text_color=theme.MEMO_ACCENT).pack(
            anchor="w", padx=20, pady=(14, 4)
        )

        # 日付の選択
        date_row = ctk.CTkFrame(box, fg_color="transparent")
        date_row.pack(fill="x", padx=20, pady=(4, 0))
        ctk.CTkLabel(date_row, text="日付", font=f.body_bold, text_color=theme.TEXT).pack(side="left", padx=(0, 10))
        self.date_field = DateField(date_row, f, on_change=self.set_date)
        self.date_field.pack(side="left")
        self.date_field.entry.bind("<Return>", lambda e: self._on_date_typed())
        ghost_button(date_row, "今日", lambda: self.set_date(date.today()), f).pack(side="left", padx=(10, 0))
        ghost_button(date_row, "明日", lambda: self.set_date(date.today() + timedelta(days=1)), f).pack(side="left", padx=(6, 0))
        self.date_label = ctk.CTkLabel(date_row, font=f.subheading, text_color=theme.TEXT)
        self.date_label.pack(side="left", padx=(16, 0))
        self.exists_label = ctk.CTkLabel(date_row, font=f.small, text_color=theme.SUB)
        self.exists_label.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            box, text="例）9:00- 授業　13:00- 研究室ミーティング　18:00- バイト", font=f.small, text_color=theme.SUB
        ).pack(anchor="w", padx=20, pady=(10, 2))
        self.memo_text = ctk.CTkTextbox(
            box, font=f.memo, wrap="word", undo=True, corner_radius=10, border_width=1,
            fg_color=theme.MEMO_TEXT_BG, border_color=theme.MEMO_BORDER, text_color=theme.TEXT,
        )
        self.memo_text.pack(fill="both", expand=True, padx=20)
        self.memo_text.bind("<<Modified>>", self._on_modified)

        footer = ctk.CTkFrame(box, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(10, 14))
        self.message = ctk.CTkLabel(footer, text="", font=f.body, text_color=theme.SUB)
        self.message.pack(side="left")
        primary_button(footer, "保存する", self._save, f, width=120).pack(side="right")
        ghost_button(footer, "キャンセル", self._cancel, f, width=100, height=34).pack(side="right", padx=(0, 8))

        self._load(date.today())

    # ---- 読み込み ----

    def refresh(self):
        """タブを開いたとき、未保存の入力がなければ最新の内容を読み直す。"""
        if not self._dirty:
            self._load(self.memo_date)

    def _load(self, d: date):
        self.memo_date = d
        self.date_field.set(d)
        self.date_label.configure(text=format_date_jp(d))
        existing = self.app.store.get_memo(d)
        self.exists_label.configure(text="（この日のメモを編集します）" if existing else "（新しいメモ）")
        self._loading = True
        self.memo_text.delete("1.0", "end")
        self.memo_text.insert("1.0", existing)
        self.memo_text.edit_reset()
        self.memo_text.edit_modified(False)
        self._loading = False
        self._dirty = False

    def focus_text(self):
        self.memo_text.focus_set()

    def _on_modified(self, _event=None):
        if self._loading or not self.memo_text.edit_modified():
            return
        self.memo_text.edit_modified(False)
        self._dirty = True
        self.message.configure(text="")

    # ---- 日付の切り替え ----

    def _on_date_typed(self):
        try:
            d = self.date_field.get()
        except ValueError:
            d = None
        if d is None:
            self.message.configure(text="日付は 2026-10-05 のように入力するか、📅 から選んでください。", text_color=theme.DANGER)
            return
        if d != self.memo_date:
            self.set_date(d)

    def set_date(self, d: date):
        # 書きかけの内容は消さずに、元の日付のメモとして保存してから切り替える
        if self._is_dirty():
            self.app.store.set_memo(self.memo_date, self._text())
            self.app.set_status(f"{format_date_jp(self.memo_date)} のメモを保存しました。")
        self._load(d)
        self.message.configure(text="")

    # ---- 保存 ----

    def _text(self) -> str:
        return self.memo_text.get("1.0", "end-1c")

    def _is_dirty(self) -> bool:
        return self._dirty or self.memo_text.edit_modified()

    def _save(self):
        """日付欄に表示されている日付のメモとして保存する。"""
        try:
            d = self.date_field.get()
        except ValueError:
            d = None
        if d is None:
            self.message.configure(text="日付は 2026-10-05 のように入力するか、📅 から選んでください。", text_color=theme.DANGER)
            return
        text = self._text()
        if not text.strip():
            self.message.configure(text="メモを入力してください。", text_color=theme.DANGER)
            return
        self.app.store.set_memo(d, text)
        self.app.set_status(f"{format_date_jp(d)} のメモを保存しました。")
        self._dirty = False
        self._load(date.today())
        self.app.show_home(d)

    def _cancel(self):
        self._load(date.today())
        self.message.configure(text="")
        self.app.show_home()
