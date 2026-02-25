# 改善天氣位置設定 UI：城市名稱搜尋取代手動輸入經緯度 — Walkthrough

- **分支:** `feat/improve-weather-config-ui`
- **日期:** 2026-02-25

## 變更摘要

在 Settings 的 Location 區塊加入城市名稱搜尋功能，使用 Open-Meteo Geocoding API 將城市名轉為經緯度，免去手動查詢和輸入的不便。同時在天氣頁面頂部顯示地點名稱，讓使用者知道目前看的是哪裡的天氣。另外修復了 Settings overlay 關閉後天氣頁面不即時更新的問題，並新增儲存成功的 UI 回饋。

## 修改的檔案

- **`src/templates/settings.html`** — 新增 City 搜尋框（text input + Search 按鈕）、搜尋結果下拉清單（CSS + JS）、`searchCity()` / `selectCity()` 函式；`saveLocation()` 一併儲存城市名稱（`weather_location`）；`loadSettings()` 載入時顯示已存的城市名；Save Location 成功後跳出綠色 dialog 告知操作說明
- **`src/pages/weather_page.py`** — 頂部加入 `_location_label`（y=2，FONT_SMALL，GRAY）顯示地點名稱；`on_enter()` 讀取 `weather_location` 設定；`_update_display()` 置中對齊地點文字；新增 `on_resume()` 覆寫以在 overlay 關閉後即時套用新設定
- **`src/ui/page.py`** — 新增 `on_resume()` 空方法（Page 基類 hook，overlay 關閉時通知底層頁面）
- **`src/ui/app.py`** — overlay 動畫收起完成後呼叫 `self._current_page.on_resume()`
- **`specs/improve-weather-config-ui.md`** — 任務規格文件

## 技術細節

### 城市搜尋（純前端）

搜尋完全在使用者瀏覽器執行，fetch 呼叫 Open-Meteo Geocoding API：

```
GET https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5&language=en&format=json
```

不需要 API key，也不消耗 Pico 的記憶體或網路資源。選取城市後，城市名存入 `weather_location`、經緯度存入 `weather_lat` / `weather_lon`，三個值一次 POST 到 `/api/settings`。

### weather_location 儲存

`settings_server.py` 的 `_handle_set_settings()` 已支援任意 key，無需修改後端，直接傳 `weather_location` 即可儲存到 `settings.json`。

### on_resume() hook 修復即時更新

**問題：** Settings overlay 關閉後底層天氣頁面的 `on_enter()` 不會再次呼叫，新設定無法即時反映。
**解法：** 在 `Page` 基類加入 `on_resume()` 空方法，`App._update_overlay_animation()` 在 overlay 完全收起時呼叫 `current_page.on_resume()`。`WeatherPage` 覆寫此方法，重新讀取 lat/lon 和 location name，若座標變更則重置 `_last_fetch = 0` 並立即觸發重新 fetch。

### Save Location 成功回饋

複用既有的 `confirm-overlay` dialog，新增 `location-saved` action type：綠色確認按鈕（`.btn-confirm.green`）、隱藏 Cancel 按鈕（`.btn-cancel.hidden`）、副標題說明需切回天氣頁面查看效果。
