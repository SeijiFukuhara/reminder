"""タスクの登録・編集画面。"""

from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from datetime import date
from tkinter import ttk
from typing import TYPE_CHECKING

from ..models import END_DATE, END_DUE, END_NONE, Link, Task, normalize_url
from .widgets import SUB_COLOR, WARN_COLOR, DateField

if TYPE_CHECKING:
    from .app import App


class TaskFormTab(ttk.Frame):
    def __init__(self, master, app: App):
        super().__init__(master, padding=16)
        self.app = app
        self.editing: Task | None = None
        self.links: list[Link] = []

        self.heading = ttk.Label(self, style="Heading.TLabel")
        self.heading.pack(anchor="w", pady=(0, 10))

        form = ttk.Frame(self)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)
        form.rowconfigure(6, weight=1)
        pad = {"padx": (0, 12), "pady": 5}

        # タイトル
        ttk.Label(form, text="タイトル").grid(row=0, column=0, sticky="w", **pad)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(form, textvariable=self.title_var)
        self.title_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # 表示開始日
        ttk.Label(form, text="表示開始日").grid(row=1, column=0, sticky="w", **pad)
        self.start_field = DateField(form)
        self.start_field.grid(row=1, column=1, sticky="w", pady=5)

        # 期日の有無
        ttk.Label(form, text="期日").grid(row=2, column=0, sticky="w", **pad)
        due_row = ttk.Frame(form)
        due_row.grid(row=2, column=1, sticky="w", pady=5)
        self.has_due_var = tk.BooleanVar()
        ttk.Checkbutton(due_row, text="期日を設定する", variable=self.has_due_var, command=self._sync_states).pack(
            side="left"
        )
        self.due_field = DateField(due_row)
        self.due_field.pack(side="left", padx=(10, 0))

        # 完了しても表示し続けるか
        ttk.Label(form, text="完了後").grid(row=3, column=0, sticky="w", **pad)
        keep_row = ttk.Frame(form)
        keep_row.grid(row=3, column=1, sticky="w", pady=5)
        self.keep_var = tk.BooleanVar()
        ttk.Checkbutton(
            keep_row, text="完了しても翌日以降も表示し続ける", variable=self.keep_var, command=self._sync_states
        ).pack(side="left")
        ttk.Label(keep_row, text="（毎日のメール確認など。チェックは日ごとに記録されます）", foreground=SUB_COLOR).pack(
            side="left", padx=(6, 0)
        )

        # いつまで表示するか
        ttk.Label(form, text="表示する期間").grid(row=4, column=0, sticky="nw", **pad)
        end_box = ttk.Frame(form)
        end_box.grid(row=4, column=1, sticky="w", pady=5)
        self.end_mode_var = tk.StringVar(value=END_NONE)
        self.end_none_radio = ttk.Radiobutton(
            end_box, variable=self.end_mode_var, value=END_NONE, command=self._sync_states
        )
        self.end_none_radio.grid(row=0, column=0, columnspan=2, sticky="w")
        self.end_due_radio = ttk.Radiobutton(
            end_box, text="期日まで表示する", variable=self.end_mode_var, value=END_DUE, command=self._sync_states
        )
        self.end_due_radio.grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Radiobutton(
            end_box, text="指定した日まで表示する：", variable=self.end_mode_var, value=END_DATE, command=self._sync_states
        ).grid(row=2, column=0, sticky="w")
        self.until_field = DateField(end_box)
        self.until_field.grid(row=2, column=1, sticky="w")

        # リンク
        ttk.Label(form, text="リンク").grid(row=5, column=0, sticky="nw", **pad)
        self._build_link_area(form).grid(row=5, column=1, sticky="ew", pady=5)

        # メモ
        ttk.Label(form, text="メモ").grid(row=6, column=0, sticky="nw", **pad)
        memo_frame = ttk.Frame(form)
        memo_frame.grid(row=6, column=1, sticky="nsew", pady=5)
        self.memo_text = tk.Text(memo_frame, height=6, wrap="word", undo=True, font=("Yu Gothic UI", 10), padx=4, pady=4)
        memo_scroll = ttk.Scrollbar(memo_frame, orient="vertical", command=self.memo_text.yview)
        self.memo_text.configure(yscrollcommand=memo_scroll.set)
        self.memo_text.pack(side="left", fill="both", expand=True)
        memo_scroll.pack(side="right", fill="y")

        # 保存・キャンセル
        footer = ttk.Frame(self)
        footer.pack(fill="x", pady=(10, 0))
        self.error_label = ttk.Label(footer, foreground=WARN_COLOR, justify="left")
        self.error_label.pack(side="left")
        ttk.Button(footer, text="キャンセル", command=self._cancel).pack(side="right")
        ttk.Button(footer, text="保存", style="Accent.TButton", command=self._save).pack(side="right", padx=(0, 8))

        self.load_new()

    def _build_link_area(self, master) -> ttk.Frame:
        area = ttk.Frame(master)
        area.columnconfigure(1, weight=1)

        ttk.Label(area, text="URL").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(area, textvariable=self.url_var)
        url_entry.grid(row=0, column=1, sticky="ew")
        url_entry.bind("<Return>", lambda e: self._add_link())
        ttk.Label(area, text="表示名（任意）").grid(row=0, column=2, sticky="w", padx=(10, 6))
        self.link_title_var = tk.StringVar()
        title_entry = ttk.Entry(area, textvariable=self.link_title_var, width=20)
        title_entry.grid(row=0, column=3, sticky="w")
        title_entry.bind("<Return>", lambda e: self._add_link())
        ttk.Button(area, text="追加", command=self._add_link).grid(row=0, column=4, padx=(6, 0))

        self.link_list = tk.Listbox(area, height=3, activestyle="none")
        self.link_list.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        buttons = ttk.Frame(area)
        buttons.grid(row=1, column=4, sticky="n", padx=(6, 0), pady=(6, 0))
        ttk.Button(buttons, text="クリップボードから追加", command=self._add_link_from_clipboard).pack(fill="x")
        ttk.Button(buttons, text="選択したリンクを削除", command=self._remove_link).pack(fill="x", pady=(4, 0))
        return area

    # ---- フォームの読み込み ----

    def load_new(self, start_date: date | None = None):
        self.editing = None
        self._fill(Task(title="", start_date=start_date or date.today()))
        self.heading.configure(text="タスクを登録")
        self.app.set_form_tab_title("タスク登録")

    def load_task(self, task: Task):
        self.editing = task
        self._fill(task)
        self.heading.configure(text="タスクを編集")
        self.app.set_form_tab_title("タスク編集")

    def _fill(self, task: Task):
        self.title_var.set(task.title)
        self.start_field.set(task.start_date)
        self.has_due_var.set(task.due_date is not None)
        self.due_field.set(task.due_date)
        self.keep_var.set(task.keep_after_done)
        self.end_mode_var.set(task.end_mode)
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

    def _sync_states(self):
        """チェック状態に合わせて入力欄の有効・無効を切り替える。"""
        has_due = self.has_due_var.get()
        self.due_field.set_enabled(has_due)
        if not has_due and self.end_mode_var.get() == END_DUE:
            self.end_mode_var.set(END_NONE)
        self.end_due_radio.configure(state="normal" if has_due else "disabled")
        self.end_none_radio.configure(
            text="ずっと表示する" if self.keep_var.get() else "完了するまで表示する"
        )
        self.until_field.set_enabled(self.end_mode_var.get() == END_DATE)

    # ---- リンク ----

    def _render_links(self):
        self.link_list.delete(0, "end")
        for link in self.links:
            self.link_list.insert("end", f"{link.title}  —  {link.url}" if link.title else link.url)

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

    def _remove_link(self):
        for index in reversed(self.link_list.curselection()):
            del self.links[index]
        self._render_links()

    # ---- 保存 ----

    def _collect(self) -> tuple[Task | None, list[str]]:
        errors = []
        dates = {}
        for key, field_, label, needed in [
            ("start", self.start_field, "表示開始日", True),
            ("due", self.due_field, "期日", self.has_due_var.get()),
            ("until", self.until_field, "表示する最終日", self.end_mode_var.get() == END_DATE),
        ]:
            if not needed:
                dates[key] = None
                continue
            try:
                dates[key] = field_.get()
            except ValueError:
                errors.append(f"{label}は 2026-10-05 のような形式で入力してください。")
                dates[key] = None
        if dates["start"] is None and not errors:
            errors.append("表示開始日を入力してください。")
        if self.has_due_var.get() and dates["due"] is None and not errors:
            errors.append("期日を入力してください。")
        if errors:
            return None, errors

        base = self.editing
        task = Task(
            title=self.title_var.get().strip(),
            start_date=dates["start"],
            due_date=dates["due"],
            keep_after_done=self.keep_var.get(),
            end_mode=self.end_mode_var.get(),
            display_until=dates["until"],
            memo=self.memo_text.get("1.0", "end-1c").strip(),
            links=list(self.links),
        )
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
        show_date = self.app.home.current
        self.load_new()
        self.app.show_home(show_date)

    def _cancel(self):
        self.load_new()
        self.app.show_home()
