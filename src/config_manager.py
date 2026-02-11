import json
import os
import time

CONFIG_FILE = "wifi_config.json"
CONFIG_VERSION = 2


class ConfigManager:
    """
    Manages persistent storage of WiFi configuration data.

    Uses a JSON file on the Flash filesystem with version tracking
    for forward compatibility and data migration.
    """

    @staticmethod
    def _migrate_v1_to_v2(data: dict) -> dict:
        """
        Migrate v1 config (no version field) to v2 format.

        Args:
            data: Legacy config with ssid/password at root level.

        Returns:
            Config in v2 format with version and wifi section.
        """
        return {
            "version": 2,
            "wifi": {
                "ssid": data.get("ssid", ""),
                "password": data.get("password", "")
            }
        }

    @staticmethod
    def _migrate(data: dict) -> dict:
        """
        Migrate config data to the current version.

        Args:
            data: Config data of any version.

        Returns:
            Config data migrated to CONFIG_VERSION.
        """
        version = data.get("version", 1)

        if version == 1:
            data = ConfigManager._migrate_v1_to_v2(data)
            version = 2

        return data

    @staticmethod
    def load_config() -> dict:
        """
        Load configuration from the JSON file.

        Automatically migrates older config formats to the current version.
        The migrated config is saved back to ensure persistence.

        Returns:
            dict: Configuration data with 'wifi' containing 'ssid' and
                  'password', or None if file doesn't exist or is invalid.
        """
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except OSError:
            return None
        except ValueError as e:
            print(f"ConfigManager: Error loading config: {e}")
            return None

        version = data.get("version", 1)
        if version < CONFIG_VERSION:
            data = ConfigManager._migrate(data)
            ConfigManager._save_raw(data)

        return data

    @staticmethod
    def get_wifi_credentials() -> tuple:
        """
        Get WiFi credentials from config.

        Returns:
            tuple: (ssid, password) or (None, None) if not configured.
        """
        config = ConfigManager.load_config()
        if config and "wifi" in config:
            wifi = config["wifi"]
            return (wifi.get("ssid"), wifi.get("password"))
        elif config and "ssid" in config:
            return (config.get("ssid"), config.get("password"))
        return (None, None)

    @staticmethod
    def _save_raw(data: dict) -> bool:
        """
        Save raw config data to file with verification.

        Args:
            data: Complete config dict to save.

        Returns:
            bool: True if save and verification succeeded.
        """
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
                f.flush()

            time.sleep(0.1)
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                if saved != data:
                    print("ConfigManager: Verification FAILED."
                          " Content mismatch.")
                    return False
                return True
        except OSError as e:
            print(f"ConfigManager: Error saving config: {e}")
            return False
        except Exception as e:
            print(f"ConfigManager: Unexpected error during save: {e}")
            return False

    @staticmethod
    def save_config(ssid: str, password: str) -> bool:
        """
        Save WiFi credentials to the JSON file with verification.

        Args:
            ssid: The WiFi SSID to save.
            password: The WiFi password to save.

        Returns:
            bool: True if save was successful and verified, False otherwise.
        """
        existing = ConfigManager.load_config()
        if existing and existing.get("version") == CONFIG_VERSION:
            existing["wifi"] = {"ssid": ssid, "password": password}
            data = existing
        else:
            data = {
                "version": CONFIG_VERSION,
                "wifi": {"ssid": ssid, "password": password}
            }

        return ConfigManager._save_raw(data)

    @staticmethod
    def delete_config() -> bool:
        """
        Remove the configuration file (factory reset of network settings).

        Returns:
            bool: True if the file was deleted, False if it didn't exist
                  or an error occurred.
        """
        try:
            os.remove(CONFIG_FILE)
            return True
        except OSError:
            return False

    @staticmethod
    def get_version() -> int:
        """
        Get the version of the current config file.

        Returns:
            int: Config version, or 0 if no config exists.
        """
        config = ConfigManager.load_config()
        if config:
            return config.get("version", 1)
        return 0
