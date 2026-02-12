# 新增天氣頁面 — Walkthrough

- **分支:** `feat/add-weather-page`
- **日期:** 2026-02-12

## 變更摘要
新增天氣頁面，透過 Open-Meteo API 非阻塞取得即時天氣與 4 日預報。在 App 層級實作左右滑動手勢偵測與頁面切換動畫，支援時鐘頁與天氣頁雙向滑動。ClockPage 模式切換改為雙擊以避免與滑動手勢衝突。

## 修改的檔案

### 新增
- **`src/pages/weather_page.py`** — 天氣頁面主體。上半部顯示即時天氣（溫度、濕度、風速、天氣狀況），下半部顯示 4 日預報。使用 `uasyncio.open_connection` 實作非阻塞 HTTP GET，避免 `urequests` 阻塞事件迴圈。10 分鐘自動刷新，有快取機制（重新進入頁面不重複抓取）。
- **`specs/add-weather-page.md`** — 功能規格文件。

### 修改
- **`src/ui/app.py`** — 新增頁面序列管理（`set_pages`）、左右滑動手勢偵測（觸控起終點距離 ≥ 50px）、滑動切換動畫（兩頁同時滑入/滑出）。觸控狀態機處理動畫期間的手勢追蹤，確保快速連續滑動不卡住。
- **`src/pages/clock_page.py`** — 數位/類比模式切換從單擊改為雙擊（400ms 內點兩下），避免與頁面滑動手勢衝突。
- **`src/main.py`** — WiFi 連線成功後建立頁面序列 `[ClockPage, WeatherPage]`，啟用滑動切換。

## 技術細節

### 非阻塞 HTTP
MicroPython 的 `urequests.get()` 是阻塞式，會凍結整個事件迴圈 1-3 秒。改用 `uasyncio.open_connection` 建立 TCP 連線，手動發送 HTTP/1.0 GET 請求並以 async stream 讀取回應，UI 在 HTTP 請求期間持續運作。使用 HTTP（port 80）而非 HTTPS 避免 SSL 握手阻塞。

### 滑動手勢狀態機
App 的觸控處理分為三個階段：
1. **觸控開始** — 記錄起始 X 座標
2. **觸控持續** — 持續追蹤最新 X 座標（`_touch_last_x`）
3. **觸控結束** — 計算 `_touch_last_x - _touch_start_x`，≥ 50px 為滑動，< 50px 為點擊

動畫期間仍追蹤觸控位置，動畫結束時若使用者正在觸控，立即記錄新的起始位置，確保連續滑動不遺失手勢。

### WMO Weather Code
Open-Meteo 回傳 WMO 標準天氣代碼（0-99），對應至文字描述和顏色（Clear/YELLOW、Rain/BLUE、Storm/RED 等）。
