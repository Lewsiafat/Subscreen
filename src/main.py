import uasyncio as asyncio
from wifi_manager import WiFiManager
from ui.app import App
from pages.demo_page import DemoPage


async def main():
    """Main entry point — 啟動 WiFi 與 UI。"""
    print("--- Subscreen Initializing ---")

    # WiFi 背景管理
    wm = WiFiManager()

    # UI 應用程式
    app = App()
    await app.run(DemoPage)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- System Stopped ---")
