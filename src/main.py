import uasyncio as asyncio
from wifi_manager import WiFiManager
from ui.app import App
from pages.splash_page import SplashPage
from pages.demo_page import DemoPage


async def main():
    """Main entry point — 啟動 WiFi 與 UI。"""
    print("--- Subscreen Initializing ---")

    # WiFi 背景管理
    wm = WiFiManager()

    # UI 應用程式
    app = App()
    app.wm = wm  # 掛載共享服務，供 Page 透過 self.app.wm 存取

    # SplashPage → WiFi 連線成功後自動跳轉 DemoPage
    await app.run(lambda a: SplashPage(a, next_page_class=DemoPage))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- System Stopped ---")
