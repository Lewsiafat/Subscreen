"""UI App — 主應用程式，管理 Presto 硬體與頁面生命週期。"""

import uasyncio as asyncio
from presto import Presto
from ui.theme import BACKGROUND

try:
    from picovector import PicoVector, Transform, ANTIALIAS_BEST
    _HAS_VECTOR = True
except ImportError:
    _HAS_VECTOR = False


class App:
    """Subscreen 主應用程式。

    負責：
    - 初始化 Presto 硬體（display, touch）
    - 驅動 async render loop
    - 管理 Page 切換

    Args:
        full_res: 是否使用 480x480 解析度（預設 False = 240x240）。
        ambient_light: 是否啟用環境光感測器。
        fps: 目標幀率。
    """

    def __init__(self, full_res=False, ambient_light=True, fps=30):
        if full_res:
            self.presto = Presto(
                full_res=True, palette=True,
                ambient_light=ambient_light
            )
        else:
            self.presto = Presto(ambient_light=ambient_light)

        self.display = self.presto.display
        self.touch = self.presto.touch
        self.width, self.height = self.display.get_bounds()
        self._frame_ms = 1000 // fps

        # PicoVector（可選）
        self.vector = None
        self._transform = None
        if _HAS_VECTOR:
            self.vector = PicoVector(self.display)
            self.vector.set_antialiasing(ANTIALIAS_BEST)
            self._transform = Transform()
            self.vector.set_transform(self._transform)

        self._current_page = None
        self._running = False

    def set_screen(self, page):
        """切換到指定頁面。

        Args:
            page: Page 實例。
        """
        if self._current_page:
            self._current_page.on_exit()
        self._current_page = page
        self._current_page.on_enter()

    async def run(self, initial_page_class):
        """啟動主迴圈。

        Args:
            initial_page_class: 初始頁面的類別（會自動實例化）。
        """
        self.set_screen(initial_page_class(self))
        self._running = True

        while self._running:
            self._tick()
            await asyncio.sleep_ms(self._frame_ms)

    def _tick(self):
        """單幀更新：觸控 → 邏輯 → 繪製 → 顯示。"""
        if not self._current_page:
            return

        # 觸控處理
        self.touch.poll()
        if self.touch.state:
            self._current_page.handle_touch(
                self.touch.x, self.touch.y
            )

        # 邏輯更新
        self._current_page.update()

        # 繪製
        self._current_page.draw(
            self.display, self.vector, offset_x=0
        )

        # 推送到螢幕
        self.presto.update()

    def stop(self):
        """停止主迴圈。"""
        self._running = False
