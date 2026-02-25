# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.5.1] - 2026-02-25

### Changed
- Settings page no longer appears in the horizontal swipe sequence; it now slides up from the bottom as a vertical overlay
- Swipe up on any page to open Settings; swipe down within Settings to dismiss
- `ui/app.py`: Added overlay system with `set_overlay()`, `_show_overlay()`, `_hide_overlay()`, and `_update_overlay_animation()`
- `ui/page.py` and `ui/widget.py`: All `draw()` methods now accept `offset_y` for vertical animation support

## [0.5.0] - 2026-02-25

### Added
- Pages Management: enable/disable and reorder pages via the Web UI Settings page
- `GET /api/pages` and `POST /api/pages` endpoints in `settings_server.py`
- Pages section in `settings.html` with checkboxes and ▲▼ reorder buttons
- Reboot confirmation dialog appears automatically after saving page changes
- `pages` setting in `settings.json` with default `["clock", "weather", "calendar"]`

### Changed
- Market page is now disabled by default (can be re-enabled via Pages Management)
- `main.py` now dynamically loads enabled pages from settings at startup
- Settings page is always fixed as the last page in the sequence

## [0.4.0] - 2026-02-23

### Added
- Market page with real-time cryptocurrency prices and stock quotes
- BTC/ETH live feed via Binance WebSocket (`wss://stream.binance.com:9443`) with auto-reconnect and ping/pong keepalive
- SPY/AAPL/TWII/2330 stock data via Stooq CSV API (polls every 5 minutes)
- WebSocket status indicator in status bar: Live (green) / Reconnecting (red)
- Market-closed periods show `--` gracefully (Stooq N/D handling)
- Color scheme: green for gains, red for losses (western style)
- Page sequence extended to Clock → Weather → Calendar → Market

## [0.3.0] - 2026-02-23

### Added
- Calendar page with monthly grid view and today highlight
- Touch navigation: tap left 1/3 to go to previous month, tap right 1/3 for next month
- Automatic day-change detection to refresh today's highlight at midnight
- Page sequence extended to Clock → Weather → Calendar (swipe left to navigate)

## [0.2.0] - 2026-02-23

### Added
- Weather page with real-time weather data via async Open-Meteo API
- Swipe left/right gesture navigation between Clock and Weather pages

## [0.1.0] - 2026-02-11

### Added
- WiFi infrastructure (Picore-W layer): 5-state async state machine with auto-recovery and captive portal provisioning
- Configuration management with versioned JSON persistence and auto-migration
- Async HTTP/DNS servers for WiFi provisioning portal
- Lightweight logging system with per-module level control
- UI display framework: App, Page, Widget (Label, Button, Container) architecture
- Theme system with unified colors, font scales, and spacing
- PicoVector integration for anti-aliased vector graphics
- Boot splash page with animated progress bar and WiFi status
- AP mode page with setup instructions for captive portal
- Clock page with digital and analog display modes
- Digital clock: large HH:MM display with screensaver-style drift animation
- Analog clock: vector-drawn face with hour/minute/second hands, tick marks, and center date
- Tap-to-switch between clock modes with linear slide transition
- NTP time synchronization with configurable timezone offset (default UTC+8)
- Debug dashboard mode for Pico Explorer hardware
