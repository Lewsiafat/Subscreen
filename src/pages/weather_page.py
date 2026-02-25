"""Weather Page — 即時天氣 + 多日預報頁面。"""

import time
import json
import uasyncio as asyncio
from config_manager import ConfigManager
from ui.page import Page
from ui.widget import Label
from ui.theme import (
    WHITE, GRAY, DARK_GRAY, PRIMARY, CYAN, YELLOW, RED,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE, FONT_XLARGE,
)

# Open-Meteo API（HTTP，避免 SSL 阻塞）
_API_HOST = "api.open-meteo.com"
_API_PATH = (
    "/v1/forecast?"
    "latitude={lat}&longitude={lon}"
    "&current=temperature_2m,relative_humidity_2m,"
    "weather_code,wind_speed_10m"
    "&daily=weather_code,temperature_2m_max,temperature_2m_min"
    "&timezone=auto&forecast_days=4"
)

# 預設經緯度（台北）
_DEFAULT_LAT = 25.033
_DEFAULT_LON = 121.565

# 刷新間隔（秒）
_FETCH_INTERVAL = 600  # 10 分鐘

# WMO Weather Code 對應
_WMO_ICONS = {
    0: ("Clear", YELLOW),
    1: ("Sunny", YELLOW),
    2: ("Cloudy", GRAY),
    3: ("Overcast", GRAY),
    45: ("Fog", GRAY),
    48: ("Fog", GRAY),
    51: ("Drizzle", CYAN),
    53: ("Drizzle", CYAN),
    55: ("Drizzle", CYAN),
    61: ("Rain", PRIMARY),
    63: ("Rain", PRIMARY),
    65: ("H.Rain", PRIMARY),
    71: ("Snow", WHITE),
    73: ("Snow", WHITE),
    75: ("H.Snow", WHITE),
    77: ("Sleet", CYAN),
    80: ("Showers", PRIMARY),
    81: ("Showers", PRIMARY),
    82: ("H.Shower", PRIMARY),
    85: ("SnowShr", WHITE),
    86: ("SnowShr", WHITE),
    95: ("Storm", RED),
    96: ("Storm", RED),
    99: ("Storm", RED),
}


def _wmo_text(code):
    """WMO weather code 轉文字描述和顏色。"""
    entry = _WMO_ICONS.get(code)
    if entry:
        return entry
    return ("???", GRAY)


async def _async_http_get(host, path, port=80):
    """非阻塞 HTTP GET，回傳 response body bytes。"""
    reader, writer = await asyncio.open_connection(
        host, port
    )
    request = (
        "GET {} HTTP/1.0\r\n"
        "Host: {}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, host)
    writer.write(request.encode())
    await writer.drain()

    # 跳過 HTTP headers
    while True:
        line = await reader.readline()
        if line == b"\r\n" or line == b"":
            break

    # 非阻塞讀取 body
    chunks = []
    while True:
        chunk = await reader.read(1024)
        if not chunk:
            break
        chunks.append(chunk)

    writer.close()
    return b"".join(chunks)


class WeatherPage(Page):
    """天氣頁面：即時天氣 + 4 日預報。

    Args:
        app: App 實例。
        lat: 緯度。
        lon: 經度。
    """

    def __init__(self, app, lat=_DEFAULT_LAT, lon=_DEFAULT_LON):
        super().__init__(app)
        self._lat = lat
        self._lon = lon
        self._data = None
        self._last_fetch = 0
        self._fetching = False
        self._error = None

        # --- 地點名稱（最頂部）---
        self._location_label = Label(
            x=0, y=2, text="",
            color=GRAY, scale=FONT_SMALL,
        )
        self.add(self._location_label)

        # --- 即時天氣 widgets（上半部）---
        self._weather_label = Label(
            x=0, y=12, text="---",
            color=YELLOW, scale=FONT_MEDIUM,
        )
        self._temp_label = Label(
            x=0, y=45, text="--.-",
            color=WHITE, scale=FONT_XLARGE,
        )
        self._unit_label = Label(
            x=0, y=50, text="C",
            color=GRAY, scale=FONT_MEDIUM,
        )
        self._humidity_label = Label(
            x=15, y=100, text="Hum: --%",
            color=CYAN, scale=FONT_SMALL,
        )
        self._wind_label = Label(
            x=130, y=100, text="Wind: -- km/h",
            color=GRAY, scale=FONT_SMALL,
        )

        self.add(self._weather_label)
        self.add(self._temp_label)
        self.add(self._unit_label)
        self.add(self._humidity_label)
        self.add(self._wind_label)

        # --- 分隔線位置 ---
        self._divider_y = 118

        # --- 4 日預報 widgets（下半部）---
        self._forecast_labels = []
        col_w = 60
        for i in range(4):
            cx = i * col_w
            day_lbl = Label(
                x=cx, y=130, text="---",
                color=GRAY, scale=FONT_SMALL,
            )
            icon_lbl = Label(
                x=cx, y=148, text="---",
                color=YELLOW, scale=FONT_SMALL,
            )
            temp_lbl = Label(
                x=cx, y=166, text="--/--",
                color=WHITE, scale=FONT_SMALL,
            )
            self.add(day_lbl)
            self.add(icon_lbl)
            self.add(temp_lbl)
            self._forecast_labels.append(
                (day_lbl, icon_lbl, temp_lbl)
            )

        # 狀態列
        self._status_label = Label(
            x=0, y=225, text="Loading...",
            color=DARK_GRAY, scale=FONT_SMALL,
        )
        self.add(self._status_label)

    def on_enter(self):
        new_lat = ConfigManager.get_setting(
            "weather_lat", self._lat
        )
        new_lon = ConfigManager.get_setting(
            "weather_lon", self._lon
        )
        if new_lat != self._lat or new_lon != self._lon:
            self._lat = new_lat
            self._lon = new_lon
            self._last_fetch = 0  # 強制重新抓取
        loc = ConfigManager.get_setting("weather_location", "")
        self._location_label.set_text(loc)
        if self._data:
            self._update_display()
        asyncio.create_task(self._fetch_weather())

    def on_exit(self):
        self._fetching = False

    def on_resume(self):
        """Settings overlay 關閉後重新讀取位置設定。"""
        new_lat = ConfigManager.get_setting(
            "weather_lat", self._lat
        )
        new_lon = ConfigManager.get_setting(
            "weather_lon", self._lon
        )
        if new_lat != self._lat or new_lon != self._lon:
            self._lat = new_lat
            self._lon = new_lon
            self._last_fetch = 0
            asyncio.create_task(self._fetch_weather())
        loc = ConfigManager.get_setting("weather_location", "")
        self._location_label.set_text(loc)
        if self._data:
            self._update_display()

    async def _fetch_weather(self):
        """非阻塞取得天氣資料。"""
        if self._fetching:
            return
        # 有快取且未過期，不重新抓取
        if (self._data
                and time.time() - self._last_fetch < _FETCH_INTERVAL):
            return
        self._fetching = True
        self._status_label.set_text("Updating...")
        self._status_label.color = GRAY

        try:
            path = _API_PATH.format(
                lat=self._lat, lon=self._lon
            )
            body = await _async_http_get(_API_HOST, path)
            self._data = json.loads(body)
            self._last_fetch = time.time()
            self._error = None
            self._update_display()
            self._status_label.set_text(
                "Updated {:02d}:{:02d}".format(
                    time.localtime()[3],
                    time.localtime()[4],
                )
            )
            self._status_label.color = DARK_GRAY
        except Exception as e:
            self._error = str(e)
            self._status_label.set_text("Err:" + self._error[:22])
            self._status_label.color = RED
        finally:
            self._fetching = False

    def _update_display(self):
        """根據 API 資料更新所有 widgets。"""
        if not self._data:
            return

        d = self.app.display
        w = self.app.width

        # --- 即時天氣 ---
        cur = self._data.get("current", {})
        temp = cur.get("temperature_2m", 0)
        humidity = cur.get("relative_humidity_2m", 0)
        wind = cur.get("wind_speed_10m", 0)
        wcode = cur.get("weather_code", -1)

        wtxt, wcolor = _wmo_text(wcode)
        self._weather_label.set_text(wtxt)
        self._weather_label.color = wcolor
        wtxt_w = d.measure_text(wtxt, FONT_MEDIUM)
        self._weather_label.x = (w - wtxt_w) // 2

        temp_str = "{:.1f}".format(temp)
        self._temp_label.set_text(temp_str)
        temp_w = d.measure_text(temp_str, FONT_XLARGE)
        unit_w = d.measure_text("C", FONT_MEDIUM)
        total_w = temp_w + 4 + unit_w
        base_x = (w - total_w) // 2
        self._temp_label.x = base_x
        self._unit_label.x = base_x + temp_w + 4

        hum_str = "Hum: {}%".format(humidity)
        self._humidity_label.set_text(hum_str)
        wind_str = "Wind: {}km/h".format(wind)
        self._wind_label.set_text(wind_str)
        hum_w = d.measure_text(hum_str, FONT_SMALL)
        wind_w = d.measure_text(wind_str, FONT_SMALL)
        self._humidity_label.x = (w // 2 - hum_w) // 2
        self._wind_label.x = w // 2 + (w // 2 - wind_w) // 2

        # --- 4 日預報 ---
        daily = self._data.get("daily", {})
        dates = daily.get("time", [])
        wcodes = daily.get("weather_code", [])
        t_maxs = daily.get("temperature_2m_max", [])
        t_mins = daily.get("temperature_2m_min", [])

        col_w = 60
        for i in range(min(4, len(dates))):
            day_lbl, icon_lbl, temp_lbl = self._forecast_labels[i]

            date_str = dates[i]
            day_name = self._date_to_weekday(date_str)
            if i == 0:
                day_name = "Today"
            day_lbl.set_text(day_name)
            day_w = d.measure_text(day_name, FONT_SMALL)
            day_lbl.x = i * col_w + (col_w - day_w) // 2

            ftxt, fcolor = _wmo_text(wcodes[i])
            icon_lbl.set_text(ftxt)
            icon_lbl.color = fcolor
            ftxt_w = d.measure_text(ftxt, FONT_SMALL)
            icon_lbl.x = i * col_w + (col_w - ftxt_w) // 2

            tstr = "{:.0f}/{:.0f}".format(
                t_maxs[i], t_mins[i]
            )
            temp_lbl.set_text(tstr)
            tstr_w = d.measure_text(tstr, FONT_SMALL)
            temp_lbl.x = i * col_w + (col_w - tstr_w) // 2

        loc_text = self._location_label.text
        if loc_text:
            lw = d.measure_text(loc_text, FONT_SMALL)
            self._location_label.x = (w - lw) // 2

        status_text = self._status_label.text
        sw = d.measure_text(status_text, FONT_SMALL)
        self._status_label.x = (w - sw) // 2

    def _date_to_weekday(self, date_str):
        """將 'YYYY-MM-DD' 轉為星期名稱。"""
        try:
            parts = date_str.split("-")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            t = time.mktime(
                (y, m, d, 0, 0, 0, 0, 0)
            )
            wday = time.localtime(t)[6]
            days = ("Mon", "Tue", "Wed", "Thu",
                    "Fri", "Sat", "Sun")
            return days[wday]
        except Exception:
            return date_str[-5:]

    def update(self):
        now = time.time()
        if (now - self._last_fetch > _FETCH_INTERVAL
                and not self._fetching):
            asyncio.create_task(self._fetch_weather())

    def draw(self, display, vector, offset_x=0):
        self._draw_background(display)

        display.set_pen(display.create_pen(*DARK_GRAY))
        display.rectangle(
            10 + offset_x, self._divider_y,
            self.app.width - 20, 1,
        )

        self._draw_widgets(display, offset_x)
