"""
Debug display dashboard for Pico Explorer 2.8" screen.

Provides real-time WiFi state machine monitoring with 4 pages
navigated via hardware buttons A/B/X/Y (GPIO 12-15).
"""
import json
import time
import uasyncio as asyncio
from machine import Pin
from picographics import PicoGraphics, DISPLAY_PICO_EXPLORER
from logger import Logger, LogLevel
from config_manager import ConfigManager, CONFIG_FILE, CONFIG_VERSION
from constants import WiFiState

# Display dimensions (Pico Explorer 2.8")
WIDTH = 240
HEIGHT = 240

# Layout constants
HEADER_H = 24
LINE_H = 18
CONTENT_Y = HEADER_H + 4
MAX_LOG_LINES = 11

# Button GPIO pins (Pico Explorer)
BTN_A = 12
BTN_B = 13
BTN_X = 14
BTN_Y = 15

# Page indices
PAGE_STATUS = 0
PAGE_CONFIG = 1
PAGE_LOG = 2
PAGE_NETWORK = 3
PAGE_COUNT = 4
PAGE_NAMES = ["Status", "Config", "Log", "Network"]


class DebugDisplay:
    """
    Debug dashboard for 2.8" PicoGraphics display.

    Shows WiFi state, config, logs, and network info across 4 pages.
    Buttons A/B navigate pages, X performs context action, Y toggles
    log level.
    """

    def __init__(self, data_provider):
        """
        Initialize the debug display.

        Args:
            data_provider: Callable returning a dict with debug data.
        """
        self._get_data = data_provider
        self._data = {}
        self._enabled = True
        self._log = Logger("DebugDisplay")

        # Display setup
        self._display = PicoGraphics(display=DISPLAY_PICO_EXPLORER)
        self._display.set_backlight(0.8)
        self._display.set_font("bitmap8")

        # Colours (RGB332 for PicoGraphics)
        self._bg = self._display.create_pen(0, 0, 0)
        self._fg = self._display.create_pen(255, 255, 255)
        self._header_bg = self._display.create_pen(40, 40, 60)
        self._green = self._display.create_pen(0, 200, 0)
        self._red = self._display.create_pen(200, 0, 0)
        self._yellow = self._display.create_pen(200, 200, 0)
        self._cyan = self._display.create_pen(0, 200, 200)
        self._dim = self._display.create_pen(120, 120, 120)
        self._blue = self._display.create_pen(80, 80, 255)

        # State colour mapping
        self._state_colours = {
            WiFiState.IDLE: self._dim,
            WiFiState.CONNECTING: self._yellow,
            WiFiState.CONNECTED: self._green,
            WiFiState.FAIL: self._red,
            WiFiState.AP_MODE: self._cyan,
        }

        # Buttons (active low with pull-up)
        self._btn_a = Pin(BTN_A, Pin.IN, Pin.PULL_UP)
        self._btn_b = Pin(BTN_B, Pin.IN, Pin.PULL_UP)
        self._btn_x = Pin(BTN_X, Pin.IN, Pin.PULL_UP)
        self._btn_y = Pin(BTN_Y, Pin.IN, Pin.PULL_UP)
        self._btn_prev = [1, 1, 1, 1]  # debounce state

        # Page state
        self._page = PAGE_STATUS
        self._show_password = False
        self._start_time = time.time()

        # Log ring buffer
        self._log_buf = []
        self._log_max = 50
        Logger.add_hook(self._log_hook)

        self._log.info("Debug display initialized")

    def _log_hook(self, level, module, msg):
        """Capture log messages into ring buffer."""
        names = ['D', 'I', 'W', 'E']
        prefix = names[level] if level < len(names) else '?'
        entry = f"[{prefix}]{module}: {msg}"
        self._log_buf.append(entry)
        if len(self._log_buf) > self._log_max:
            self._log_buf = self._log_buf[-self._log_max:]

    def enable(self):
        """Enable the display loop."""
        self._enabled = True
        self._log.info("Display enabled")

    def disable(self):
        """Disable the display loop and clear the screen."""
        self._enabled = False
        self._display.set_pen(self._bg)
        self._display.clear()
        self._display.update()
        self._log.info("Display disabled")

    def is_enabled(self) -> bool:
        """Check if the display is enabled."""
        return self._enabled

    def _read_buttons(self):
        """Read buttons with edge detection. Returns (a, b, x, y)."""
        vals = [
            self._btn_a.value(),
            self._btn_b.value(),
            self._btn_x.value(),
            self._btn_y.value(),
        ]
        pressed = [False, False, False, False]
        for i in range(4):
            # Detect falling edge (1 -> 0 = press)
            if self._btn_prev[i] == 1 and vals[i] == 0:
                pressed[i] = True
            self._btn_prev[i] = vals[i]
        return pressed

    def _handle_buttons(self):
        """Process button presses."""
        a, b, x, y = self._read_buttons()

        if a:
            self._page = (self._page - 1) % PAGE_COUNT
            self._show_password = False
        if b:
            self._page = (self._page + 1) % PAGE_COUNT
            self._show_password = False

        if x:
            self._handle_action()

        if y:
            # Toggle global log level DEBUG <-> INFO
            current = Logger.get_level()
            if current == LogLevel.DEBUG:
                Logger.set_level(LogLevel.INFO)
                self._log.info("Log level -> INFO")
            else:
                Logger.set_level(LogLevel.DEBUG)
                self._log.info("Log level -> DEBUG")

    def _handle_action(self):
        """Handle X button action based on current page."""
        if self._page == PAGE_CONFIG:
            self._show_password = not self._show_password
        elif self._page == PAGE_LOG:
            self._log_buf.clear()
            self._log.info("Log cleared")

    def _draw_header(self):
        """Draw the page header bar."""
        self._display.set_pen(self._header_bg)
        self._display.rectangle(0, 0, WIDTH, HEADER_H)

        # Page title
        self._display.set_pen(self._fg)
        title = PAGE_NAMES[self._page]
        self._display.text(title, 4, 4, scale=2)

        # Page indicator dots
        for i in range(PAGE_COUNT):
            dot_x = WIDTH - 8 - (PAGE_COUNT - 1 - i) * 12
            if i == self._page:
                self._display.set_pen(self._fg)
            else:
                self._display.set_pen(self._dim)
            self._display.circle(dot_x, HEADER_H // 2, 3)

    def _draw_label_value(self, y, label, value, value_pen=None):
        """Draw a label: value pair at given y position."""
        self._display.set_pen(self._dim)
        self._display.text(label, 4, y, scale=2)
        if value_pen:
            self._display.set_pen(value_pen)
        else:
            self._display.set_pen(self._fg)
        self._display.text(str(value), 120, y, scale=2)

    def _draw_status_page(self):
        """Draw the Status page."""
        y = CONTENT_Y
        state = self._data.get("state", 0)
        state_name = WiFiState.get_name(state)
        colour = self._state_colours.get(state, self._fg)

        self._draw_label_value(y, "State:", state_name, colour)
        y += LINE_H

        # IP address
        ip = "N/A"
        ifcfg = self._data.get("wlan_ifconfig")
        if state == WiFiState.CONNECTED and ifcfg:
            ip = ifcfg[0]
        self._draw_label_value(y, "IP:", ip)
        y += LINE_H

        # Target SSID
        ssid = self._data.get("target_ssid") or "N/A"
        self._draw_label_value(y, "SSID:", ssid)
        y += LINE_H

        # Retry count
        retry = self._data.get("retry_count", 0)
        max_r = self._data.get("max_retries", 0)
        self._draw_label_value(y, "Retries:", f"{retry}/{max_r}")
        y += LINE_H

        # Uptime
        elapsed = time.time() - self._start_time
        mins = elapsed // 60
        secs = elapsed % 60
        self._draw_label_value(y, "Uptime:", f"{int(mins)}m {int(secs)}s")
        y += LINE_H

        # WLAN status code
        wlan_status = self._data.get("wlan_status", "?")
        self._draw_label_value(
            y, "WLAN:", str(wlan_status) if wlan_status is not None else "?"
        )

    def _draw_config_page(self):
        """Draw the Config page - shows saved config file."""
        y = CONTENT_Y

        # Check file existence
        file_exists = False
        raw_data = None
        try:
            with open(CONFIG_FILE, "r") as f:
                raw_data = json.load(f)
            file_exists = True
        except Exception:
            pass

        exists_str = "Yes" if file_exists else "No"
        exists_pen = self._green if file_exists else self._red
        self._draw_label_value(y, "File:", exists_str, exists_pen)
        y += LINE_H

        if raw_data:
            version = raw_data.get("version", "?")
            self._draw_label_value(y, "Version:", str(version))
            y += LINE_H

            wifi = raw_data.get("wifi", {})
            saved_ssid = wifi.get("ssid", "N/A")
            self._draw_label_value(y, "SSID:", saved_ssid)
            y += LINE_H

            saved_pw = wifi.get("password", "")
            if self._show_password:
                pw_display = saved_pw
                pw_pen = self._yellow
            else:
                pw_len = len(saved_pw) if saved_pw else 0
                pw_display = f"{'*' * min(pw_len, 12)} ({pw_len})"
                pw_pen = self._fg
            self._draw_label_value(y, "Pass:", pw_display, pw_pen)
            y += LINE_H

            # Password length
            pw_len = len(saved_pw) if saved_pw else 0
            self._draw_label_value(y, "PW Len:", str(pw_len))
            y += LINE_H
        else:
            y += LINE_H
            self._display.set_pen(self._red)
            self._display.text("No config file", 4, y, scale=2)
            y += LINE_H

        y += 8
        # Action hint
        self._display.set_pen(self._dim)
        hint = "[X] Hide pass" if self._show_password else "[X] Show pass"
        self._display.text(hint, 4, y, scale=2)

    def _draw_log_page(self):
        """Draw the Log page - scrolling log view."""
        y = CONTENT_Y

        if not self._log_buf:
            self._display.set_pen(self._dim)
            self._display.text("No log entries", 4, y, scale=2)
        else:
            # Show most recent entries that fit
            visible = self._log_buf[-MAX_LOG_LINES:]
            for entry in visible:
                # Colour by level prefix
                if entry.startswith("[E]"):
                    self._display.set_pen(self._red)
                elif entry.startswith("[W]"):
                    self._display.set_pen(self._yellow)
                elif entry.startswith("[D]"):
                    self._display.set_pen(self._dim)
                else:
                    self._display.set_pen(self._fg)
                # Truncate to fit width (~30 chars at scale 2)
                display_text = entry[:38]
                self._display.text(display_text, 2, y, scale=2)
                y += LINE_H

        # Action hint at bottom
        self._display.set_pen(self._dim)
        self._display.text(
            "[X] Clear  [Y] Toggle level",
            4, HEIGHT - LINE_H, scale=2
        )

    def _draw_network_page(self):
        """Draw the Network page - raw network info."""
        y = CONTENT_Y

        # WLAN status code
        wlan_status = self._data.get("wlan_status")
        self._draw_label_value(
            y, "Status:",
            str(wlan_status) if wlan_status is not None else "?"
        )
        y += LINE_H

        # RSSI
        rssi = self._data.get("wlan_rssi")
        rssi_str = f"{rssi} dBm" if rssi is not None else "N/A"
        self._draw_label_value(y, "RSSI:", rssi_str)
        y += LINE_H

        # Connected?
        connected = self._data.get("wlan_connected", False)
        conn_pen = self._green if connected else self._red
        self._draw_label_value(
            y, "Linked:", "Yes" if connected else "No", conn_pen
        )
        y += LINE_H

        # ifconfig
        ifcfg = self._data.get("wlan_ifconfig")
        if ifcfg:
            self._draw_label_value(y, "IP:", ifcfg[0])
            y += LINE_H
            self._draw_label_value(y, "GW:", ifcfg[2])
            y += LINE_H
        else:
            self._draw_label_value(y, "IP:", "N/A")
            y += LINE_H

        # AP mode info
        y += 4
        self._display.set_pen(self._cyan)
        self._display.text("-- AP Mode --", 4, y, scale=2)
        y += LINE_H

        ap_active = self._data.get("ap_active", False)
        ap_pen = self._green if ap_active else self._dim
        self._draw_label_value(
            y, "Active:", "Yes" if ap_active else "No", ap_pen
        )
        y += LINE_H

        if ap_active:
            self._draw_label_value(
                y, "SSID:", self._data.get("ap_ssid", "")
            )
            y += LINE_H
            self._draw_label_value(
                y, "Pass:", self._data.get("ap_password", "")
            )
            y += LINE_H
            ap_ifcfg = self._data.get("ap_ifconfig")
            ap_ip = ap_ifcfg[0] if ap_ifcfg else self._data.get("ap_ip", "")
            self._draw_label_value(y, "IP:", ap_ip)

    def _render(self):
        """Render the current page to the display."""
        # Fetch data snapshot
        self._data = self._get_data()

        # Clear
        self._display.set_pen(self._bg)
        self._display.clear()

        # Header
        self._draw_header()

        # Page content
        if self._page == PAGE_STATUS:
            self._draw_status_page()
        elif self._page == PAGE_CONFIG:
            self._draw_config_page()
        elif self._page == PAGE_LOG:
            self._draw_log_page()
        elif self._page == PAGE_NETWORK:
            self._draw_network_page()

        # Footer - button hints
        self._display.set_pen(self._dim)
        self._display.text(
            "[A]<  [B]>  [Y]Lvl",
            4, HEIGHT - 2, scale=1
        )

        self._display.update()

    async def run(self):
        """Async main loop - update display every 200ms."""
        self._log.info("Display loop started")
        while True:
            if self._enabled:
                self._handle_buttons()
                self._render()
            await asyncio.sleep_ms(200)
