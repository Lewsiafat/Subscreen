"""UI App — 主應用程式，管理 Presto 硬體與頁面生命週期。"""

import uasyncio as asyncio
from presto import Presto
from ui.theme import BACKGROUND

try:
    from picovector import PicoVector, Transform, ANTIALIAS_BEST
    _HAS_VECTOR = True
except ImportError:
    _HAS_VECTOR = False

# 滑動偵測參數
_SWIPE_THRESHOLD = 50   # 最小滑動距離（px）
_SWIPE_ANIM_SPEED = 20  # 動畫速度（px/frame）


class App:
    """Subscreen 主應用程式。

    負責：
    - 初始化 Presto 硬體（display, touch）
    - 驅動 async render loop
    - 管理 Page 切換與滑動手勢導航

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

        # 頁面序列（滑動切換用）
        self._pages = []       # Page 實例列表
        self._page_index = -1  # 當前頁面索引，-1 = 不在序列中

        # 滑動偵測狀態
        self._touch_start_x = -1
        self._touch_last_x = -1
        self._touch_was_down = False

        # 滑動動畫狀態
        self._swiping = False
        self._swipe_offset = 0.0
        self._swipe_direction = 0   # +1 往右（前一頁），-1 往左（下一頁）
        self._swipe_next_page = None

    def set_pages(self, pages):
        """設定可滑動切換的頁面序列。

        Args:
            pages: Page 實例列表。
        """
        self._pages = pages
        # 將當前頁面對應到序列中的索引
        if self._current_page in self._pages:
            self._page_index = self._pages.index(
                self._current_page
            )

    def set_screen(self, page):
        """切換到指定頁面。

        Args:
            page: Page 實例。
        """
        if self._current_page:
            self._current_page.on_exit()
        self._current_page = page
        self._current_page.on_enter()
        # 同步 page_index
        if page in self._pages:
            self._page_index = self._pages.index(page)
        else:
            self._page_index = -1

    def _navigate(self, direction):
        """啟動滑動切換動畫。

        Args:
            direction: -1（往左，下一頁）或 +1（往右，前一頁）。
        """
        if self._swiping or self._page_index < 0:
            return
        target = self._page_index - direction
        if target < 0 or target >= len(self._pages):
            return

        self._swiping = True
        self._swipe_direction = direction
        self._swipe_offset = 0.0
        self._swipe_next_page = self._pages[target]

    def _update_swipe_animation(self):
        """更新滑動動畫（每幀呼叫）。"""
        self._swipe_offset += (
            self._swipe_direction * _SWIPE_ANIM_SPEED
        )
        if abs(self._swipe_offset) >= self.width:
            # 動畫完成，切換頁面
            old = self._current_page
            old.on_exit()
            self._current_page = self._swipe_next_page
            self._current_page.on_enter()
            if self._current_page in self._pages:
                self._page_index = self._pages.index(
                    self._current_page
                )
            self._swiping = False
            self._swipe_offset = 0.0
            self._swipe_next_page = None

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
        touching = self.touch.state

        if self._swiping:
            was_swiping = True
            self._update_swipe_animation()
        else:
            was_swiping = False

        if self._swiping:
            # 動畫進行中，持續追蹤觸控位置（不消費手勢）
            if touching:
                self._touch_last_x = self.touch.x
        else:
            if touching:
                if not self._touch_was_down or was_swiping:
                    # 觸控開始（或動畫剛結束時正在觸控）
                    self._touch_start_x = self.touch.x
                # 持續追蹤最新位置
                self._touch_last_x = self.touch.x
            elif self._touch_was_down and not was_swiping:
                # 觸控結束 → 用追蹤的最後位置計算距離
                dx = self._touch_last_x - self._touch_start_x
                if abs(dx) >= _SWIPE_THRESHOLD:
                    # 滑動 → 切換頁面
                    direction = 1 if dx > 0 else -1
                    self._navigate(direction)
                else:
                    # 點擊 → 傳給頁面處理
                    self._current_page.handle_touch(
                        self._touch_last_x, self.touch.y
                    )
                self._touch_start_x = -1
        self._touch_was_down = touching

        # 邏輯更新
        self._current_page.update()

        # 繪製
        if self._swiping:
            self._draw_swipe_transition()
        else:
            self._current_page.draw(
                self.display, self.vector, offset_x=0
            )

        # 推送到螢幕
        self.presto.update()

    def _draw_swipe_transition(self):
        """繪製滑動過渡動畫（兩個頁面同時顯示）。"""
        ofs = int(self._swipe_offset)
        w = self.width

        # 清除背景
        self.display.set_pen(
            self.display.create_pen(*BACKGROUND)
        )
        self.display.clear()

        # 當前頁面滑出
        self._current_page.draw(
            self.display, self.vector, offset_x=ofs
        )

        # 新頁面滑入（從反方向進入）
        if self._swipe_next_page:
            incoming_ofs = ofs - self._swipe_direction * w
            self._swipe_next_page.draw(
                self.display, self.vector,
                offset_x=incoming_ofs,
            )

    def stop(self):
        """停止主迴圈。"""
        self._running = False
