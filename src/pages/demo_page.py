"""Demo Page — Hello World 示範頁面。"""

from ui.page import Page
from ui.widget import Label, Button, Container
from ui.theme import (
    WHITE, PRIMARY, YELLOW, DARK_GRAY,
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL,
)


class DemoPage(Page):
    """Hello World 示範頁面。

    展示基本的 Label、Button、Container 元件用法。
    """

    def __init__(self, app):
        super().__init__(app)
        self._count = 0

        # 標題
        self.add(Label(
            x=40, y=30,
            text="Hello World!",
            color=WHITE,
            scale=FONT_LARGE,
        ))

        # 副標題
        self.add(Label(
            x=50, y=70,
            text="Subscreen UI",
            color=PRIMARY,
            scale=FONT_MEDIUM,
        ))

        # 計數器標籤
        self._counter_label = self.add(Label(
            x=70, y=130,
            text="Count: 0",
            color=YELLOW,
            scale=FONT_MEDIUM,
        ))

        # 按鈕
        self.add(Button(
            x=70, y=170, w=100, h=40,
            text="Click!",
            on_press=self._on_click,
        ))

        # 底部資訊容器
        info = Container(
            x=0, y=215, w=240, h=25,
            bg=DARK_GRAY,
        )
        info.add(Label(
            x=60, y=220,
            text="240x240 Touch",
            color=WHITE,
            scale=FONT_SMALL,
        ))
        self.add(info)

    def _on_click(self):
        self._count += 1
        self._counter_label.set_text(f"Count: {self._count}")
