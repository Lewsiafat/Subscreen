"""UI Widgets — 基礎 UI 元件。"""

from ui.theme import (
    TEXT_COLOR, BUTTON_BG, BUTTON_PRESSED_BG, BUTTON_TEXT,
    FONT_MEDIUM, BACKGROUND, PADDING,
)


class Widget:
    """所有 UI 元件的基類。"""

    def __init__(self, x=0, y=0, w=0, h=0, visible=True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible
        self._dirty = True

    def mark_dirty(self):
        self._dirty = True

    def draw(self, display, offset_x=0, offset_y=0):
        """繪製元件。子類必須覆寫。"""
        pass

    def handle_touch(self, tx, ty):
        """處理觸控事件。回傳 True 表示已消費。"""
        return False

    def contains(self, tx, ty):
        """判斷座標是否在元件範圍內。"""
        return (self.x <= tx < self.x + self.w and
                self.y <= ty < self.y + self.h)


class Label(Widget):
    """文字標籤。"""

    def __init__(self, x=0, y=0, text="", color=TEXT_COLOR,
                 scale=FONT_MEDIUM, wrap_width=0):
        super().__init__(x=x, y=y)
        self.text = text
        self.color = color
        self.scale = scale
        self.wrap_width = wrap_width

    def set_text(self, text):
        if self.text != text:
            self.text = text
            self.mark_dirty()

    def draw(self, display, offset_x=0, offset_y=0):
        if not self.visible:
            return
        display.set_pen(display.create_pen(*self.color))
        if self.wrap_width > 0:
            display.text(self.text, self.x + offset_x, self.y + offset_y,
                         self.wrap_width, self.scale)
        else:
            display.text(self.text, self.x + offset_x, self.y + offset_y,
                         240, self.scale)


class Button(Widget):
    """觸控按鈕，含按壓狀態視覺回饋。"""

    def __init__(self, x=0, y=0, w=80, h=40, text="",
                 bg=BUTTON_BG, bg_pressed=BUTTON_PRESSED_BG,
                 text_color=BUTTON_TEXT, scale=FONT_MEDIUM,
                 on_press=None):
        super().__init__(x=x, y=y, w=w, h=h)
        self.text = text
        self.bg = bg
        self.bg_pressed = bg_pressed
        self.text_color = text_color
        self.scale = scale
        self.on_press = on_press
        self._pressed = False
        self._touch_btn = None

    def register_touch(self, touch_button_class):
        """註冊硬體 touch.Button 實例。"""
        self._touch_btn = touch_button_class(
            self.x, self.y, self.w, self.h
        )

    def is_pressed(self):
        if self._touch_btn:
            return self._touch_btn.is_pressed()
        return self._pressed

    def draw(self, display, offset_x=0, offset_y=0):
        if not self.visible:
            return
        bg = self.bg_pressed if self.is_pressed() else self.bg
        display.set_pen(display.create_pen(*bg))
        display.rectangle(self.x + offset_x, self.y + offset_y, self.w, self.h)

        if self.text:
            display.set_pen(display.create_pen(*self.text_color))
            # 簡易置中：估算文字寬度
            char_w = 8 * self.scale
            text_w = len(self.text) * char_w
            tx = self.x + offset_x + (self.w - text_w) // 2
            ty = self.y + offset_y + (self.h - 8 * self.scale) // 2
            display.text(self.text, tx, ty, self.w, self.scale)

    def handle_touch(self, tx, ty):
        if not self.visible:
            return False
        if self.contains(tx, ty):
            self._pressed = True
            if self.on_press:
                self.on_press()
            return True
        self._pressed = False
        return False


class Container(Widget):
    """容器元件，群組化子元件。"""

    def __init__(self, x=0, y=0, w=0, h=0, bg=None,
                 padding=PADDING):
        super().__init__(x=x, y=y, w=w, h=h)
        self.bg = bg
        self.padding = padding
        self.children = []

    def add(self, widget):
        self.children.append(widget)
        return widget

    def draw(self, display, offset_x=0, offset_y=0):
        if not self.visible:
            return
        if self.bg:
            display.set_pen(display.create_pen(*self.bg))
            display.rectangle(self.x + offset_x, self.y + offset_y,
                              self.w, self.h)
        for child in self.children:
            child.draw(display, offset_x, offset_y)

    def handle_touch(self, tx, ty):
        if not self.visible:
            return False
        for child in self.children:
            if child.handle_touch(tx, ty):
                return True
        return False
