# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
