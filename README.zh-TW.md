# Subscreen

基於 [Pimoroni Presto](https://shop.pimoroni.com/products/presto) (RP2350) 的桌面副螢幕裝置。透過 240x240 觸控顯示器，在桌面上即時顯示各類資訊。

[English](README.md)

## 硬體需求

- **Pimoroni Presto** — RP2350 + 240x240 IPS 觸控螢幕、WiFi、7 RGB LEDs、加速度計、蜂鳴器、SD 卡槽
- USB-C 傳輸線（部署與供電）

## 功能特色

- **時鐘頁面** — 數位/類比雙模式，點擊切換，螢幕保護漂移動畫
- **天氣頁面** — 透過非同步 Open-Meteo API 取得即時天氣資訊，左右滑動切換頁面
- **日曆頁面** — 月曆格式顯示，今日高亮，點擊左右切換月份
- **行情頁面** — BTC/ETH 透過 Binance WebSocket 即時推送 + SPY/AAPL/TWII/2330 透過 Stooq CSV API 輪詢（預設停用）
- **頁面管理** — 透過 Web 設定介面啟用/停用頁面並調整順序，重開機後生效
- **NTP 時間同步** — WiFi 連線後自動同步，可設定時區
- **WiFi 自動管理** — 連線失敗自動重試，超過上限後進入 AP 模式
- **Captive Portal 設定** — AP 模式下透過手機瀏覽器設定 WiFi 密碼
- **觸控 UI 框架** — Page/Widget 架構，支援頁面切換動畫
- **Debug 儀表板** — 即時顯示 WiFi 狀態、設定、日誌（需 Pico Explorer）

## 快速開始

### 安裝工具

```bash
pip install mpremote
```

### 部署到裝置

將 Presto 透過 USB 連接電腦，然後：

```bash
# 使用 Claude Code skill
/deploy

# 或手動
mpremote cp -r src/ :
```

### 執行

```bash
# 使用 Claude Code skill
/run
```

## 專案結構

```
src/                    # 原始碼（部署至 Pico 根目錄）
  ui/                   # UI 框架
    app.py              # App — 硬體初始化 + 渲染迴圈
    page.py             # Page 基類 — 生命週期、觸控分派
    widget.py           # Widget — Label, Button, Container
    theme.py            # 主題色彩、字型、間距
  pages/                # 應用頁面
    splash_page.py      # 開機動畫 + WiFi 狀態
    ap_mode_page.py     # AP 模式設定引導
    clock_page.py       # 時鐘 — 數位/類比模式、NTP 同步
    weather_page.py     # 天氣 — 透過 Open-Meteo API 取得即時資料
    calendar_page.py    # 日曆 — 月曆格、今日高亮、觸控月份切換
    market_page.py      # 行情 — Binance WebSocket 加密貨幣 + Stooq 股票報價
    settings_page.py    # 設定 — QR Code + IP，引導進入 Web 設定介面
  settings_server.py    # Web 設定伺服器，提供 /api/pages、/api/settings 端點
  wifi_manager.py       # WiFi 狀態機核心
  provisioning.py       # Web 設定介面
  config_manager.py     # 設定檔管理
  web_server.py         # Async HTTP 伺服器
  dns_server.py         # Captive Portal DNS
  logger.py             # 日誌系統
  main.py               # 主程式進入點
  main_debug.py         # Debug 模式進入點
  templates/            # 設定頁面 HTML
ref_doc/                # 參考文件
specs/                  # 功能規格文件
```

## 技術架構

建立在 **Picore-W** WiFi 基礎設施之上，使用 MicroPython + `uasyncio` 非同步架構。

WiFi 生命週期：

```
IDLE → CONNECTING → CONNECTED（每 2 秒健康檢查）
                  ↘ FAIL → AP_MODE（Captive Portal 設定）
```

頁面流程：

```
SplashPage → ClockPage（WiFi 連線成功）
           → ApModePage（WiFi 連線失敗，進入 AP 模式）

ClockPage ←滑動→ WeatherPage ←滑動→ CalendarPage ←滑動→ ... ←滑動→ SettingsPage
（頁面順序與顯示可透過 Web 設定介面調整）
```
