"""タスクとメモをJSONファイルに保存・読み込みする。"""

from __future__ import annotations

import json
import os
import shutil
from datetime import date, datetime
from pathlib import Path

from .models import Task

DATA_VERSION = 1


def default_data_path() -> Path:
    """環境変数 REMINDER_DATA_FILE があればそれを、なければ %APPDATA%/ReminderApp/data.json を使う。"""
    override = os.environ.get("REMINDER_DATA_FILE")
    if override:
        return Path(override)
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "ReminderApp" / "data.json"


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.tasks: list[Task] = []
        self.memos: dict[str, str] = {}  # 日付（ISO形式）→ その日のメモ
        self.load_warning: str | None = None

    @classmethod
    def load(cls, path: Path) -> Store:
        store = cls(path)
        if not path.exists():
            return store
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            store.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
            store.memos = dict(data.get("memos", {}))
        except (ValueError, KeyError, TypeError) as e:
            # 壊れたファイルは消さずに退避して、空の状態で起動する
            backup = path.with_name(f"{path.stem}.broken-{datetime.now():%Y%m%d%H%M%S}{path.suffix}")
            shutil.copy2(path, backup)
            store.tasks, store.memos = [], {}
            store.load_warning = f"データの読み込みに失敗したため、{backup.name} に退避しました（{e}）"
        return store

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": DATA_VERSION,
            "tasks": [t.to_dict() for t in self.tasks],
            "memos": self.memos,
        }
        # 書き込み途中で終了してもファイルが壊れないよう、一時ファイルから置き換える
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    # ---- タスク ----

    def get_task(self, task_id: str) -> Task | None:
        return next((t for t in self.tasks if t.id == task_id), None)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)
        self.save()

    def update_task(self, task: Task) -> None:
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
        else:
            self.tasks.append(task)
        self.save()

    def delete_task(self, task_id: str) -> None:
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.save()

    def set_task_done(self, task_id: str, d: date, done: bool) -> None:
        task = self.get_task(task_id)
        if task is not None:
            task.set_done(d, done)
            self.save()

    def tasks_on(self, d: date) -> list[Task]:
        """その日に表示するタスク。未完了→完了の順、その中は期日の近い順。"""
        visible = [t for t in self.tasks if t.is_visible_on(d)]
        return sorted(
            visible,
            key=lambda t: (t.is_done_on(d), t.due_date or date.max, t.created_at),
        )

    def completed_by_date(self) -> list[tuple[date, list[tuple[Task, str]]]]:
        """完了済みタスクを完了した日ごとにまとめる（新しい日付が先）。"""
        groups: dict[str, list[tuple[Task, str]]] = {}
        for task in self.tasks:
            for day, done_at in task.completions.items():
                groups.setdefault(day, []).append((task, done_at))
        return [
            (date.fromisoformat(day), sorted(groups[day], key=lambda item: item[1]))
            for day in sorted(groups, reverse=True)
        ]

    # ---- 今日のメモ ----

    def get_memo(self, d: date) -> str:
        return self.memos.get(d.isoformat(), "")

    def set_memo(self, d: date, text: str) -> None:
        if text.strip():
            self.memos[d.isoformat()] = text
        else:
            self.memos.pop(d.isoformat(), None)
        self.save()

    def delete_memo(self, d: date) -> None:
        self.memos.pop(d.isoformat(), None)
        self.save()

    def memo_dates(self) -> list[date]:
        return sorted((date.fromisoformat(k) for k in self.memos), reverse=True)
