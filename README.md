# Subscreen

A desktop sub-screen device based on [Pimoroni Presto](https://shop.pimoroni.com/products/presto) (RP2350). Displays various real-time information on your desktop via a 240x240 touch display.

[繁體中文](README.zh-TW.md)

## Hardware Requirements

- **Pimoroni Presto** — RP2350 + 240x240 IPS touch screen, WiFi, 7 RGB LEDs, accelerometer, buzzer, SD card slot
- USB-C cable (for deployment and power)

## Features

- **Clock Page** — Digital/analog dual modes, toggle by tapping, screen saver drift animation.
- **Weather Page** — Real-time weather data via async Open-Meteo API, swipe to navigate.
- **Calendar Page** — Monthly calendar grid, today highlighted, tap to switch months.
- **Market Page** — Real-time BTC/ETH via Binance WebSocket + SPY/AAPL/TWII/2330 via Stooq CSV API.
- **NTP Time Sync** — Auto-sync after WiFi connection, configurable time zone.
- **WiFi Auto Management** — Auto-retry on connection failure, enters AP mode after exceeding retry limits.
- **Captive Portal Setup** — Configure WiFi password via mobile browser in AP mode.
- **Touch UI Framework** — Page/Widget architecture, supports page transition animations.
- **Debug Dashboard** — Real-time display of WiFi status, settings, and logs (requires Pico Explorer).

## Quick Start

### Install Tools

```bash
pip install mpremote
```

### Deploy to Device

Connect Presto to your computer via USB, then:

```bash
# Using Claude Code skill
/deploy

# Or manually
mpremote cp -r src/ :
```

### Run

```bash
# Using Claude Code skill
/run
```

## Project Structure

```
src/                    # Source code (deploy to Pico root)
  ui/                   # UI Framework
    app.py              # App — Hardware init + rendering loop
    page.py             # Page base class — Lifecycle, touch dispatching
    widget.py           # Widget — Label, Button, Container
    theme.py            # Theme colors, fonts, spacing
  pages/                # Application pages
    splash_page.py      # Boot animation + WiFi status
    ap_mode_page.py     # AP mode setup guide
    clock_page.py       # Clock — Digital/analog modes, NTP sync
    weather_page.py     # Weather — Real-time data via Open-Meteo API
    calendar_page.py    # Calendar — Monthly grid, today highlight, touch navigation
    market_page.py      # Market — Binance WebSocket crypto + Stooq stock quotes
  wifi_manager.py       # WiFi state machine core
  provisioning.py       # Web setup interface
  config_manager.py     # Config file management
  web_server.py         # Async HTTP server
  dns_server.py         # Captive Portal DNS
  logger.py             # Logging system
  main.py               # Main entry point
  main_debug.py         # Debug mode entry point
  templates/            # Setup page HTML
ref_doc/                # Reference documents
specs/                  # Functional specification documents
```

## Technical Architecture

Built on top of the **Picore-W** WiFi infrastructure, using MicroPython + `uasyncio` asynchronous architecture.

WiFi Lifecycle:

```
IDLE → CONNECTING → CONNECTED (Health check every 2s)
                  ↘ FAIL → AP_MODE (Captive Portal setup)
```

Page Flow:

```
SplashPage → ClockPage (WiFi connection success)
           → ApModePage (WiFi connection failed, enter AP mode)

ClockPage ←swipe→ WeatherPage ←swipe→ CalendarPage ←swipe→ MarketPage
```
