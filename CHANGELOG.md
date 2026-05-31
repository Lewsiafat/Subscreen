# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.7.1] - 2026-05-31

### Changed
- Pomodoro **Work** duration is now a fixed preset list (10 / 15 / 30 / 45 min) instead of a 1–90 step-5 range. On-device `−`/`+` steps through the presets (clamped at the ends); the Web Settings Work field is now a matching dropdown.
- Default `pomodoro_work` is now 30 (was 25, which is not in the preset list). Saved non-preset values snap to the nearest preset on page load.

## [0.7.0] - 2026-05-31

### Added
- **Pomodoro Page** ("tomato clock") — cycles Work → Break until a configurable total session time elapses, with buzzer + RGB LED feedback at each boundary. IDLE `-`/`+` controls for work/break/total, running countdown with progress ring, tap-to-pause, and RESET.
- `pomodoro_work` / `pomodoro_break` / `pomodoro_total` settings (defaults 25 / 5 / 120 min) with a Pomodoro section in the Web Settings UI.
- `"pomodoro"` registered as an available page in `settings_server.py` and the `main.py` page builder.
- `pomodoro_alert` setting (`off` / `normal` / `loud`, default `loud`) with an Alert dropdown in the Web Settings UI — controls phase-switch and session-done alert intensity.
- `loud` alert mode blinks all 7 RGB LEDs and plays an urgent siren sweep at the piezo resonant frequency (~3 kHz) so the alert is far more noticeable.

### Changed
- `pomodoro_page.py` `_signal_phase` / `_signal_done` are now tiered by `pomodoro_alert`; new non-blocking `_blink_leds` and `_alarm` helpers, guarded by an `_alert_seq` generation counter so in-flight alerts abort cleanly on page exit/reset.

## [0.6.0] - 2026-02-25

### Added
- City name search in Settings Location section using Open-Meteo Geocoding API (browser-side, no API key required)
- Weather page now displays the current location name at the top (small gray text, centered)
- `on_resume()` hook in `Page` base class — called when the settings overlay is dismissed
- `WeatherPage.on_resume()` — immediately re-reads location settings and refreshes when settings overlay closes

### Changed
- `saveLocation()` now also saves `weather_location` (city name) alongside lat/lon
- Settings page loads and displays the previously saved city name in the City search field
- Save Location success now shows a dialog with instructions instead of a small status text

### Fixed
- Weather page location and forecast did not update immediately after closing Settings overlay; required swiping away and back to apply

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
