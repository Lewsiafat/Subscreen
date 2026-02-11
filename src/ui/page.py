"""UI Page — 頁面基類。"""

from ui.theme import BACKGROUND


class Page:
    """所有頁面的基類。

    子類應覆寫 draw() 和 update() 方法。
    可透過 add() 加入 Widget，由基類統一管理繪製與觸控。
    """

    def __init__(self, app):
        self.app = app
        self.widgets = []
        self.bg = BACKGROUND

    def add(self, widget):
        """加入 Widget 到頁面。"""
        self.widgets.append(widget)
        return widget

    def update(self):
        """邏輯更新。子類覆寫以處理資料抓取等。"""
        pass

    def draw(self, display, vector, offset_x=0):
        """繪製頁面。

        預設行為：清除背景 + 繪製所有 widgets。
        子類可覆寫以加入自訂繪製邏輯。

        Args:
            display: PicoGraphics 實例。
            vector: PicoVector 實例（可為 None）。
            offset_x: 水平偏移，用於滑動換頁效果。
        """
        self._draw_background(display)
        self._draw_widgets(display, offset_x)

    def _draw_background(self, display):
        display.set_pen(display.create_pen(*self.bg))
        display.clear()

    def _draw_widgets(self, display, offset_x=0):
        for widget in self.widgets:
            widget.draw(display, offset_x)

    def handle_touch(self, tx, ty):
        """分發觸控事件給 widgets。"""
        for widget in self.widgets:
            if widget.handle_touch(tx, ty):
                return True
        return False

    def on_enter(self):
        """頁面進入時呼叫。"""
        pass

    def on_exit(self):
        """頁面離開時呼叫。"""
        pass
