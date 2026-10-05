"""リマインダーアプリの起動スクリプト。 `python main.py` で起動する。"""

from reminder_app.storage import Store, default_data_path
from reminder_app.ui.app import App


def main():
    # 高DPI対応は customtkinter が行う
    store = Store.load(default_data_path())
    App(store).mainloop()


if __name__ == "__main__":
    main()
