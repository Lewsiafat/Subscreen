"""
Core WiFi management system with state machine.
Handles connection lifecycles, retries, and web-based provisioning.
"""
import network
import uasyncio as asyncio
import time
from config_manager import ConfigManager
from dns_server import DNSServer
from web_server import WebServer
from provisioning import ProvisioningHandler
from constants import (
    WiFiState,
    STATE_IDLE, STATE_CONNECTING, STATE_CONNECTED, STATE_FAIL, STATE_AP_MODE
)
from config import WiFiConfig
from logger import Logger

# AP activation timeout (in 100ms ticks)
AP_ACTIVATION_TIMEOUT = 50  # 5 seconds


class WiFiManager:
    """
    Core WiFi management system.
    Handles connection lifecycles, retries, and web-based provisioning.
    """

    def __init__(
        self,
        dns_server: DNSServer = None,
        web_server: WebServer = None,
        config: WiFiConfig = None,
        max_retries: int = None,
        connect_timeout: int = None,
        retry_delay: int = None,
        fail_recovery_delay: int = None,
        health_check_interval: int = None,
        ap_ssid: str = None,
        ap_password: str = None,
        ap_ip: str = None
    ):
        """
        Initialize the WiFi manager.

        Args:
            dns_server: Optional DNSServer instance (created if None).
            web_server: Optional WebServer instance (created if None).
            config: Optional WiFiConfig instance for all settings.
            max_retries: Override max connection retries (default 5).
            connect_timeout: Override connection timeout in seconds (default 15).
            retry_delay: Override delay between retries in seconds (default 2).
            fail_recovery_delay: Override recovery delay in seconds (default 30).
            health_check_interval: Override health check interval (default 2).
            ap_ssid: Override AP mode SSID (default "Picore-W-Setup").
            ap_password: Override AP mode password.
            ap_ip: Override AP mode IP address (default "192.168.4.1").
        """
        self._log = Logger("WiFiManager")

        # Build configuration: passed config instance or create from parameters
        if config is not None:
            self._config = config
        else:
            self._config = WiFiConfig(
                max_retries=max_retries,
                connect_timeout=connect_timeout,
                retry_delay=retry_delay,
                fail_recovery_delay=fail_recovery_delay,
                health_check_interval=health_check_interval,
                ap_ssid=ap_ssid,
                ap_password=ap_password,
                ap_ip=ap_ip
            )

        # Station interface for connecting to existing networks
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

        # Access Point interface for provisioning mode
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(False)

        # Network services (dependency injection)
        self.dns_server = dns_server if dns_server else DNSServer(self._config.ap_ip)
        self.web_server = web_server if web_server else WebServer()

        # Provisioning handler
        self._provisioning = ProvisioningHandler(self.web_server, wlan=self.wlan)

        # Internal state
        self._state = STATE_IDLE
        self._target_ssid = None
        self._target_password = None
        self._retry_count = 0

        # Event listeners: event_name -> list of callbacks
        self._listeners = {
            'connected': [],
            'disconnected': [],
            'state_change': [],
            'ap_mode_started': [],
            'connection_failed': []
        }

        # Keep reference to background task to prevent GC
        self._state_machine_task = asyncio.create_task(self._run_state_machine())

    def _set_state(self, new_state: int) -> None:
        """
        Set the state machine state with logging and event emission.

        Args:
            new_state: The new state constant.
        """
        if self._state != new_state:
            old_state = self._state
            old_name = WiFiState.get_name(old_state)
            new_name = WiFiState.get_name(new_state)
            self._log.info(f"State: {old_name} -> {new_name}")
            self._state = new_state

            # Emit state_change event
            self._emit('state_change', old_state, new_state)

            # Emit specific state events
            if new_state == STATE_CONNECTED:
                ip = self.wlan.ifconfig()[0]
                self._emit('connected', ip)
            elif old_state == STATE_CONNECTED and new_state != STATE_CONNECTED:
                self._emit('disconnected')
            elif new_state == STATE_AP_MODE:
                self._emit('ap_mode_started', self._config.ap_ssid)
            elif new_state == STATE_FAIL:
                self._emit('connection_failed', self._retry_count)

    async def _run_state_machine(self) -> None:
        """Main asynchronous loop for WiFi state transitions."""
        self._log.info("State machine started")
        self._load_and_connect()
        while True:
            try:
                if self._state == STATE_IDLE:
                    await self._handle_idle()
                elif self._state == STATE_CONNECTING:
                    await self._handle_connecting()
                elif self._state == STATE_CONNECTED:
                    await self._handle_connected()
                elif self._state == STATE_FAIL:
                    await self._handle_fail()
                elif self._state == STATE_AP_MODE:
                    await self._handle_ap_mode()
            except Exception as e:
                self._log.error(f"State machine error: {e}")
                await asyncio.sleep(5)
            await asyncio.sleep(0.1)

    def _load_and_connect(self) -> None:
        """Attempt to load credentials and start connection sequence."""
        ssid, password = ConfigManager.get_wifi_credentials()
        if ssid:
            self._log.info(f"Found config for '{ssid}'")
            self.connect(ssid, password)
        else:
            self._log.info("No config found, entering AP mode")
            self._set_state(STATE_AP_MODE)

    async def _handle_idle(self) -> None:
        """
        Handle IDLE state - waiting for explicit connect() call.
        This state is entered after disconnect() is called.
        """
        await asyncio.sleep(1)

    async def _handle_connecting(self) -> None:
        """Manage connection attempts and retries."""
        self._stop_ap_services()

        self._log.info(f"Connecting to '{self._target_ssid}' (attempt {self._retry_count + 1}/{self._config.max_retries})")
        self.wlan.connect(self._target_ssid, self._target_password)

        start_time = time.time()
        while (time.time() - start_time) < self._config.connect_timeout:
            if self.wlan.isconnected():
                ip = self.wlan.ifconfig()[0]
                self._log.info(f"Connected! IP: {ip}")
                self._set_state(STATE_CONNECTED)
                self._retry_count = 0
                return

            status = self.wlan.status()
            # Stop early if explicit failure is detected
            if status == network.STAT_CONNECT_FAIL or status == network.STAT_NO_AP_FOUND or status == network.STAT_WRONG_PASSWORD:
                self._log.debug(f"Connection failed with status {status}")
                break
            await asyncio.sleep(0.5)

        self._retry_count += 1
        if self._retry_count >= self._config.max_retries:
            self._log.warning("Max retries reached")
            self._set_state(STATE_FAIL)
        else:
            self.wlan.disconnect()
            await asyncio.sleep(self._config.retry_delay)

    async def _handle_connected(self) -> None:
        """Monitor connection health when connected."""
        if not self.wlan.isconnected():
            self._log.warning("Connection lost, reconnecting...")
            self.wlan.disconnect()
            self._retry_count = 0
            self._set_state(STATE_CONNECTING)
        else:
            await asyncio.sleep(self._config.health_check_interval)

    async def _handle_fail(self) -> None:
        """Handle failure state with recovery delay, then enter AP mode."""
        self._log.info(f"Cooldown {self._config.fail_recovery_delay}s before AP mode")
        for _ in range(self._config.fail_recovery_delay):
            if self._state != STATE_FAIL:
                return
            await asyncio.sleep(1)
        self._retry_count = 0
        self._set_state(STATE_AP_MODE)

    async def _handle_ap_mode(self) -> None:
        """Manage Access Point and related services."""
        if not self.ap.active():
            self._log.info(f"Starting AP '{self._config.ap_ssid}'")
            self.ap.config(essid=self._config.ap_ssid, password=self._config.ap_password)
            self.ap.active(True)

            # Wait for AP activation with timeout
            for _ in range(AP_ACTIVATION_TIMEOUT):
                if self.ap.active():
                    break
                await asyncio.sleep(0.1)
            else:
                self._log.error("AP activation timeout")
                self._set_state(STATE_FAIL)
                return

            current_ip = self.ap.ifconfig()[0]
            self._log.info(f"AP active at {current_ip}")

            self.dns_server.ip_address = current_ip
            self.dns_server.start()
            await self.web_server.start(host='0.0.0.0', port=80)

        await asyncio.sleep(2)

    def _stop_ap_services(self) -> None:
        """Ensure AP and its services are stopped."""
        if self.ap.active():
            self._log.debug("Stopping AP services")
            self.dns_server.stop()
            self.web_server.stop()
            self.ap.active(False)

    def connect(self, ssid: str, password: str) -> None:
        """
        Trigger a connection request.

        Args:
            ssid: WiFi network name.
            password: WiFi password.
        """
        self._target_ssid = ssid
        self._target_password = password
        self._retry_count = 0
        self._set_state(STATE_CONNECTING)

    def disconnect(self) -> None:
        """Disconnect from WiFi and enter IDLE state."""
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self._set_state(STATE_IDLE)
        self._retry_count = 0
        self._stop_ap_services()

    def enter_ap_mode(self) -> None:
        """Manually enter AP provisioning mode."""
        self._stop_ap_services()
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self._set_state(STATE_AP_MODE)

    def is_connected(self) -> bool:
        """Check if currently connected to WiFi."""
        return self._state == STATE_CONNECTED

    def get_status(self) -> int:
        """Get the current state machine state."""
        return self._state

    def get_status_name(self) -> str:
        """Get the current state name as string."""
        return WiFiState.get_name(self._state)

    def get_config(self) -> tuple:
        """Get current IP configuration (ip, subnet, gateway, dns)."""
        return self.wlan.ifconfig()

    def get_ap_config(self) -> tuple:
        """
        Get AP mode configuration for external display.

        Returns:
            tuple: (ssid, password, ip) for display on screens/LEDs.

        Example:
            ssid, password, ip = wm.get_ap_config()
            display.show(f"SSID: {ssid}")
            display.show(f"Pass: {password}")
        """
        return (self._config.ap_ssid, self._config.ap_password, self._config.ap_ip)

    def is_ap_mode(self) -> bool:
        """Check if currently in AP provisioning mode."""
        return self._state == STATE_AP_MODE

    def get_debug_info(self) -> dict:
        """
        Get all debug information as a single snapshot dict.

        Returns:
            dict: Debug data for external display consumers.
        """
        info = {
            "state": self._state,
            "target_ssid": self._target_ssid,
            "retry_count": self._retry_count,
            "max_retries": self._config.max_retries,
            "wlan_status": None,
            "wlan_rssi": None,
            "wlan_connected": False,
            "wlan_ifconfig": None,
            "ap_active": False,
            "ap_ssid": self._config.ap_ssid,
            "ap_password": self._config.ap_password,
            "ap_ip": self._config.ap_ip,
            "ap_ifconfig": None,
        }
        try:
            info["wlan_status"] = self.wlan.status()
        except Exception:
            pass
        try:
            info["wlan_rssi"] = self.wlan.status('rssi')
        except Exception:
            pass
        try:
            info["wlan_connected"] = self.wlan.isconnected()
        except Exception:
            pass
        try:
            info["wlan_ifconfig"] = self.wlan.ifconfig()
        except Exception:
            pass
        try:
            info["ap_active"] = self.ap.active()
        except Exception:
            pass
        try:
            info["ap_ifconfig"] = self.ap.ifconfig()
        except Exception:
            pass
        return info

    def on(self, event: str, callback) -> None:
        """
        Register a callback for an event.

        Events:
            connected: Called with (ip_address) when WiFi connects.
            disconnected: Called with no args when WiFi disconnects.
            state_change: Called with (old_state, new_state) on any transition.
            ap_mode_started: Called with (ap_ssid) when AP mode activates.
            connection_failed: Called with (retry_count) when entering FAIL state.

        Args:
            event: Event name to listen for.
            callback: Function to call when event occurs.

        Raises:
            ValueError: If event name is not recognized.
        """
        if event not in self._listeners:
            raise ValueError(f"Unknown event: {event}. Valid events: {list(self._listeners.keys())}")
        if callback not in self._listeners[event]:
            self._listeners[event].append(callback)

    def off(self, event: str, callback=None) -> None:
        """
        Remove a callback from an event.

        Args:
            event: Event name to remove callback from.
            callback: Specific callback to remove. If None, removes all callbacks.

        Raises:
            ValueError: If event name is not recognized.
        """
        if event not in self._listeners:
            raise ValueError(f"Unknown event: {event}. Valid events: {list(self._listeners.keys())}")
        if callback is None:
            self._listeners[event] = []
        elif callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def _emit(self, event: str, *args) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event: Event name to emit.
            *args: Arguments to pass to callbacks.
        """
        if event not in self._listeners:
            return
        for callback in self._listeners[event]:
            try:
                callback(*args)
            except Exception as e:
                self._log.error(f"Event callback error ({event}): {e}")
