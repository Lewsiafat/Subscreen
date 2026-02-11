# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Subscreen** is a MicroPython "second screen" device designed to sit on a desk/table, built on the **Pimoroni Presto** (RP2350) platform with a 240x240 touch display. It connects to WiFi to fetch and display real-time information (weather, calendar, notifications, system stats, etc.) as a companion display.

The project builds on top of the **Picore-W** WiFi infrastructure library, which provides resilient WiFi state management with automatic recovery and captive portal provisioning.

### Target Hardware

- **Primary:** Pimoroni Presto (RP2350) — 240x240 IPS touch display, WiFi, 7 RGB LEDs, accelerometer, buzzer, SD card slot
- **Also compatible:** Raspberry Pi Pico 2 W (RP2350), Pico W (RP2040)

## Development Environment

MicroPython project — no traditional build system. Code deploys directly to hardware.

**Required Tools:**
- `mpremote` CLI (`pip install mpremote`)
- MicroPython firmware on target device (Pimoroni custom firmware for Presto)

**Deploy to device:** `/deploy` (uses `mpremote` to upload `src/` to Pico)
**Run on device:** `/run` for normal mode, `/run` with debug option for display dashboard
**Lint:** `pylint`

## Code Style

- Google Python Style Guide, 80-char line limit, 4-space indent
- `snake_case` functions/variables, `PascalCase` classes, `ALL_CAPS` constants
- Type annotations encouraged for public APIs
- Docstrings: triple double quotes with `Args:`, `Returns:`, `Raises:`

## Architecture

### WiFi Infrastructure (Picore-W Layer)

5-state WiFi lifecycle managed by `src/wifi_manager.py`:

```
IDLE → CONNECTING → CONNECTED ↔ (health check every 2s)
                  ↘ FAIL → AP_MODE (captive portal provisioning)
```

Key modules:
- `wifi_manager.py` — Core async state machine with event system (`on`/`off` callbacks)
- `config_manager.py` — Versioned JSON persistence (`wifi_config.json`, auto-migrates v1→v2)
- `provisioning.py` — Web-based WiFi setup with captive portal (Apple/Android detection)
- `web_server.py` / `dns_server.py` — Async HTTP + DNS servers for provisioning
- `logger.py` — Lightweight logging with global/per-module levels and hook system
- `constants.py` — `WiFiState` class (IDLE=0, CONNECTING=1, CONNECTED=2, FAIL=3, AP_MODE=4)

### Presto Hardware API (from frozen modules)

```python
from presto import Presto
presto = Presto(ambient_light=True)  # 240x240 default
display = presto.display              # PicoGraphics instance
touch = presto.touch                  # FT6236 touch driver
WIDTH, HEIGHT = display.get_bounds()

# Full resolution (memory intensive)
presto = Presto(full_res=True, palette=True)  # 480x480, 8-bit palette saves RAM

# Touch buttons
from touch import Button
btn = Button(x, y, w, h)
touch.poll()  # Must call every loop
btn.is_pressed()

# Display update (must call to render)
presto.update()        # Full update + touch poll
presto.partial_update(x, y, w, h)  # Partial region

# Hardware
presto.set_backlight(0.5)          # 0.0–1.0
presto.set_led_rgb(0, 255, 0, 0)  # LED index 0-6
presto.connect()                    # Blocking WiFi (uses secrets.py)
await presto.async_connect()        # Async WiFi
```

### Design Principles

- **Async-First:** All network operations use `uasyncio`, non-blocking
- **Pure MicroPython:** No external dependencies, only built-in + Pimoroni frozen modules
- **Hardware-Aware:** RP2350 memory constraints; 240x240 standard, 480x480 requires `palette=True`
- **Resilience Over Features:** Every network state handled gracefully with auto-recovery

### Event System

```python
wm = WiFiManager()
wm.on("connected", lambda ip: print(f"Connected: {ip}"))
wm.on("disconnected", lambda: reconnect())
wm.on("state_change", lambda old, new: update_display())
wm.on("ap_mode_started", lambda ssid: show_setup_screen())
```

### Logging

```python
from logger import Logger, LogLevel
log = Logger("MyModule")
log.debug("detail")  # [DEBUG] MyModule: ...
Logger.set_level(LogLevel.DEBUG)
Logger.set_module_level("WiFiManager", LogLevel.ERROR)
```

## Project Structure

```
src/                    # All source code (deployed to Pico root)
  templates/            # HTML for provisioning UI
  main.py               # Production entry point
  main_debug.py         # Debug entry point (Pico Explorer display)
ref_doc/                # Reference documentation
  AI_REFERENCE_GUIDE.md # Presto device coding patterns
  MODULE_SPEC.md        # Frozen module API specs (presto, touch, lsm6ds3, etc.)
  WIFI_BASE.md          # Original Picore-W CLAUDE.md
specs/                  # Feature specifications
```

## Commit Convention

```
<type>(<scope>): <description>
```
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Key Reference Files

- `ref_doc/AI_REFERENCE_GUIDE.md` — Presto boilerplate, touch, vectors, WiFi, sensors, audio, SD card patterns
- `ref_doc/MODULE_SPEC.md` — Full API for frozen modules: `presto`, `ezwifi`, `touch`, `lsm6ds3`, `psram`, `qwstpad`
