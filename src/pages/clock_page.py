"""Clock Page — 時鐘頁面，支援數位與類比顯示模式。"""

import math
import time
import ntptime
import uasyncio as asyncio
from ui.page import Page
from ui.widget import Label
from ui.theme import (
    WHITE, GRAY, DARK_GRAY, PRIMARY, BACKGROUND,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE, FONT_XLARGE,
)

# 顯示模式
MODE_DIGITAL = 0
MODE_ANALOG = 1

# 星期名稱
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# 類比時鐘參數
_CENTER_X = 120
_CENTER_Y = 120
_FACE_RADIUS = 105
_HOUR_MARK_OUTER = 100
_HOUR_MARK_INNER = 88
_MIN_MARK_OUTER = 100
_MIN_MARK_INNER = 94
_HOUR_HAND_LEN = 55
_MIN_HAND_LEN = 78
_SEC_HAND_LEN = 88

# 指針寬度（半寬）
_HOUR_HAND_W = 4
_MIN_HAND_W = 3
_SEC_HAND_W = 1


class ClockPage(Page):
    """時鐘頁面，點擊螢幕切換數位/類比模式。

    Args:
        app: App 實例。
        tz_offset: 時區偏移（小時），預設 8（UTC+8）。
    """

    def __init__(self, app, tz_offset=8):
        super().__init__(app)
        self._mode = MODE_DIGITAL
        self._tz_offset = tz_offset
        self._ntp_synced = False
        self._last_sec = -1

        # 滑動動畫
        self._animating = False
        self._anim_offset = 0.0
        self._anim_target = 0.0
        self._anim_direction = 0  # +1 右滑出, -1 左滑出
        self._next_mode = None

        # 觸控防抖
        self._touch_cooldown = 0

        # 螢幕保護漂移
        self._drift_x = 0.0
        self._drift_y = 0.0
        self._drift_vx = 0.7   # px/frame
        self._drift_vy = 0.5

        # 預計算三角函數表（60 格，每格 6 度）
        self._sin_table = []
        self._cos_table = []
        for i in range(60):
            angle = math.radians(i * 6 - 90)
            self._sin_table.append(math.sin(angle))
            self._cos_table.append(math.cos(angle))

        # Digital 模式的 widgets
        # HH:MM 用 scale 5，:SS 用 scale 3 緊貼右側
        self._time_scale = 5
        self._sec_scale = FONT_LARGE
        self._time_label = Label(
            x=0, y=75, text="--:--",
            color=WHITE, scale=self._time_scale,
        )
        self._sec_label = Label(
            x=0, y=80, text="",
            color=GRAY, scale=self._sec_scale,
        )
        self._date_label = Label(
            x=0, y=130, text="",
            color=GRAY, scale=FONT_LARGE,
        )
        self._weekday_label = Label(
            x=0, y=165, text="",
            color=PRIMARY, scale=FONT_MEDIUM,
        )
        self.add(self._time_label)
        self.add(self._sec_label)
        self.add(self._date_label)
        self.add(self._weekday_label)

        # 測量實際字元寬度（在 on_enter 時校準）
        self._char_w = 8  # 預設，on_enter 會更新

        # 預建 Polygon 快取（類比模式用）
        self._hand_polygons = {}
        self._build_hand_polygons()

    def _build_hand_polygons(self):
        """預建指針 Polygon 物件。"""
        try:
            from picovector import Polygon
            # 時針：寬短矩形
            h = Polygon()
            h.path(
                (-_HOUR_HAND_W, 8),
                (_HOUR_HAND_W, 8),
                (_HOUR_HAND_W, -_HOUR_HAND_LEN),
                (0, -_HOUR_HAND_LEN - 4),
                (-_HOUR_HAND_W, -_HOUR_HAND_LEN),
            )
            self._hand_polygons['hour'] = h

            # 分針
            m = Polygon()
            m.path(
                (-_MIN_HAND_W, 8),
                (_MIN_HAND_W, 8),
                (_MIN_HAND_W, -_MIN_HAND_LEN),
                (0, -_MIN_HAND_LEN - 3),
                (-_MIN_HAND_W, -_MIN_HAND_LEN),
            )
            self._hand_polygons['min'] = m

            # 秒針：細長
            s = Polygon()
            s.path(
                (-_SEC_HAND_W, 15),
                (_SEC_HAND_W, 15),
                (_SEC_HAND_W, -_SEC_HAND_LEN),
                (-_SEC_HAND_W, -_SEC_HAND_LEN),
            )
            self._hand_polygons['sec'] = s

            # 中心圓點
            c = Polygon()
            c.circle(0, 0, 5)
            self._hand_polygons['center'] = c
        except ImportError:
            pass

    def on_enter(self):
        asyncio.create_task(self._sync_ntp())

    async def _sync_ntp(self):
        """背景同步 NTP 時間。"""
        try:
            ntptime.settime()
            self._ntp_synced = True
        except Exception:
            # NTP 失敗就用系統時間
            pass

    def _get_local_time(self):
        """取得本地時間 tuple。"""
        utc = time.time()
        local = utc + self._tz_offset * 3600
        return time.localtime(local)

    def update(self):
        # 觸控冷卻（每幀遞減）
        if self._touch_cooldown > 0:
            self._touch_cooldown -= 1

        if self._animating:
            self._update_animation()
            return

        # 螢幕保護漂移（每幀更新）
        if self._mode == MODE_DIGITAL:
            self._update_drift()

        t = self._get_local_time()
        sec = t[5]

        if sec == self._last_sec:
            return
        self._last_sec = sec

        if self._mode == MODE_DIGITAL:
            self._update_digital_text(t)

    def _update_drift(self):
        """更新螢幕保護漂移位置（每幀呼叫）。"""
        d = self.app.display
        w = self.app.width
        h = self.app.height
        time_text = self._time_label.text or "--:--"
        sec_text = self._sec_label.text or ":00"
        total_w = (d.measure_text(time_text, self._time_scale) +
                   d.measure_text(sec_text, self._sec_scale))
        block_h = 100

        max_dx = max((w - total_w) // 2, 5)
        max_dy = max((h - block_h) // 2, 5)

        self._drift_x += self._drift_vx
        self._drift_y += self._drift_vy
        if self._drift_x > max_dx or self._drift_x < -max_dx:
            self._drift_vx = -self._drift_vx
            self._drift_x += self._drift_vx
        if self._drift_y > max_dy or self._drift_y < -max_dy:
            self._drift_vy = -self._drift_vy
            self._drift_y += self._drift_vy

        self._apply_drift_positions()

    def _apply_drift_positions(self):
        """根據漂移偏移量套用 widget 位置。"""
        d = self.app.display
        w = self.app.width
        dx = int(self._drift_x)
        dy = int(self._drift_y)

        time_text = self._time_label.text or "--:--"
        time_w = d.measure_text(time_text, self._time_scale)
        sec_text = self._sec_label.text or ":00"
        sec_w = d.measure_text(sec_text, self._sec_scale)

        # 整組寬度 = HH:MM + :SS
        total_w = time_w + sec_w
        base_x = (w - total_w) // 2 + dx
        base_y = 65 + dy

        self._time_label.x = base_x
        self._time_label.y = base_y

        # 秒數緊貼時間右側，底部對齊
        self._sec_label.x = base_x + time_w
        self._sec_label.y = base_y + (8 * self._time_scale -
                                       8 * self._sec_scale)

        date_text = self._date_label.text or "0000/00/00"
        date_w = d.measure_text(date_text, FONT_LARGE)
        self._date_label.x = (w - date_w) // 2 + dx
        self._date_label.y = base_y + 55

        wday_text = self._weekday_label.text or "Mon"
        wday_w = d.measure_text(wday_text, FONT_MEDIUM)
        self._weekday_label.x = (w - wday_w) // 2 + dx
        self._weekday_label.y = base_y + 85

    def _update_digital_text(self, t):
        """更新數位時鐘文字（每秒呼叫）。"""
        hour, minute, sec = t[3], t[4], t[5]
        year, month, day = t[0], t[1], t[2]
        wday = t[6]  # 0=Monday

        self._time_label.set_text(
            "{:02d}:{:02d}".format(hour, minute))
        self._sec_label.set_text(
            ":{:02d}".format(sec))
        self._date_label.set_text(
            "{:04d}/{:02d}/{:02d}".format(year, month, day))
        self._weekday_label.set_text(_WEEKDAYS[wday])

    def _update_animation(self):
        """更新滑動過渡動畫（線性）。"""
        step = self._anim_direction * 20  # 每幀 20px
        self._anim_offset += step

        if abs(self._anim_offset) >= self.app.width:
            # 動畫完成
            self._animating = False
            self._mode = self._next_mode
            self._anim_offset = 0.0
            self._last_sec = -1  # 強制刷新
            # 切換 widget 可見性
            digital_visible = (self._mode == MODE_DIGITAL)
            self._time_label.visible = digital_visible
            self._sec_label.visible = digital_visible
            self._date_label.visible = digital_visible
            self._weekday_label.visible = digital_visible

    def draw(self, display, vector, offset_x=0):
        self._draw_background(display)

        if self._animating:
            self._draw_animated(display, vector, offset_x)
        elif self._mode == MODE_DIGITAL:
            self._draw_widgets(display, offset_x)
        else:
            self._draw_analog(display, vector, offset_x)

    def _draw_animated(self, display, vector, offset_x):
        """繪製滑動過渡動畫。"""
        ofs = int(self._anim_offset)
        w = self.app.width

        # 當前模式滑出
        if self._mode == MODE_DIGITAL:
            self._draw_widgets(display, offset_x + ofs)
        else:
            self._draw_analog(display, vector, offset_x + ofs)

        # 新模式滑入
        incoming_ofs = ofs - self._anim_direction * w
        if self._next_mode == MODE_DIGITAL:
            # 暫時顯示 digital widgets
            self._time_label.visible = True
            self._sec_label.visible = True
            self._date_label.visible = True
            self._weekday_label.visible = True
            t = self._get_local_time()
            self._update_digital_text(t)
            self._apply_drift_positions()
            self._draw_widgets(display, offset_x + incoming_ofs)
        else:
            self._draw_analog(
                display, vector, offset_x + incoming_ofs
            )

    def _draw_analog(self, display, vector, offset_x=0):
        """繪製類比時鐘。"""
        cx = _CENTER_X + offset_x
        cy = _CENTER_Y
        t = self._get_local_time()
        hour, minute, sec = t[3] % 12, t[4], t[5]

        # 錶面外圈
        self._draw_circle_outline(display, cx, cy,
                                  _FACE_RADIUS, DARK_GRAY)

        # 刻度
        self._draw_tick_marks(display, cx, cy)

        # 數字 12, 3, 6, 9
        self._draw_hour_numbers(display, cx, cy)

        # 中央日期
        month, day = t[1], t[2]
        wday = t[6]
        date_str = "{:02d}/{:02d}".format(month, day)
        wday_str = _WEEKDAYS[wday]
        display.set_pen(display.create_pen(*GRAY))
        date_w = display.measure_text(date_str, FONT_SMALL)
        display.text(date_str, cx - date_w // 2,
                     cy + 25, 240, FONT_SMALL)
        wday_w = display.measure_text(wday_str, FONT_SMALL)
        display.text(wday_str, cx - wday_w // 2,
                     cy + 38, 240, FONT_SMALL)

        if vector and self._hand_polygons:
            self._draw_hands_vector(
                display, vector, cx, cy, hour, minute, sec
            )
        else:
            self._draw_hands_lines(
                display, cx, cy, hour, minute, sec
            )

        # 中心點
        display.set_pen(display.create_pen(*WHITE))
        self._fill_circle(display, cx, cy, 4)

    def _draw_circle_outline(self, display, cx, cy, r, color):
        """用點陣繪製圓形外框。"""
        display.set_pen(display.create_pen(*color))
        steps = 60
        for i in range(steps):
            x = cx + int(r * self._cos_table[i])
            y = cy + int(r * self._sin_table[i])
            display.pixel(x, y)
            # 加粗
            display.pixel(x + 1, y)
            display.pixel(x, y + 1)

    def _fill_circle(self, display, cx, cy, r):
        """填充小圓形。"""
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            display.rectangle(cx - dx, cy + dy, dx * 2, 1)

    def _draw_tick_marks(self, display, cx, cy):
        """繪製刻度線。"""
        for i in range(60):
            cos_v = self._cos_table[i]
            sin_v = self._sin_table[i]

            if i % 5 == 0:
                # 時刻度（粗）
                display.set_pen(display.create_pen(*WHITE))
                x1 = cx + int(_HOUR_MARK_INNER * cos_v)
                y1 = cy + int(_HOUR_MARK_INNER * sin_v)
                x2 = cx + int(_HOUR_MARK_OUTER * cos_v)
                y2 = cy + int(_HOUR_MARK_OUTER * sin_v)
                self._draw_thick_line(display, x1, y1, x2, y2, 2)
            else:
                # 分刻度（細）
                display.set_pen(display.create_pen(*GRAY))
                x1 = cx + int(_MIN_MARK_INNER * cos_v)
                y1 = cy + int(_MIN_MARK_INNER * sin_v)
                x2 = cx + int(_MIN_MARK_OUTER * cos_v)
                y2 = cy + int(_MIN_MARK_OUTER * sin_v)
                display.line(x1, y1, x2, y2)

    def _draw_hour_numbers(self, display, cx, cy):
        """繪製 12, 3, 6, 9 數字。"""
        display.set_pen(display.create_pen(*WHITE))
        num_r = 75
        nums = [(12, 0), (3, 15), (6, 30), (9, 45)]
        for num, idx in nums:
            x = cx + int(num_r * self._cos_table[idx])
            y = cy + int(num_r * self._sin_table[idx])
            text = str(num)
            # 置中偏移
            tx = x - len(text) * 4
            ty = y - 4
            display.text(text, tx, ty, 240, FONT_SMALL)

    def _draw_hands_vector(self, display, vector, cx, cy,
                           hour, minute, sec):
        """使用 PicoVector 繪製指針。"""
        transform = self.app._transform

        # 時針角度：每小時 30 度 + 每分鐘 0.5 度
        hour_angle = hour * 30 + minute * 0.5

        # 分針角度：每分鐘 6 度
        min_angle = minute * 6

        # 秒針角度：每秒 6 度（逐秒跳動）
        sec_angle = sec * 6

        # 時針
        display.set_pen(display.create_pen(*WHITE))
        transform.reset()
        transform.translate(cx, cy)
        transform.rotate(hour_angle, (0, 0))
        vector.draw(self._hand_polygons['hour'])

        # 分針
        display.set_pen(display.create_pen(*WHITE))
        transform.reset()
        transform.translate(cx, cy)
        transform.rotate(min_angle, (0, 0))
        vector.draw(self._hand_polygons['min'])

        # 秒針
        display.set_pen(display.create_pen(255, 60, 60))
        transform.reset()
        transform.translate(cx, cy)
        transform.rotate(sec_angle, (0, 0))
        vector.draw(self._hand_polygons['sec'])

        # 中心圓
        display.set_pen(display.create_pen(*WHITE))
        transform.reset()
        transform.translate(cx, cy)
        vector.draw(self._hand_polygons['center'])

    def _draw_hands_lines(self, display, cx, cy,
                          hour, minute, sec):
        """使用基礎 line API 繪製指針（fallback）。"""
        # 時針
        hour_idx = ((hour % 12) * 5 + minute // 12) % 60
        display.set_pen(display.create_pen(*WHITE))
        hx = cx + int(_HOUR_HAND_LEN * self._cos_table[hour_idx])
        hy = cy + int(_HOUR_HAND_LEN * self._sin_table[hour_idx])
        self._draw_thick_line(display, cx, cy, hx, hy, 3)

        # 分針
        display.set_pen(display.create_pen(*WHITE))
        mx = cx + int(_MIN_HAND_LEN * self._cos_table[minute])
        my = cy + int(_MIN_HAND_LEN * self._sin_table[minute])
        self._draw_thick_line(display, cx, cy, mx, my, 2)

        # 秒針
        display.set_pen(display.create_pen(255, 60, 60))
        sx = cx + int(_SEC_HAND_LEN * self._cos_table[sec])
        sy = cy + int(_SEC_HAND_LEN * self._sin_table[sec])
        display.line(cx, cy, sx, sy)

    def _draw_thick_line(self, display, x1, y1, x2, y2,
                         thickness):
        """繪製粗線。"""
        for d in range(-(thickness // 2), thickness // 2 + 1):
            display.line(x1 + d, y1, x2 + d, y2)
            display.line(x1, y1 + d, x2, y2 + d)

    def handle_touch(self, tx, ty):
        """點擊螢幕切換模式。"""
        if self._animating or self._touch_cooldown > 0:
            return False

        self._touch_cooldown = 10  # ~300ms 冷卻

        # 啟動滑動動畫
        w = self.app.width
        if self._mode == MODE_DIGITAL:
            self._next_mode = MODE_ANALOG
            self._anim_direction = -1  # 向左滑出
        else:
            self._next_mode = MODE_DIGITAL
            self._anim_direction = 1   # 向右滑出

        self._anim_offset = 0.0
        self._anim_target = self._anim_direction * w
        self._animating = True
        return True
