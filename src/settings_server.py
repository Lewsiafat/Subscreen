"""
Settings server — CONNECTED 狀態下提供網頁設定介面。
復用 WebServer，提供背光控制、重啟、重置等 API。
"""
import json
import machine
import uasyncio as asyncio
from web_server import WebServer
from config_manager import ConfigManager
from logger import Logger


class SettingsServer:
    """在 WiFi 連線狀態下提供設定用 Web API。"""

    def __init__(self, app=None):
        """
        Args:
            app: App 實例，用於控制背光等硬體。
        """
        self._log = Logger("SettingsServer")
        self._app = app
        self._web = WebServer()
        self._running = False
        self._setup_routes()

    def _setup_routes(self):
        """註冊設定相關路由。"""
        self._web.add_route("/", self._handle_page)
        self._web.add_route(
            "/api/settings", self._handle_get_settings
        )
        self._web.add_route(
            "/api/settings", self._handle_set_settings,
            method="POST"
        )
        self._web.add_route(
            "/api/backlight", self._handle_backlight,
            method="POST"
        )
        self._web.add_route(
            "/api/reboot", self._handle_reboot,
            method="POST"
        )
        self._web.add_route(
            "/api/reset-wifi", self._handle_reset_wifi,
            method="POST"
        )

    def _read_template(self):
        """讀取設定頁面 HTML。"""
        paths = [
            "templates/settings.html",
            "src/templates/settings.html",
        ]
        for path in paths:
            try:
                with open(path, "r") as f:
                    return f.read()
            except OSError:
                continue
        return "<html><body>Settings page not found</body></html>"

    def _json_response(self, data, status=200):
        """建立 JSON HTTP 回應。"""
        body = json.dumps(data)
        return (
            f"HTTP/1.1 {status} OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            f"\r\n{body}"
        ).encode()

    def _html_response(self, html):
        """建立 HTML HTTP 回應。"""
        return (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"\r\n{html}"
        ).encode()

    async def _handle_page(self, request):
        """提供設定頁面 HTML。"""
        html = self._read_template()
        return self._html_response(html)

    async def _handle_get_settings(self, request):
        """GET /api/settings — 回傳目前設定。"""
        settings = ConfigManager.load_settings()
        return self._json_response(settings)

    async def _handle_set_settings(self, request):
        """POST /api/settings — 更新設定值。"""
        params = request.get("params", {})
        if not params:
            return self._json_response(
                {"error": "No parameters"}, 400
            )
        settings = ConfigManager.load_settings()
        for key, value in params.items():
            # 嘗試轉換數值
            try:
                value = float(value)
                if value == int(value):
                    value = int(value)
            except (ValueError, TypeError):
                pass
            settings[key] = value
        ConfigManager.save_settings(settings)
        self._apply_settings(settings)
        return self._json_response({"ok": True})

    async def _handle_backlight(self, request):
        """POST /api/backlight — 切換背光。"""
        params = request.get("params", {})
        value_str = params.get("value", "")
        try:
            value = float(value_str)
            value = max(0.0, min(1.0, value))
        except (ValueError, TypeError):
            # 切換：若目前 > 0 則關閉，否則開啟
            current = ConfigManager.get_setting("backlight", 1.0)
            value = 0.0 if current > 0 else 1.0

        ConfigManager.set_setting("backlight", value)
        if self._app and hasattr(self._app, 'presto'):
            self._app.presto.set_backlight(value)
        self._log.info(f"Backlight set to {value}")
        return self._json_response(
            {"backlight": value}
        )

    async def _handle_reboot(self, request):
        """POST /api/reboot — 重啟裝置。"""
        self._log.info("Reboot requested via settings")
        asyncio.create_task(self._delayed_reboot())
        return self._json_response({"ok": True})

    async def _handle_reset_wifi(self, request):
        """POST /api/reset-wifi — 清除 WiFi 設定並重啟。"""
        self._log.info("WiFi reset requested via settings")
        ConfigManager.delete_config()
        asyncio.create_task(self._delayed_reboot())
        return self._json_response({"ok": True})

    async def _delayed_reboot(self):
        """延遲重啟，讓 HTTP 回應先送出。"""
        await asyncio.sleep(2)
        machine.reset()

    def _apply_settings(self, settings):
        """套用設定到硬體。"""
        if self._app and hasattr(self._app, 'presto'):
            bl = settings.get("backlight", 1.0)
            self._app.presto.set_backlight(bl)
            ambient = settings.get("ambient_leds", False)
            self._app.presto.auto_ambient_leds(
                bool(ambient)
            )

    async def start(self, port=80):
        """啟動設定伺服器。"""
        if not self._running:
            self._running = True
            await self._web.start(port=port)
            self._log.info(f"Settings server started on port {port}")

    def stop(self):
        """停止設定伺服器。"""
        if self._running:
            self._web.stop()
            self._running = False
            self._log.info("Settings server stopped")
