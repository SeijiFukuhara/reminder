"""リマインダーアプリの起動スクリプト。 `python main.py` で起動する。"""

import sys

from reminder_app.storage import Store, default_data_path
from reminder_app.ui.app import App


def enable_high_dpi():
    """Windowsの高DPI環境で文字がぼやけないようにする。"""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main():
    enable_high_dpi()
    store = Store.load(default_data_path())
    App(store).mainloop()


if __name__ == "__main__":
    main()
