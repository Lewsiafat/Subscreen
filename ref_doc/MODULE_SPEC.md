# Presto Py_Frozen Modules API Specification

This document provides the API specification for the frozen Python modules available in the `modules/py_frozen` directory.

## Table of Contents

- [presto](#module-presto)
- [ezwifi](#module-ezwifi)
- [touch](#module-touch)
- [lsm6ds3](#module-lsm6ds3)
- [psram](#module-psram)
- [qwstpad](#module-qwstpad)

---

## Module: `presto`

Main interface for the Presto device, handling display, touch, WiFi, and audio.

### Class: `Buzzer`

Control the piezo buzzer.

#### `__init__(self, pin)`
- `pin`: The GPIO pin number connected to the buzzer.

#### `set_tone(self, freq, duty=0.5)`
Sets the frequency and duty cycle of the buzzer.
- `freq`: Frequency in Hz. If `< 50.0`, the buzzer is turned off.
- `duty`: Duty cycle (0.0 to 1.0). Default is 0.5.
- **Returns**: `True` if tone set, `False` if frequency was too low (buzzer off).

### Class: `Presto`

The main class to interact with Presto hardware.

#### `__init__(self, full_res=False, palette=False, ambient_light=False, direct_to_fb=False, layers=None)`
- `full_res`: Resolution control.
  - `False` (Default): 240x240 resolution. Uses ~115KB RAM (16-bit). Safe for most uses.
  - `True`: 480x480 resolution. Uses ~460KB RAM (16-bit). May require `palette=True` or careful memory management on devices without PSRAM.
- `palette`: If `True`, uses `PEN_P8` (8-bit palette), otherwise `PEN_RGB565`. Reduces memory usage by 50%.
- `ambient_light`: If `True`, enables auto ambient LED control.
- `direct_to_fb`: If `True` and using full res without palette, writes directly to frame buffer (saves RAM).
- `layers`: Number of display layers. Defaults to 1 for full res, 2 otherwise.

#### Properties
- `touch_a`: Returns `Touch(x, y, touched)` for the first touch point.
- `touch_b`: Returns `Touch(x, y, touched)` for the second touch point.
- `touch_delta`: Returns a tuple `(distance, angle)` between two touch points.

#### Constants
- `NUM_LEDS = 7`
- `LED_PIN = 33`

#### Methods
- `async_connect(self)`: Async method to connect to WiFi.
- `set_backlight(self, brightness)`: Sets display backlight brightness (0.0 - 1.0).
- `auto_ambient_leds(self, enable)`: Enable/disable automatic ambient light LED control.
- `set_led_rgb(self, i, r, g, b)`: Set LED `i` (0-6) to RGB color.
- `set_led_hsv(self, i, h, s, v)`: Set LED `i` (0-6) to HSV color.
- `connect(self, ssid=None, password=None)`: Synchronous WiFi connect. Uses `secrets.py` if args not provided.
- `touch_poll(self)`: Poll touch sensor manually.
- `update(self)`: Update the display and poll touch.
- `partial_update(self, x, y, w, h)`: Update a region of the display and poll touch.
- `clear(self)`: Clear the display and update.

---

## Module: `ezwifi`

Simplified WiFi connection management.

### Class: `EzWiFi`

#### `__init__(self, **kwargs)`
- `verbose`: (bool) Enable verbose logging.
- Callbacks: `connected`, `failed`, `info`, `warning`, `error`.

#### Methods
- `on(self, handler_name, handler=None)`: Register a callback handler. Used as decorator if `handler` is None.
- `error(self)`: Returns `(last_error_code, last_error_message)`.
- `connect(self, ssid=None, password=None, timeout=60, retries=10)`: Async connection attempt.
- `isconnected(self)`: Returns `True` if connected.
- `ipv4(self)`: Returns IPv4 address.
- `ipv6(self)`: Returns IPv6 address.

### Helper Function
- `connect(**kwargs)`: Helper to create `EzWiFi` instance and connect synchronously.

---

## Module: `touch`

Touch screen driver (FT6236).

### Class: `Button`

Simple soft-button logic.

#### `__init__(self, x, y, w, h)`
Define a button area.
- `x, y`: Top-left coordinates.
- `w, h`: Width and height.

#### Methods
- `is_pressed(self)`: Returns `True` if currently pressed.
- `bounds`: Property returning `(x, y, w, h)`.

### Class: `FT6236`

#### `__init__(self, full_res=False, enable_interrupt=False)`
- `full_res`: Adjusts coordinate scaling.
- `enable_interrupt`: If `True`, uses IRQ pin instead of polling (logic present but `poll` implementation returns early if IRQ).

#### Methods
- `poll(self)`: Polls the I2C bus for touch data (if not using interrupts).

---

## Module: `lsm6ds3`

Driver for LSM6DS3 Accelerometer and Gyroscope.

### Class: `LSM6DS3`

#### `__init__(self, i2c, address=0x6A, mode=NORMAL_MODE_104HZ)`
- `i2c`: I2C bus object.
- `address`: I2C address.
- `mode`: Sampling rate mode.

#### Methods
- `get_readings(self)`: Returns `(ax, ay, az, gx, gy, gz)` raw readings.
- `get_step_count(self)`: Returns pedometer step count.
- `reset_step_count(self)`: Resets step count.
- `tilt_detected(self)`: Returns `1` if tilt detected.
- `sig_motion_detected(self)`: Returns `1` if significant motion detected.
- `single_tap_detected(self)`: Returns `1` if single tap detected.
- `double_tap_detected(self)`: Returns `1` if double tap detected.
- `freefall_detected(self)`: Returns `1` if freefall detected.

---

## Module: `psram`

Utilities for using external PSRAM.

### Constants
- `PSRAM_BASE = 0x11000000`
- `PSRAM_SIZE = 8MB`

### Class: `PSRAMBlockDevice`

Block device interface for PSRAM, suitable for mounting as a filesystem.

#### `__init__(self, size, offset=None, blocksize=256, debug=False)`
- `size`: Size of filesystem in bytes.
- `offset`: Offset in PSRAM. Defaults to end of PSRAM (`PSRAM_SIZE - size`).

### Function: `mkramfs`

#### `mkramfs(size=64KB, mount_point="/ramfs", debug=False)`
Creates and mounts a LittleFS filesystem in PSRAM.

---

## Module: `qwstpad`

Driver for QwSTPad (I2C button/LED interface, likely TCA9555 based).

### Class: `QwSTPad`

#### `__init__(self, i2c, address=0x21, show_address=True)`
- `i2c`: I2C bus object.
- `address`: I2C address (0x21, 0x23, 0x25, 0x27).
- `show_address`: If `True`, displays address on LEDs at startup.

#### Methods
- `read_buttons(self)`: Reads and returns dictionary of button states (A, B, X, Y, U, D, L, R, +, -).
- `set_leds(self, states)`: Set all 4 LEDs using a bitmask (4 bits).
- `set_led(self, led, state)`: Set a specific LED (1-4) on or off.
- `clear_leds(self)`: Turn off all LEDs.
