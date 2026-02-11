# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Picore-W is a MicroPython infrastructure library for **Raspberry Pi Pico 2 W (RP2350)** and **Raspberry Pi Pico W (RP2040)**. It implements a resilient WiFi State Machine that manages network connection lifecycle with automatic recovery and AP-mode provisioning.

## Development Environment

This is a MicroPython project - no traditional build system exists. Code is deployed directly to hardware.

**Required Tools:**
- VS Code with MicroPico extension (or `mpremote` CLI)
- MicroPython firmware on target Pico device

**Deployment:**
- Upload all files from `src/` to the root of the Pico device
- The `templates/` folder must be included for provisioning UI

## Code Style

Follow the Google Python Style Guide:
- **Linting:** `pylint`
- **Line length:** 80 characters max
- **Indentation:** 4 spaces (never tabs)
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes, `ALL_CAPS` for constants
- **Type annotations:** Encouraged for public APIs
- **Docstrings:** Triple double quotes, include `Args:`, `Returns:`, `Raises:` sections

## Architecture

### Core State Machine

The WiFi lifecycle is managed through 5 states in `src/wifi_manager.py`:

| State | Value | Description |
|-------|-------|-------------|
| STATE_IDLE | 0 | Initial/waiting state |
| STATE_CONNECTING | 1 | Attempting WiFi connection |
| STATE_CONNECTED | 2 | Connected with IP assigned |
| STATE_FAIL | 3 | Failed, cooling down before retry |
| STATE_AP_MODE | 4 | Provisioning hotspot active |

### Key Files

- `src/wifi_manager.py` - Core state machine, WiFi lifecycle, and event system
- `src/provisioning.py` - Web-based WiFi provisioning handler (routes, templates, form processing, WiFi SSID scanning)
- `src/config_manager.py` - Versioned JSON persistence with automatic migration
- `src/web_server.py` - Async HTTP server for provisioning UI
- `src/dns_server.py` - Captive portal DNS server
- `src/logger.py` - Lightweight logging with global and per-module level control, hook system
- `src/config.py` - Configuration class with runtime override support
- `src/constants.py` - `WiFiState` class with state definitions and utilities
- `src/main.py` - Standard entry point (no display, pure WiFi management)
- `src/debug_display.py` - Debug dashboard for Pico Explorer 2.8" display (4 pages, button navigation)
- `src/main_debug.py` - Debug mode entry point (upload as `main.py` to device)

### Design Principles

- **Async-First:** All network operations use `uasyncio`, non-blocking execution
- **Pure MicroPython:** No external dependencies, only built-in modules (`network`, `uasyncio`, `usocket`, `json`, `machine`)
- **Resilience Over Features:** Every network state must be handled gracefully with auto-recovery
- **Hardware-Aware:** Designed for RP2350/RP2040 memory and power constraints

### Logging System

The project uses a lightweight logging system (`src/logger.py`) with configurable levels:

```python
from logger import Logger, LogLevel

log = Logger("MyModule")
log.debug("Verbose details")    # [DEBUG] MyModule: ...
log.info("Normal operation")    # [INFO] MyModule: ...
log.warning("Potential issue")  # [WARN] MyModule: ...
log.error("Failure occurred")   # [ERROR] MyModule: ...

# Change global log level
Logger.set_level(LogLevel.DEBUG)  # Show all messages
Logger.set_level(LogLevel.ERROR)  # Only show errors

# Module-specific level (overrides global for that module)
Logger.set_module_level("WiFiManager", LogLevel.DEBUG)
Logger.set_module_level("WebServer", LogLevel.ERROR)

# Hook system - capture logs programmatically
def my_hook(level, module, msg):
    # level: int, module: str, msg: str
    pass

Logger.add_hook(my_hook)
Logger.remove_hook(my_hook)
```

### Event System

`WiFiManager` supports event-driven programming via callbacks:

```python
wm = WiFiManager()

def on_connected(ip):
    print(f"Connected: {ip}")

def on_state_change(old, new):
    print(f"State: {old} -> {new}")

wm.on("connected", on_connected)
wm.on("state_change", on_state_change)
wm.off("connected", on_connected)  # Remove listener
```

Available events:
- `connected(ip_address)` - WiFi connection established
- `disconnected()` - WiFi connection lost
- `state_change(old_state, new_state)` - Any state transition
- `ap_mode_started(ap_ssid)` - AP mode activated
- `connection_failed(retry_count)` - Entered FAIL state

### Display Integration

Retrieve AP credentials for external displays (OLED, LCD):

```python
# Get AP config for display
ssid, password, ip = wm.get_ap_config()

# Check if in AP mode
if wm.is_ap_mode():
    display.text(f"SSID: {ssid}", 0, 0)
    display.text(f"Pass: {password}", 0, 16)
```

### Debug Info API

`WiFiManager.get_debug_info()` returns a snapshot dict of all debug data, with hardware access wrapped in try/except:

```python
info = wm.get_debug_info()
# Returns: {
#   "state": int, "target_ssid": str|None,
#   "retry_count": int, "max_retries": int,
#   "wlan_status": int|None, "wlan_rssi": int|None,
#   "wlan_connected": bool, "wlan_ifconfig": tuple|None,
#   "ap_active": bool, "ap_ssid": str,
#   "ap_password": str, "ap_ip": str, "ap_ifconfig": tuple|None,
# }
```

### Debug Display (Pico Explorer)

Hardware debug dashboard using 2.8" PicoGraphics display and 4 buttons. Requires Pimoroni MicroPython firmware with `picographics` module.

`DebugDisplay` accepts a **data provider** callable (returning a dict) instead of a `WiFiManager` instance directly. This decouples the display from any specific data source.

```python
from debug_display import DebugDisplay

# Using WiFiManager's built-in provider
debug = DebugDisplay(wm.get_debug_info)

# Or any callable returning the expected dict
debug = DebugDisplay(my_custom_data_provider)

# Enable/disable at runtime
debug.disable()   # Stops rendering, clears screen
debug.enable()    # Resumes rendering
debug.is_enabled()  # Query state
```

**Pages** (navigate with A/B buttons):
| Page | Content |
|------|---------|
| Status | WiFi state, IP, SSID, retry count, uptime, WLAN status |
| Config | Saved SSID, password (masked), config version, file status |
| Log | Last ~11 log entries, colour-coded by level |
| Network | WLAN status, RSSI, AP mode info |

**Buttons:** A=prev page, B=next page, X=context action (Config: toggle password, Log: clear), Y=toggle log level (DEBUG/INFO)

**Usage:** Upload `main_debug.py` as `main.py` to the device. If startup fails, error is shown on display and LED flashes.

### Runtime Configuration

`WiFiManager` accepts configuration parameters at construction:

```python
# Override specific settings
wm = WiFiManager(
    max_retries=10,
    connect_timeout=20,
    ap_ssid="MyDevice-Setup",
    ap_password="SecurePass!"
)

# Or pass a WiFiConfig instance
from config import WiFiConfig
cfg = WiFiConfig(max_retries=10, ap_ssid="Custom")
wm = WiFiManager(config=cfg)
```

### Dependency Injection

`WiFiManager` supports dependency injection for testing and customization:

```python
# Default usage
manager = WiFiManager()

# Custom services
custom_dns = DNSServer("192.168.1.1")
custom_web = WebServer()
manager = WiFiManager(dns_server=custom_dns, web_server=custom_web)
```

### WiFiState Class

State constants are available via the `WiFiState` class:

```python
from constants import WiFiState

state = WiFiState.CONNECTED
name = WiFiState.get_name(state)  # "CONNECTED"
valid = WiFiState.is_valid(state)  # True
all_states = WiFiState.all_states()  # [0, 1, 2, 3, 4]
```

### Config Versioning

`ConfigManager` uses versioned config files for forward compatibility:

```python
from config_manager import ConfigManager

# Get WiFi credentials (handles migration automatically)
ssid, password = ConfigManager.get_wifi_credentials()

# Check config version
version = ConfigManager.get_version()  # Returns 2 for current format
```

## Project Guidelines

- **No testing in production code:** Test files are kept separate
- **Minimalist documentation:** Use clear naming; comments only for complex logic or hardware workarounds
- **All source code in `src/`:** Maintain flat, intuitive directory structure

## Commit Message Format

```
<type>(<scope>): <description>
```
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Versioning

Semantic Versioning with manual `CHANGELOG.md` updates. Release tags use annotated format: `git tag -a vX.Y.Z -m "Release vX.Y.Z: [summary]"`

## Project Structure

```
src/                    # Library code (deployed to Pico)
  templates/            # HTML for provisioning UI
  main.py               # Standard entry point (no display)
  main_debug.py         # Debug entry point (rename to main.py for use)
  debug_display.py      # Debug dashboard (requires Pico Explorer)
examples/               # Integration examples
```
