class WiFiConfig:
    """
    Configuration for WiFi connection and AP mode.

    This class provides default values that can be overridden at runtime
    by passing parameters to WiFiManager constructor.

    Attributes:
        MAX_RETRIES: Maximum connection attempts before entering FAIL state.
        CONNECT_TIMEOUT: Seconds to wait for connection per attempt.
        RETRY_DELAY: Seconds to wait between retry attempts.
        FAIL_RECOVERY_DELAY: Seconds in FAIL state before auto-recovery.
        HEALTH_CHECK_INTERVAL: Seconds between connection health checks.
        AP_SSID: Default SSID for provisioning AP mode.
        AP_PASSWORD: Default password for provisioning AP mode.
        AP_IP: IP address for AP mode.
    """
    # Connection parameters
    MAX_RETRIES = 5
    CONNECT_TIMEOUT = 15
    RETRY_DELAY = 2
    FAIL_RECOVERY_DELAY = 30
    HEALTH_CHECK_INTERVAL = 2

    # AP Mode Settings
    AP_SSID = "Picore-W-Setup"
    AP_PASSWORD = "PicoreSetup2024!"
    AP_IP = "192.168.4.1"

    def __init__(
        self,
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
        Create a configuration instance with optional overrides.

        Args:
            max_retries: Override MAX_RETRIES (default 5).
            connect_timeout: Override CONNECT_TIMEOUT (default 15).
            retry_delay: Override RETRY_DELAY (default 2).
            fail_recovery_delay: Override FAIL_RECOVERY_DELAY (default 30).
            health_check_interval: Override HEALTH_CHECK_INTERVAL (default 2).
            ap_ssid: Override AP_SSID (default "Picore-W-Setup").
            ap_password: Override AP_PASSWORD.
            ap_ip: Override AP_IP (default "192.168.4.1").
        """
        self.max_retries = max_retries if max_retries is not None else WiFiConfig.MAX_RETRIES
        self.connect_timeout = connect_timeout if connect_timeout is not None else WiFiConfig.CONNECT_TIMEOUT
        self.retry_delay = retry_delay if retry_delay is not None else WiFiConfig.RETRY_DELAY
        self.fail_recovery_delay = fail_recovery_delay if fail_recovery_delay is not None else WiFiConfig.FAIL_RECOVERY_DELAY
        self.health_check_interval = health_check_interval if health_check_interval is not None else WiFiConfig.HEALTH_CHECK_INTERVAL
        self.ap_ssid = ap_ssid if ap_ssid is not None else WiFiConfig.AP_SSID
        self.ap_password = ap_password if ap_password is not None else WiFiConfig.AP_PASSWORD
        self.ap_ip = ap_ip if ap_ip is not None else WiFiConfig.AP_IP
