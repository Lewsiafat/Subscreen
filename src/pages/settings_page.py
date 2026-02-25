"""Settings Page — 顯示 QR Code 讓使用者掃描進入網頁設定介面。"""

import uasyncio as asyncio
from ui.page import Page
from ui.widget import Label
from ui.theme import (
    WHITE, GRAY, CYAN, FONT_SMALL, FONT_MEDIUM,
)
from settings_server import SettingsServer
from uQR import QRCode


class SettingsPage(Page):
    """設定頁面 — 顯示 QR Code + IP，引導掃描進入網頁設定。"""

    def __init__(self, app):
        super().__init__(app)
        self._server = None
        self._ip = "0.0.0.0"
        self._qr_matrix = None

        # 取得 IP
        wm = getattr(app, 'wm', None)
        if wm and wm.is_connected():
            config = wm.get_config()
            if config:
                self._ip = config[0]

        # 標題
        self.add(Label(
            x=60, y=8, text="Settings",
            color=CYAN, scale=FONT_MEDIUM,
        ))

        # 說明
        self.add(Label(
            x=30, y=32, text="Scan to configure",
            color=GRAY, scale=FONT_SMALL,
        ))

        # IP 位址
        self.add(Label(
            x=20, y=210, text=f"http://{self._ip}",
            color=WHITE, scale=FONT_SMALL,
        ))

        # 產生 QR Code
        url = f"http://{self._ip}"
        try:
            qr = QRCode()
            qr.add_data(url)
            self._qr_matrix = qr.get_matrix()
        except Exception:
            self._qr_matrix = None

    def on_enter(self):
        """啟動設定伺服器。"""
        self._server = SettingsServer(app=self.app)
        asyncio.create_task(self._server.start())

    def on_exit(self):
        """停止設定伺服器。"""
        if self._server:
            self._server.stop()
            self._server = None

    def draw(self, display, vector, offset_x=0, offset_y=0):
        """繪製頁面，包含 QR Code。"""
        super().draw(display, vector, offset_x, offset_y)
        if self._qr_matrix:
            self._draw_qr(display, offset_x, offset_y)

    def _draw_qr(self, display, offset_x, offset_y=0):
        """繪製 QR Code 點陣圖。"""
        qr = self._qr_matrix
        qr_size = len(qr)
        # 在螢幕中央繪製
        pixel_size = min(140 // qr_size, 5)
        total_px = qr_size * pixel_size
        start_x = (240 - total_px) // 2 + offset_x
        start_y = 50 + (150 - total_px) // 2 + offset_y

        # 白色背景
        white_pen = display.create_pen(255, 255, 255)
        display.set_pen(white_pen)
        display.rectangle(
            start_x, start_y, total_px, total_px
        )

        # 黑色模組
        black_pen = display.create_pen(0, 0, 0)
        display.set_pen(black_pen)
        for r in range(qr_size):
            for c in range(qr_size):
                if qr[r][c]:
                    px = start_x + c * pixel_size
                    py = start_y + r * pixel_size
                    display.rectangle(
                        px, py, pixel_size, pixel_size
                    )
