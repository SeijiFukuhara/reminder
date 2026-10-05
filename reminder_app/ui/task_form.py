"""タスクの登録・編集画面。"""

from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from datetime import date
from typing import TYPE_CHECKING

import customtkinter as ctk

from ..models import END_DATE, END_DUE, END_NONE, Link, Task, normalize_url
from . import theme
from .widgets import DateField, DeleteButton, card, ghost_button, primary_button, scroll_frame

if TYPE_CHECKING:
    from .app import App

END_LABELS = {END_NONE: "指定しない", END_DUE: "期日まで", END_DATE: "日付を指定"}
END_BY_LABEL = {label: mode for mode, label in END_LABELS.items()}


class TaskFormPage(ctk.CTkFrame):
    def __init__(self, master, app: App):
        super().__init__(master, fg_color=theme.BG)
        self.app = app
        self.fonts = f = app.fonts
        self.editing: Task | None = None
        self.links: list[Link] = []

        box = card(self)
        box.pack(fill="both", expand=True, pady=(4, 4))
        self.heading = ctk.CTkLabel(box, font=f.heading, text_color=theme.TEXT)
        self.heading.pack(anchor="w", padx=20, pady=(14, 4))

        body = scroll_frame(box)
        body.pack(fill="both", expand=True, padx=8)
        body.grid_columnconfigure(1, weight=1)
        self._row = 0

        # タイトル
        self.title_var = tk.StringVar()
        self.title_entry = ctk.CTkEntry(body, textvariable=self.title_var, font=f.task, height=38, corner_radius=10)
        self._field(body, "タイトル", self.title_entry, sticky="ew")

        # 期日
        due_row = ctk.CTkFrame(body, fg_color="transparent")
        self.has_due_var = tk.BooleanVar()
        ctk.CTkSwitch(
            due_row, text="期日を設定する", variable=self.has_due_var, onvalue=True, offvalue=False,
            font=f.body, progress_color=theme.PRIMARY, command=self._on_due_toggled,
        ).pack(side="left")
        self.due_field = DateField(due_row, f)
        self.due_field.pack(side="left", padx=(14, 0))
        self._field(body, "期日", due_row)

        # 表示期間（開始日〜終了日）
        period = ctk.CTkFrame(body, fg_color="transparent")
        ctk.CTkLabel(period, text="表示開始日", font=f.body, text_color=theme.SUB).grid(row=0, column=0, sticky="w")
        self.start_field = DateField(period, f)
        self.start_field.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=3)
        ctk.CTkLabel(period, text="表示終了日", font=f.body, text_color=theme.SUB).grid(row=1, column=0, sticky="w")
        end_row = ctk.CTkFrame(period, fg_color="transparent")
        end_row.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=3)
        self.end_mode_button = ctk.CTkSegmentedButton(
            end_row, values=list(END_LABELS.values()), command=self._on_end_mode, font=f.body,
            selected_color=theme.PRIMARY, selected_hover_color=theme.PRIMARY_HOVER,
            unselected_color=theme.GHOST, unselected_hover_color=theme.GHOST_HOVER, text_color=theme.TEXT,
            fg_color=theme.GHOST, corner_radius=14, height=32,
        )
        self.end_mode_button.pack(side="left")
        self.until_field = DateField(end_row, f)
        self.until_field.pack(side="left", padx=(10, 0))
        self.end_hint = ctk.CTkLabel(period, font=f.small, text_color=theme.SUB)
        self.end_hint.grid(row=2, column=1, sticky="w", padx=(10, 0))
        self._field(body, "表示期間", period)

        # 完了後の扱い
        keep_row = ctk.CTkFrame(body, fg_color="transparent")
        self.keep_var = tk.BooleanVar()
        ctk.CTkSwitch(
            keep_row, text="完了しても翌日以降も表示し続ける", variable=self.keep_var, onvalue=True, offvalue=False,
            font=f.body, progress_color=theme.PRIMARY, command=self._sync_states,
        ).pack(anchor="w")
        ctk.CTkLabel(
            keep_row, text="毎日のメール確認などに。チェックは日ごとに記録され、翌日はまた未完了で表示されます。",
            font=f.small, text_color=theme.SUB,
        ).pack(anchor="w")
        self._field(body, "完了後", keep_row)

        # メモ
        self.memo_text = ctk.CTkTextbox(
            body, height=110, font=f.body, wrap="word", undo=True, corner_radius=10, border_width=1,
            border_color=theme.BORDER, fg_color="#fbfcfe",
        )
        self._field(body, "メモ", self.memo_text, sticky="ew")

        # リンク
        self._field(body, "リンク", self._build_link_area(body), sticky="ew")

        # 下部: エラー表示とボタン
        footer = ctk.CTkFrame(box, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(6, 14))
        self.error_label = ctk.CTkLabel(footer, text="", font=f.body, text_color=theme.DANGER, justify="left")
        self.error_label.pack(side="left")
        primary_button(footer, "保存する", self._save, f, width=120).pack(side="right")
        ghost_button(footer, "キャンセル", self._cancel, f, width=100, height=34).pack(side="right", padx=(0, 8))
        self.delete_button = DeleteButton(footer, f, self._delete, text="このタスクを削除", question="本当に削除しますか？")

        self.load_new()

    def _field(self, body, label: str, widget, sticky="w"):
        ctk.CTkLabel(body, text=label, font=self.fonts.body_bold, text_color=theme.TEXT).grid(
            row=self._row, column=0, sticky="nw", padx=(12, 16), pady=(12, 0)
        )
        widget.grid(row=self._row, column=1, sticky=sticky, padx=(0, 12), pady=(8, 0))
        self._row += 1

    def _build_link_area(self, master) -> ctk.CTkFrame:
        f = self.fonts
        area = ctk.CTkFrame(master, fg_color="transparent")
        area.grid_columnconfigure(0, weight=1)

        inputs = ctk.CTkFrame(area, fg_color="transparent")
        inputs.grid(row=0, column=0, sticky="ew")
        inputs.grid_columnconfigure(0, weight=3)
        inputs.grid_columnconfigure(1, weight=1)
        self.url_var = tk.StringVar()
        self.link_title_var = tk.StringVar()
        url_entry = ctk.CTkEntry(inputs, textvariable=self.url_var, font=f.body, corner_radius=10)
        url_entry.grid(row=0, column=0, sticky="ew")
        title_entry = ctk.CTkEntry(inputs, textvariable=self.link_title_var, font=f.body, corner_radius=10)
        title_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(inputs, text="URL", font=f.small, text_color=theme.SUB).grid(row=1, column=0, sticky="w", padx=4)
        ctk.CTkLabel(inputs, text="表示名（任意）", font=f.small, text_color=theme.SUB).grid(row=1, column=1, sticky="w", padx=12)
        for entry in (url_entry, title_entry):
            entry.bind("<Return>", lambda e: self._add_link())
        primary_button(inputs, "追加", self._add_link, f, width=70).grid(row=0, column=2, padx=(8, 0))
        ghost_button(inputs, "📋 クリップボードから追加", self._add_link_from_clipboard, f, width=190, height=34).grid(
            row=0, column=3, padx=(8, 0)
        )

        self.link_list = ctk.CTkFrame(area, fg_color="transparent")
        self.link_list.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return area

    # ---- フォームの読み込み ----

    def load_new(self, start_date: date | None = None):
        self.editing = None
        self._fill(Task(title="", start_date=start_date or date.today()))
        self.heading.configure(text="✏️ タスクを登録")
        self.delete_button.pack_forget()

    def load_task(self, task: Task):
        self.editing = task
        self._fill(task)
        self.heading.configure(text="✏️ タスクを編集")
        self.delete_button.reset()
        self.delete_button.pack(side="right", padx=(0, 16))

    def _fill(self, task: Task):
        self.title_var.set(task.title)
        self.start_field.set(task.start_date)
        self.has_due_var.set(task.due_date is not None)
        self.due_field.set(task.due_date)
        self.keep_var.set(task.keep_after_done)
        self.end_mode_button.set(END_LABELS[task.end_mode])
        self.until_field.set(task.display_until)
        self.links = [replace(link) for link in task.links]
        self._render_links()
        self.url_var.set("")
        self.link_title_var.set("")
        self.memo_text.delete("1.0", "end")
        self.memo_text.insert("1.0", task.memo)
        self.memo_text.edit_reset()
        self.error_label.configure(text="")
        self._sync_states()

    def focus_title(self):
        self.title_entry.focus_set()

    # ---- 入力欄の連動 ----

    def _end_mode(self) -> str:
        return END_BY_LABEL[self.end_mode_button.get()]

    def _on_due_toggled(self):
        # 期日をなくしたら「期日まで」は選べないので「指定しない」に戻す
        if not self.has_due_var.get() and self._end_mode() == END_DUE:
            self.end_mode_button.set(END_LABELS[END_NONE])
        self._sync_states()

    def _on_end_mode(self, _value=None):
        # 「期日まで」を選んだら期日を設定する
        if self._end_mode() == END_DUE and not self.has_due_var.get():
            self.has_due_var.set(True)
        self._sync_states()

    def _sync_states(self):
        self.due_field.set_enabled(self.has_due_var.get())
        mode = self._end_mode()
        self.until_field.set_enabled(mode == END_DATE)
        if mode == END_NONE:
            hint = "ずっと表示します。" if self.keep_var.get() else "完了するまで表示します。"
        elif mode == END_DUE:
            hint = "期日の日まで表示します。"
        else:
            hint = "指定した日まで表示します。"
        self.end_hint.configure(text=hint)

    # ---- リンク ----

    def _render_links(self):
        for child in self.link_list.winfo_children():
            child.destroy()
        for i, link in enumerate(self.links):
            chip = ctk.CTkFrame(self.link_list, fg_color=theme.GHOST, corner_radius=12)
            chip.pack(anchor="w", pady=2)
            text = f"🔗 {link.title}（{link.url}）" if link.title else f"🔗 {link.url}"
            ctk.CTkLabel(chip, text=text, font=self.fonts.body, text_color=theme.TEXT).pack(side="left", padx=(10, 4))
            ctk.CTkButton(
                chip, text="✕", width=26, height=24, corner_radius=12, font=self.fonts.small_bold,
                fg_color="transparent", hover_color=theme.GHOST_HOVER, text_color=theme.SUB,
                command=lambda i=i: self._remove_link(i),
            ).pack(side="left", padx=(0, 4))

    def _add_link(self, url: str | None = None):
        url = normalize_url(url if url is not None else self.url_var.get())
        if not url:
            self.error_label.configure(text="URLを入力してください。")
            return
        self.links.append(Link(url=url, title=self.link_title_var.get().strip()))
        self.url_var.set("")
        self.link_title_var.set("")
        self.error_label.configure(text="")
        self._render_links()

    def _add_link_from_clipboard(self):
        try:
            text = self.clipboard_get().strip()
        except tk.TclError:
            text = ""
        if not text or any(c.isspace() for c in text):
            self.error_label.configure(text="クリップボードにURLがありません。")
            return
        self._add_link(text)

    def _remove_link(self, index: int):
        del self.links[index]
        self._render_links()

    # ---- 保存・削除 ----

    def _collect(self) -> tuple[Task | None, list[str]]:
        errors = []
        dates = {}
        mode = self._end_mode()
        for key, field_, label, needed in [
            ("start", self.start_field, "表示開始日", True),
            ("due", self.due_field, "期日", self.has_due_var.get()),
            ("until", self.until_field, "表示終了日", mode == END_DATE),
        ]:
            dates[key] = None
            if not needed:
                continue
            try:
                dates[key] = field_.get()
            except ValueError:
                errors.append(f"{label}は 2026-10-05 のような形式で入力してください（📅 から選ぶこともできます）。")
                continue
            if dates[key] is None:
                errors.append(f"{label}を入力してください。")
        if errors:
            return None, errors

        task = Task(
            title=self.title_var.get().strip(),
            start_date=dates["start"],
            due_date=dates["due"],
            keep_after_done=self.keep_var.get(),
            end_mode=mode,
            display_until=dates["until"],
            memo=self.memo_text.get("1.0", "end-1c").strip(),
            links=list(self.links),
        )
        base = self.editing
        if base is not None:
            task.id = base.id
            task.created_at = base.created_at
            task.completions = dict(base.completions)
            if base.keep_after_done and not task.keep_after_done and len(task.completions) > 1:
                # 継続タスクから通常タスクに変えた場合は、最初に完了した日だけを残す
                first = min(task.completions)
                task.completions = {first: task.completions[first]}
        return task, task.validate()

    def _save(self):
        task, errors = self._collect()
        if errors:
            self.error_label.configure(text="\n".join(errors))
            return
        if self.editing is None:
            self.app.store.add_task(task)
            self.app.set_status(f"「{task.title}」を登録しました。")
        else:
            self.app.store.update_task(task)
            self.app.set_status(f"「{task.title}」を更新しました。")
        self.load_new()
        self.app.show_home()

    def _delete(self):
        if self.editing is not None:
            self.app.delete_task(self.editing.id)
        self.load_new()
        self.app.show_home()

    def _cancel(self):
        self.load_new()
        self.app.show_home()
