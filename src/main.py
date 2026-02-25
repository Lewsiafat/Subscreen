import uasyncio as asyncio
from wifi_manager import WiFiManager
from ui.app import App
from config_manager import ConfigManager
from pages.splash_page import SplashPage
from pages.clock_page import ClockPage
from pages.weather_page import WeatherPage
from pages.calendar_page import CalendarPage
from pages.market_page import MarketPage
from pages.ap_mode_page import ApModePage
from pages.settings_page import SettingsPage


async def main():
    """Main entry point — 啟動 WiFi 與 UI。"""
    print("--- Subscreen Initializing ---")

    # WiFi 背景管理
    wm = WiFiManager()

    # UI 應用程式
    app = App()
    app.wm = wm

    # 事件驅動頁面路由
    def on_connected(ip):
        """WiFi 連線成功 → 建立頁面序列，滑動切換。"""
        async def _wait_and_switch():
            splash = app._current_page
            while isinstance(splash, SplashPage) and not splash.ready:
                await asyncio.sleep_ms(100)
            # 讀取設定
            tz = ConfigManager.get_setting("timezone", 8)
            lat = ConfigManager.get_setting(
                "weather_lat", 25.033
            )
            lon = ConfigManager.get_setting(
                "weather_lon", 121.565
            )
            ambient = ConfigManager.get_setting(
                "ambient_leds", False
            )
            # 動態建立啟用的頁面序列
            page_ids = ConfigManager.get_setting(
                "pages", ["clock", "weather", "calendar"]
            )
            page_list = []
            for pid in page_ids:
                if pid == "clock":
                    page_list.append(ClockPage(app, tz_offset=tz))
                elif pid == "weather":
                    page_list.append(WeatherPage(app, lat=lat, lon=lon))
                elif pid == "calendar":
                    page_list.append(CalendarPage(app))
                elif pid == "market":
                    page_list.append(MarketPage(app))
            settings_page = SettingsPage(app)
            page_list.append(settings_page)
            app.presto.auto_ambient_leds(bool(ambient))
            app.set_screen(page_list[0])
            app.set_pages(page_list)
        asyncio.create_task(_wait_and_switch())

    def on_ap_mode(ssid):
        """進入 AP Mode → 等 Splash 動畫後跳轉 ApModePage。"""
        async def _wait_and_switch():
            splash = app._current_page
            while isinstance(splash, SplashPage) and not splash.ready:
                await asyncio.sleep_ms(100)
            app.set_screen(ApModePage(app))
        asyncio.create_task(_wait_and_switch())

    wm.on("connected", on_connected)
    wm.on("ap_mode_started", on_ap_mode)

    # 啟動 UI，SplashPage 作為初始畫面
    await app.run(SplashPage)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- System Stopped ---")
