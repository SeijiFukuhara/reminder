"""タスクのデータ定義と、ある日にタスクを表示するかどうかの判定ロジック。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

# 表示する期間（いつまで表示するか）
END_NONE = "none"  # 終了日なし（通常タスクは完了するまで、継続タスクはずっと）
END_DUE = "due"  # 期日まで
END_DATE = "date"  # 指定した日まで
END_MODES = (END_NONE, END_DUE, END_DATE)

WEEKDAYS = "月火水木金土日"


def parse_date(text: str) -> date:
    """'YYYY-MM-DD' または 'YYYY/MM/DD' 形式の文字列を date に変換する。"""
    return datetime.strptime(text.strip().replace("/", "-"), "%Y-%m-%d").date()


def format_date_jp(d: date) -> str:
    """例: 2026年10月5日（月）"""
    return f"{d.year}年{d.month}月{d.day}日（{WEEKDAYS[d.weekday()]}）"


def format_date_short(d: date) -> str:
    """例: 10/5（月）"""
    return f"{d.month}/{d.day}（{WEEKDAYS[d.weekday()]}）"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalize_url(url: str) -> str:
    """スキームのないURLには https:// を付ける。"""
    url = url.strip()
    if url and "://" not in url and not url.startswith("mailto:"):
        url = "https://" + url
    return url


@dataclass
class Link:
    url: str
    title: str = ""

    @property
    def label(self) -> str:
        return self.title or self.url


@dataclass
class Task:
    title: str
    start_date: date  # 表示を始める日
    due_date: date | None = None  # 期日（なしも可）
    keep_after_done: bool = False  # 完了しても翌日以降も表示し続ける（毎日のメール確認など）
    end_mode: str = END_NONE  # いつまで表示するか
    display_until: date | None = None  # end_mode == END_DATE のときの表示最終日
    memo: str = ""
    links: list[Link] = field(default_factory=list)
    # 完了した日（ISO形式）→ 完了操作をした日時。継続タスクは日ごとに記録する
    completions: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: str = field(default_factory=now_iso)

    # ---- 入力チェック ----

    def validate(self) -> list[str]:
        errors = []
        if not self.title.strip():
            errors.append("タイトルを入力してください。")
        if self.end_mode not in END_MODES:
            errors.append("表示する期間の指定が不正です。")
        if self.end_mode == END_DUE and self.due_date is None:
            errors.append("「期日まで表示」を選ぶには期日を設定してください。")
        if self.end_mode == END_DATE and self.display_until is None:
            errors.append("表示する最終日を入力してください。")
        last = self.last_visible_date()
        if last is not None and last < self.start_date:
            errors.append("表示の最終日が表示開始日より前になっています。")
        return errors

    # ---- 表示ロジック ----

    def last_visible_date(self) -> date | None:
        if self.end_mode == END_DUE:
            return self.due_date
        if self.end_mode == END_DATE:
            return self.display_until
        return None

    def completed_on(self) -> date | None:
        """通常タスクが完了した日。未完了なら None。"""
        if not self.completions:
            return None
        return date.fromisoformat(min(self.completions))

    def is_visible_on(self, d: date) -> bool:
        if d < self.start_date:
            return False
        last = self.last_visible_date()
        if last is not None and d > last:
            return False
        if self.keep_after_done:
            return True
        # 通常タスクは完了した日までは表示し、翌日以降は表示しない
        done = self.completed_on()
        return done is None or d <= done

    def is_done_on(self, d: date) -> bool:
        if self.keep_after_done:
            return d.isoformat() in self.completions
        done = self.completed_on()
        return done is not None and done <= d

    def set_done(self, d: date, done: bool) -> None:
        if self.keep_after_done:
            if done:
                self.completions[d.isoformat()] = now_iso()
            else:
                self.completions.pop(d.isoformat(), None)
        else:
            self.completions = {d.isoformat(): now_iso()} if done else {}

    def is_overdue_on(self, d: date) -> bool:
        return (
            not self.keep_after_done
            and self.due_date is not None
            and d > self.due_date
            and not self.is_done_on(d)
        )

    # ---- 保存形式との変換 ----

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start_date": self.start_date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "keep_after_done": self.keep_after_done,
            "end_mode": self.end_mode,
            "display_until": self.display_until.isoformat() if self.display_until else None,
            "memo": self.memo,
            "links": [{"url": link.url, "title": link.title} for link in self.links],
            "completions": dict(self.completions),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        def opt_date(value):
            return date.fromisoformat(value) if value else None

        return cls(
            id=data["id"],
            title=data["title"],
            start_date=date.fromisoformat(data["start_date"]),
            due_date=opt_date(data.get("due_date")),
            keep_after_done=data.get("keep_after_done", False),
            end_mode=data.get("end_mode", END_NONE),
            display_until=opt_date(data.get("display_until")),
            memo=data.get("memo", ""),
            links=[Link(url=link["url"], title=link.get("title", "")) for link in data.get("links", [])],
            completions=dict(data.get("completions", {})),
            created_at=data.get("created_at", now_iso()),
        )
