import uasyncio as asyncio
from wifi_manager import WiFiManager
from ui.app import App
from pages.splash_page import SplashPage
from pages.demo_page import DemoPage
from pages.ap_mode_page import ApModePage


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
        """WiFi 連線成功 → 等 Splash 動畫完成後跳轉 DemoPage。"""
        async def _wait_and_switch():
            splash = app._current_page
            while isinstance(splash, SplashPage) and not splash.ready:
                await asyncio.sleep_ms(100)
            app.set_screen(DemoPage(app))
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
