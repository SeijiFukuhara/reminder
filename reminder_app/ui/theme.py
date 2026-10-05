"""色とフォントの定義。"""

import customtkinter as ctk

FONT_FAMILY = "Yu Gothic UI"

BG = "#f3f5fa"  # ウインドウの背景
CARD = "#ffffff"
CARD_DONE = "#f7f8fb"
BORDER = "#e2e6ef"
TEXT = "#2f3542"
SUB = "#8a94a6"

PRIMARY = "#5b8def"
PRIMARY_HOVER = "#4877d9"
GHOST = "#eef2fa"
GHOST_HOVER = "#dfe6f5"
DANGER = "#e5534b"
DANGER_HOVER = "#c8423b"
DANGER_LIGHT = "#fdecea"
SUCCESS = "#3aa76d"

MEMO_BG = "#fff8e6"
MEMO_BORDER = "#f3dc9b"
MEMO_TEXT_BG = "#fffdf7"
MEMO_ACCENT = "#d4900f"

# バッジの (背景色, 文字色)
BADGE_DAILY = ("#e6efff", "#3867d6")
BADGE_INFO = ("#f0f2f6", "#5f6b7a")
BADGE_OVERDUE = ("#fde8e7", "#c62828")
BADGE_DONE = ("#e5f6ec", "#2e7d4f")
BADGE_TODAY = ("#e6efff", "#3867d6")


class Fonts:
    """CTkFont はウインドウ作成後に作る必要があるので、App から生成する。"""

    def __init__(self):
        self.app_title = ctk.CTkFont(FONT_FAMILY, 20, "bold")
        self.date = ctk.CTkFont(FONT_FAMILY, 22, "bold")
        self.heading = ctk.CTkFont(FONT_FAMILY, 17, "bold")
        self.subheading = ctk.CTkFont(FONT_FAMILY, 14, "bold")
        self.body = ctk.CTkFont(FONT_FAMILY, 13)
        self.body_bold = ctk.CTkFont(FONT_FAMILY, 13, "bold")
        self.small = ctk.CTkFont(FONT_FAMILY, 11)
        self.small_bold = ctk.CTkFont(FONT_FAMILY, 11, "bold")
        self.task = ctk.CTkFont(FONT_FAMILY, 15)
        self.task_done = ctk.CTkFont(FONT_FAMILY, 15, overstrike=True)
        self.memo = ctk.CTkFont(FONT_FAMILY, 14)
        self.link = ctk.CTkFont(FONT_FAMILY, 12, underline=True)
