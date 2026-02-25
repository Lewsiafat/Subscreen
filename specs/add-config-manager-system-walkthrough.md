# 新增設定管理系統（Config Manager System）— Walkthrough

- **分支:** `feat/add-config-manager-system`
- **日期:** 2026-02-25

## 變更摘要

新增完整的設定管理系統。使用者可在 Subscreen 裝置上滑動到最後一頁，掃描 QR Code 開啟手機網頁設定介面，即時調整背光亮度、環境光 LED、時區、天氣地區，並可重啟裝置或重置 WiFi。所有設定持久化到 `settings.json`，各頁面在進入時動態讀取最新值。

## 修改的檔案

### 新增

- `src/config_manager.py` *(擴充)* — 新增 `settings.json` 管理 API：`load_settings()`、`save_settings()`、`get_setting()`、`set_setting()`；預設設定包含 `backlight`、`timezone`、`weather_lat`、`weather_lon`、`ambient_leds`
- `src/settings_server.py` — 復用 `WebServer`，提供設定 Web API（GET/POST /api/settings、/api/backlight、/api/reboot、/api/reset-wifi）；套用設定後即時呼叫硬體 API
- `src/templates/settings.html` — 響應式深色主題設定網頁，包含背光滑桿、Ambient LED 切換、天氣地區 lat/lon 輸入、時區下拉（UTC-12~+14）、重啟/重置按鈕（帶二次確認）
- `src/pages/settings_page.py` — 裝置端設定頁面，使用 `uQR` 庫繪製 QR Code 點陣圖（白底黑模組），顯示 IP 位址；進入頁面時自動啟動 SettingsServer，離開時停止
- `src/uQR.py` — 第三方 MicroPython QR Code 庫（JASchilz/uQR），已修正 `import ure as re` 相容性

### 修改

- `src/main.py` — 加入 `ConfigManager` import；`on_connected` 時讀取 timezone/lat/lon/ambient_leds 傳入對應頁面，並呼叫 `auto_ambient_leds()`；加入 `SettingsPage` 到頁面導航序列
- `src/pages/clock_page.py` — `on_enter` 時從設定讀取最新 `timezone`，切換回時鐘頁面即更新時區
- `src/pages/weather_page.py` — `on_enter` 時讀取最新 `weather_lat`/`weather_lon`；若地區變更則清除快取強制重新抓取

## 技術細節

### 設定架構

設定以獨立的 `settings.json` 儲存（與 WiFi 設定的 `wifi_config.json` 分離），避免互相影響。`ConfigManager` 使用「預設值合併」策略：讀取時先 copy `DEFAULT_SETTINGS`，再 update 磁碟上的值，確保新增的 key 自動補入預設值，不需要遷移機制。

```python
DEFAULT_SETTINGS = {
    "backlight": 1.0,
    "timezone": 8,
    "weather_lat": 25.033,
    "weather_lon": 121.565,
    "ambient_leds": False,
}
```

### SettingsServer 設計

復用現有 `WebServer`（已有 route 系統和 async TCP 處理），不另起新框架。POST /api/settings 通用端點處理所有設定寫入，儲存後呼叫 `_apply_settings()` 即時套用到硬體（背光 + ambient LEDs）。地區和時區在下次進入對應頁面時生效，不需要重啟。

### QR Code 繪製

由於 Presto 沒有內建 QR Code 支援，引入 `uQR.py`（~1,300 行，支援 QR V1-40，完整 Reed-Solomon 實作）。使用 `display.rectangle()` 繪製每個黑色模組（4×4 px），整體置中於 240×240 螢幕。

### 動態設定讀取

各頁面採用「懶讀取」策略：設定只在 `on_enter` 時讀取一次（I/O），正常渲染幀不觸碰檔案系統。WeatherPage 額外比對新舊 lat/lon，變更時清零 `_last_fetch` 強制重新抓取。
