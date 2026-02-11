"""Splash Page — 開機畫面，顯示 loading 動畫與 WiFi 連線狀態。"""

import time
from ui.page import Page
from ui.widget import Label
from ui.theme import (
    WHITE, GRAY, DARK_GRAY, PRIMARY, GREEN, YELLOW, RED, CYAN,
    FONT_SMALL, FONT_MEDIUM,
)
from constants import (
    STATE_IDLE, STATE_CONNECTING, STATE_CONNECTED,
    STATE_FAIL, STATE_AP_MODE,
)


# WiFi 狀態對應的顯示文字與顏色
_STATUS_MAP = {
    STATE_IDLE: ("Initializing...", GRAY),
    STATE_CONNECTING: ("Connecting to WiFi...", YELLOW),
    STATE_CONNECTED: ("Connected!", GREEN),
    STATE_FAIL: ("Connection failed", RED),
    STATE_AP_MODE: ("AP Mode - Setup required", CYAN),
}


class SplashPage(Page):
    """開機 Splash 畫面。

    顯示品牌名稱、進度條動畫、WiFi 連線狀態。
    連線成功後自動跳轉到下一個頁面。
    """

    # 最少顯示時間（毫秒）
    MIN_DISPLAY_MS = 3000

    def __init__(self, app, next_page_class=None):
        super().__init__(app)
        self._next_page_class = next_page_class
        self._progress = 0.0
        self._target = 0.0
        self._start_time = None
        self._wifi_connected = False

        # 品牌名稱
        self.add(Label(
            x=60, y=80, text="Subscreen",
            color=WHITE, scale=FONT_MEDIUM,
        ))

        # 副標題
        self.add(Label(
            x=68, y=110, text="Second Screen",
            color=GRAY, scale=FONT_SMALL,
        ))

        # WiFi 狀態文字
        self._status_label = self.add(Label(
            x=0, y=185, text="Initializing...",
            color=GRAY, scale=FONT_SMALL,
        ))

        # 進度條參數
        self._bar_x = 40
        self._bar_y = 150
        self._bar_w = 160
        self._bar_h = 6

    def on_enter(self):
        self._start_time = time.ticks_ms()

    def update(self):
        wm = getattr(self.app, 'wm', None)
        if not wm:
            return

        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self._start_time)
        status = wm.get_status()
        text, color = _STATUS_MAP.get(status, ("...", GRAY))

        # 更新狀態文字（置中）
        char_w = 8  # FONT_SMALL 字元寬度約 8px
        text_w = len(text) * char_w
        self._status_label.x = (self.app.width - text_w) // 2
        self._status_label.set_text(text)
        self._status_label.color = color

        # 根據狀態設定目標進度
        if status == STATE_IDLE:
            self._target = 0.15
        elif status == STATE_CONNECTING:
            self._target = 0.6
        elif status == STATE_CONNECTED:
            self._wifi_connected = True
            self._target = 1.0
        elif status == STATE_FAIL:
            self._target = 0.3
        elif status == STATE_AP_MODE:
            self._target = 0.5

        # 平滑動畫：逐步趨近目標
        diff = self._target - self._progress
        if abs(diff) > 0.005:
            self._progress += diff * 0.08

        # 跳轉條件：WiFi 已連線 + 最少顯示時間 + 進度條接近滿
        if (self._wifi_connected and
                self._next_page_class and
                elapsed >= self.MIN_DISPLAY_MS and
                self._progress > 0.95):
            self.app.set_screen(
                self._next_page_class(self.app)
            )

    def draw(self, display, vector, offset_x=0):
        self._draw_background(display)

        # 繪製 widgets（品牌名稱、副標題、狀態文字）
        self._draw_widgets(display, offset_x)

        # 繪製進度條背景
        display.set_pen(display.create_pen(*DARK_GRAY))
        display.rectangle(
            self._bar_x + offset_x, self._bar_y,
            self._bar_w, self._bar_h,
        )

        # 繪製進度條填充
        fill_w = int(self._bar_w * self._progress)
        if fill_w > 0:
            display.set_pen(display.create_pen(*PRIMARY))
            display.rectangle(
                self._bar_x + offset_x, self._bar_y,
                fill_w, self._bar_h,
            )
