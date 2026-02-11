"""
Provisioning handler for WiFi configuration via web interface.
Handles HTTP routes, template rendering, and form processing.
"""
import json
import uasyncio as asyncio
import machine
from config_manager import ConfigManager
from logger import Logger


class ProvisioningHandler:
    """
    Handles web-based WiFi provisioning.
    Manages routes, templates, and configuration form processing.
    """

    def __init__(self, web_server, on_config_saved=None, wlan=None):
        """
        Initialize the provisioning handler.

        Args:
            web_server: WebServer instance to register routes on.
            on_config_saved: Optional callback when config is saved successfully.
            wlan: Optional WLAN STA_IF interface for WiFi scanning.
        """
        self._log = Logger("Provisioning")
        self._web_server = web_server
        self._on_config_saved = on_config_saved
        self._wlan = wlan
        self._reboot_task = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Register routes for the provisioning web server."""
        self._web_server.add_route("/", self._handle_root_request)
        # Apple captive portal detection
        self._web_server.add_route("/hotspot-detect.html", self._handle_root_request)
        # Android captive portal detection
        self._web_server.add_route("/generate_204", self._handle_root_request)
        self._web_server.add_route("/configure", self._handle_configure, method="POST")
        self._web_server.add_route("/scan", self._handle_scan)

    def _read_template(self, name: str) -> str:
        """
        Read a template file from templates/ directory.

        Args:
            name: Template name (without .html extension).

        Returns:
            Template content or error message.
        """
        # Validate template name (alphanumeric and underscore only)
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        for char in name:
            if char not in allowed:
                self._log.warning(f"Invalid template name: {name}")
                return "Error: Invalid template name"

        paths = [f"templates/{name}.html", f"src/templates/{name}.html"]
        for path in paths:
            try:
                with open(path, "r") as f:
                    return f.read()
            except OSError:
                continue
        self._log.warning(f"Template not found: {name}")
        return f"Error: Template {name} not found"

    def _build_html_response(self, html: str, status: int = 200) -> bytes:
        """
        Build an HTTP response with HTML content.

        Args:
            html: HTML content string.
            status: HTTP status code (default 200).

        Returns:
            Encoded HTTP response.
        """
        return f"HTTP/1.1 {status} OK\r\nContent-Type: text/html\r\n\r\n{html}".encode()

    def _build_json_response(self, data, status: int = 200) -> bytes:
        """
        Build an HTTP response with JSON content.

        Args:
            data: Data to serialize as JSON.
            status: HTTP status code (default 200).

        Returns:
            Encoded HTTP response.
        """
        body = json.dumps(data)
        return (
            f"HTTP/1.1 {status} OK\r\n"
            "Content-Type: application/json\r\n"
            f"\r\n{body}"
        ).encode()

    async def _handle_scan(self, request: dict) -> bytes:
        """Scan for nearby WiFi networks and return as JSON."""
        if not self._wlan:
            return self._build_json_response(
                {"error": "Scanner not available"}, status=503
            )

        try:
            self._wlan.active(True)
            results = self._wlan.scan()
        except Exception as e:
            self._log.error(f"Scan failed: {e}")
            return self._build_json_response(
                {"error": "Scan failed"}, status=500
            )

        # Deduplicate by SSID, keeping strongest signal
        seen = {}
        for item in results:
            ssid = item[0].decode("utf-8", "ignore")
            rssi = item[3]
            security = item[4]
            if not ssid:
                continue
            if ssid not in seen or rssi > seen[ssid]["rssi"]:
                seen[ssid] = {
                    "ssid": ssid,
                    "rssi": rssi,
                    "security": security
                }

        # Sort by RSSI descending (strongest first)
        networks = sorted(
            seen.values(), key=lambda x: x["rssi"], reverse=True
        )
        return self._build_json_response(networks)

    async def _handle_root_request(self, request: dict) -> bytes:
        """Serve the main provisioning page."""
        html = self._read_template("provision")
        return self._build_html_response(html)

    async def _handle_configure(self, request: dict) -> bytes:
        """Process form submission from the provisioning page."""
        self._log.info("Received configure request")
        params = request.get("params", {})
        ssid = params.get("ssid", "").strip()
        password = params.get("password", "").strip()

        # Validate SSID (1-32 bytes, required)
        if not ssid or len(ssid) > 32:
            self._log.warning("Invalid SSID submitted")
            return b"HTTP/1.1 400 Bad Request\r\n\r\nInvalid SSID (must be 1-32 characters)"

        # Validate Password (8-63 chars for WPA2, required)
        if not password:
            self._log.warning(
                "Empty password received "
                f"(params keys: {list(params.keys())})"
            )
            return b"HTTP/1.1 400 Bad Request\r\n\r\nPassword is required"
        if len(password) < 8 or len(password) > 63:
            self._log.warning(
                f"Invalid password length: {len(password)}"
            )
            return b"HTTP/1.1 400 Bad Request\r\n\r\nInvalid password (must be 8-63 characters)"

        # Save configuration to flash
        success = ConfigManager.save_config(ssid, password)
        self._log.info(f"Config saved = {success}")
        if success:
            # Notify callback if provided
            if self._on_config_saved:
                self._on_config_saved(ssid, password)

            # Schedule a reboot to apply changes
            self._reboot_task = asyncio.create_task(self._reboot_device())
            html = self._read_template("success")
            return self._build_html_response(html)
        else:
            self._log.error("Failed to save config")
            return b"HTTP/1.1 500 Internal Server Error\r\n\r\nFailed to save configuration"

    async def _reboot_device(self) -> None:
        """Delayed reboot to allow HTTP response to be sent."""
        self._log.info("Rebooting in 3 seconds...")
        await asyncio.sleep(3)
        machine.reset()
