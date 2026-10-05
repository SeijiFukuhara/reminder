import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from reminder_app.models import END_DATE, END_DUE, END_NONE, Link, Task, normalize_url, parse_date
from reminder_app.storage import Store

D1 = date(2026, 10, 1)
D2 = date(2026, 10, 2)
D3 = date(2026, 10, 3)
D5 = date(2026, 10, 5)


class TaskVisibilityTest(unittest.TestCase):
    def test_normal_task_shown_until_completed_day(self):
        task = Task(title="資料作成", start_date=D1)
        self.assertFalse(task.is_visible_on(date(2026, 9, 30)))
        self.assertTrue(task.is_visible_on(D5))

        task.set_done(D2, True)
        self.assertTrue(task.is_visible_on(D1))
        self.assertFalse(task.is_done_on(D1))
        self.assertTrue(task.is_visible_on(D2))
        self.assertTrue(task.is_done_on(D2))
        self.assertFalse(task.is_visible_on(D3))

        task.set_done(D2, False)
        self.assertTrue(task.is_visible_on(D3))

    def test_keep_after_done_task_tracks_each_day(self):
        task = Task(title="メール確認", start_date=D1, keep_after_done=True)
        task.set_done(D1, True)
        self.assertTrue(task.is_done_on(D1))
        self.assertTrue(task.is_visible_on(D2))
        self.assertFalse(task.is_done_on(D2))
        task.set_done(D2, True)
        self.assertEqual(set(task.completions), {"2026-10-01", "2026-10-02"})

    def test_until_due(self):
        task = Task(title="提出", start_date=D1, due_date=D3, end_mode=END_DUE)
        self.assertTrue(task.is_visible_on(D3))
        self.assertFalse(task.is_visible_on(date(2026, 10, 4)))

    def test_until_date(self):
        task = Task(title="期間限定", start_date=D1, keep_after_done=True, end_mode=END_DATE, display_until=D2)
        self.assertTrue(task.is_visible_on(D2))
        self.assertFalse(task.is_visible_on(D3))

    def test_overdue_when_shown_until_done(self):
        task = Task(title="提出", start_date=D1, due_date=D2, end_mode=END_NONE)
        self.assertFalse(task.is_overdue_on(D2))
        self.assertTrue(task.is_overdue_on(D3))
        task.set_done(D3, True)
        self.assertFalse(task.is_overdue_on(D3))

    def test_validate(self):
        self.assertIn("タイトルを入力してください。", Task(title=" ", start_date=D1).validate())
        self.assertTrue(Task(title="a", start_date=D1, end_mode=END_DUE).validate())
        self.assertTrue(Task(title="a", start_date=D1, end_mode=END_DATE).validate())
        self.assertTrue(Task(title="a", start_date=D3, due_date=D1, end_mode=END_DUE).validate())
        self.assertEqual(Task(title="a", start_date=D1, due_date=D3, end_mode=END_DUE).validate(), [])


class HelperTest(unittest.TestCase):
    def test_parse_date(self):
        self.assertEqual(parse_date("2026/10/05"), D5)
        self.assertEqual(parse_date(" 2026-10-05 "), D5)
        with self.assertRaises(ValueError):
            parse_date("10/05")

    def test_normalize_url(self):
        self.assertEqual(normalize_url("example.com"), "https://example.com")
        self.assertEqual(normalize_url("http://example.com"), "http://example.com")
        self.assertEqual(normalize_url("  "), "")


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "data.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_round_trip(self):
        store = Store.load(self.path)
        task = Task(
            title="メール確認",
            start_date=D1,
            due_date=D3,
            keep_after_done=True,
            end_mode=END_DUE,
            memo="受信箱を確認",
            links=[Link(url="https://mail.google.com", title="Gmail")],
        )
        store.add_task(task)
        store.set_task_done(task.id, D2, True)
        store.set_memo(D2, "9:00- 会議")
        store.set_memo(D3, "   ")

        loaded = Store.load(self.path)
        self.assertEqual(loaded.tasks, store.tasks)
        self.assertEqual(loaded.get_memo(D2), "9:00- 会議")
        self.assertEqual(loaded.memo_dates(), [D2])

    def test_tasks_on_sorts_open_tasks_first(self):
        store = Store.load(self.path)
        done = Task(title="済み", start_date=D1)
        later = Task(title="期日遅い", start_date=D1, due_date=D5)
        sooner = Task(title="期日近い", start_date=D1, due_date=D3)
        for t in (done, later, sooner):
            store.add_task(t)
        store.set_task_done(done.id, D2, True)
        self.assertEqual([t.title for t in store.tasks_on(D2)], ["期日近い", "期日遅い", "済み"])

    def test_completed_by_date(self):
        store = Store.load(self.path)
        daily = Task(title="メール確認", start_date=D1, keep_after_done=True)
        once = Task(title="提出", start_date=D1)
        store.add_task(daily)
        store.add_task(once)
        store.set_task_done(daily.id, D1, True)
        store.set_task_done(daily.id, D2, True)
        store.set_task_done(once.id, D2, True)
        groups = store.completed_by_date()
        self.assertEqual([d for d, _ in groups], [D2, D1])
        self.assertEqual({t.title for t, _ in groups[0][1]}, {"メール確認", "提出"})

    def test_broken_file_is_backed_up(self):
        self.path.write_text("{ broken", encoding="utf-8")
        store = Store.load(self.path)
        self.assertEqual(store.tasks, [])
        self.assertIsNotNone(store.load_warning)
        self.assertEqual(len(list(Path(self.tmp.name).glob("data.broken-*.json"))), 1)
        store.save()
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["tasks"], [])


if __name__ == "__main__":
    unittest.main()
