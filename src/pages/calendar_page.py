"""Calendar Page — 月曆頁面。"""

import time
from ui.page import Page
from ui.theme import (
    WHITE, GRAY, DARK_GRAY, PRIMARY, CYAN,
    FONT_SMALL, FONT_MEDIUM,
)

_MONTH_NAMES = (
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
)
_WEEKDAY_ABBR = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")

# Layout constants (240x240)
_HEADER_H = 35   # Header strip height (y: 0–34)
_WEEKDAY_H = 22  # Weekday labels height (y: 35–56)
_GRID_Y = _HEADER_H + _WEEKDAY_H  # 57 — grid start y
_COL_W = 34      # Column width; 34*7 = 238 ≈ 240
_ROW_H = 30      # Row height; 30*6 = 180 (grid fills to y=237)
_TEXT_H = 8      # Approximate text height at FONT_SMALL (scale=1)


def _days_in_month(year, month):
    """返回指定月份的天數。"""
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    # February — leap year check
    if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
        return 29
    return 28


def _first_weekday(year, month):
    """返回指定月份第一天是星期幾（0=Monday, 6=Sunday）。"""
    t = time.mktime((year, month, 1, 0, 0, 0, 0, 0))
    return time.localtime(t)[6]


class CalendarPage(Page):
    """月曆頁面：顯示當月月曆，左右觸控切換月份。

    Args:
        app: App 實例。
        tz_offset: 時區偏移（小時），預設 8（UTC+8）。
    """

    def __init__(self, app, tz_offset=8):
        super().__init__(app)
        self._tz_offset = tz_offset
        t = self._get_local_time()
        self._today_year = t[0]
        self._today_month = t[1]
        self._today_day = t[2]
        self._view_year = t[0]
        self._view_month = t[1]
        self._last_day = t[2]

    def _get_local_time(self):
        """取得本地時間 tuple。"""
        return time.localtime(time.time() + self._tz_offset * 3600)

    def on_enter(self):
        """進入頁面：更新今日標記，重置顯示到當月。"""
        t = self._get_local_time()
        self._today_year = t[0]
        self._today_month = t[1]
        self._today_day = t[2]
        self._view_year = t[0]
        self._view_month = t[1]

    def update(self):
        """偵測日期跨天，更新今日標記。"""
        t = self._get_local_time()
        day = t[2]
        if day != self._last_day:
            self._last_day = day
            self._today_year = t[0]
            self._today_month = t[1]
            self._today_day = day

    def handle_touch(self, tx, ty):
        """左側觸控 → 上個月，右側觸控 → 下個月。"""
        w = self.app.width
        if tx < w // 3:
            self._view_month -= 1
            if self._view_month < 1:
                self._view_month = 12
                self._view_year -= 1
            return True
        if tx > w * 2 // 3:
            self._view_month += 1
            if self._view_month > 12:
                self._view_month = 1
                self._view_year += 1
            return True
        return False

    def draw(self, display, vector, offset_x=0):
        self._draw_background(display)
        self._draw_header(display, offset_x)
        self._draw_weekday_labels(display, offset_x)
        self._draw_grid(display, offset_x)

    def _draw_header(self, display, offset_x):
        """繪製月份 / 年份標題列。"""
        w = self.app.width

        display.set_pen(display.create_pen(*DARK_GRAY))
        display.rectangle(offset_x, 0, w, _HEADER_H)

        # < button (left touch zone)
        display.set_pen(display.create_pen(*GRAY))
        display.text("<", offset_x + 8, 10, w, FONT_MEDIUM)

        # Month + Year centred
        title = "{} {}".format(
            _MONTH_NAMES[self._view_month - 1], self._view_year
        )
        title_w = display.measure_text(title, FONT_MEDIUM)
        display.set_pen(display.create_pen(*WHITE))
        display.text(
            title,
            offset_x + (w - title_w) // 2,
            10, w, FONT_MEDIUM,
        )

        # > button (right touch zone)
        display.set_pen(display.create_pen(*GRAY))
        btn_w = display.measure_text(">", FONT_MEDIUM)
        display.text(
            ">",
            offset_x + w - btn_w - 8,
            10, w, FONT_MEDIUM,
        )

    def _draw_weekday_labels(self, display, offset_x):
        """繪製星期標題列（Sa / Su 以青色區分）。"""
        w = self.app.width

        display.set_pen(display.create_pen(*DARK_GRAY))
        display.rectangle(offset_x, _HEADER_H, w, _WEEKDAY_H)

        label_y = _HEADER_H + (_WEEKDAY_H - _TEXT_H) // 2
        for i, abbr in enumerate(_WEEKDAY_ABBR):
            col_center = offset_x + i * _COL_W + _COL_W // 2
            tw = display.measure_text(abbr, FONT_SMALL)
            color = CYAN if i >= 5 else GRAY
            display.set_pen(display.create_pen(*color))
            display.text(
                abbr, col_center - tw // 2,
                label_y, w, FONT_SMALL,
            )

    def _draw_grid(self, display, offset_x):
        """繪製月曆格和日期數字。"""
        w = self.app.width
        year = self._view_year
        month = self._view_month

        first_wd = _first_weekday(year, month)
        num_days = _days_in_month(year, month)
        is_current = (
            year == self._today_year
            and month == self._today_month
        )

        col = first_wd
        row = 0
        for day in range(1, num_days + 1):
            cell_x = offset_x + col * _COL_W
            cell_y = _GRID_Y + row * _ROW_H
            is_today = is_current and day == self._today_day
            is_weekend = col >= 5

            # Today highlight — filled rect
            if is_today:
                display.set_pen(display.create_pen(*PRIMARY))
                display.rectangle(
                    cell_x + 2, cell_y + 2,
                    _COL_W - 4, _ROW_H - 4,
                )

            # Day number — centred in cell
            day_str = str(day)
            tw = display.measure_text(day_str, FONT_SMALL)
            tx = cell_x + (_COL_W - tw) // 2
            ty = cell_y + (_ROW_H - _TEXT_H) // 2
            color = WHITE if (is_today or not is_weekend) else CYAN
            display.set_pen(display.create_pen(*color))
            display.text(day_str, tx, ty, w, FONT_SMALL)

            col += 1
            if col >= 7:
                col = 0
                row += 1
