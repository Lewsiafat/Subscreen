# 改善天氣位置設定 UI：城市名稱搜尋取代手動輸入經緯度

- **分支:** `feat/improve-weather-config-ui`
- **日期:** 2026-02-25

## 描述

目前 Settings 頁面的 Location 區塊需要使用者手動輸入 Latitude 和 Longitude，非常不直覺。
本任務在 lat/lon 欄位上方加入城市搜尋框，使用 Open-Meteo Geocoding API 將城市名稱轉換為經緯度。
點選搜尋結果後自動填入 lat/lon，原有手動輸入欄位保留供進階用途。

### API

```
GET https://geocoding-api.open-meteo.com/v1/search?name={城市名}&count=5&language=en&format=json
```

回傳欄位：`results[].name`, `results[].country`, `results[].latitude`, `results[].longitude`, `results[].admin1`

### UI 設計

```
[ Location                              ]
  City: [ Taipei            ] [Search]
  ┌─────────────────────────────────────┐
  │ Taipei, Taiwan (25.047, 121.544)    │ ← 點選自動填入
  │ Tainan, Taiwan (22.999, 120.227)    │
  └─────────────────────────────────────┘
  Latitude:  [ 25.047      ]
  Longitude: [ 121.544     ]
  Applied when you return to the Weather page.
  [Save Location]
```

### 實作限制

- 僅修改 `src/templates/settings.html`（純前端，後端不動）
- Geocoding API 從使用者瀏覽器發出 fetch，不經過 Pico
- 搜尋結果以下拉清單顯示，點選後自動填入 lat/lon 並收起清單
- 搜尋無結果時顯示 "No results found"
- 搜尋中顯示 "Searching..." 狀態

## 任務清單

- [x] `src/templates/settings.html` — Location 區塊加入 City 搜尋欄位（text input + Search 按鈕）
- [x] `src/templates/settings.html` — 新增搜尋結果下拉清單的 CSS 樣式（`.search-results`、`.result-item`）
- [x] `src/templates/settings.html` — 實作 `searchCity()` 函式：fetch Open-Meteo Geocoding API，顯示結果清單
- [x] `src/templates/settings.html` — 實作 `selectCity(lat, lon)` 函式：點選結果後填入 lat/lon 並收起清單
- [x] `src/templates/settings.html` — 支援 Enter 鍵觸發搜尋（city input 的 `onkeydown`）
- [x] `src/templates/settings.html` — 搜尋中/無結果/錯誤等狀態的 UI 回饋
- [x] `src/templates/settings.html` — Save Location 成功後顯示說明 dialog（複用 confirm-overlay）
- [x] `src/templates/settings.html` — `loadSettings()` 載入已存城市名到 City 欄位
- [x] `src/pages/weather_page.py` — 頂部加入地點名稱 label，`on_enter()` 讀取並置中顯示
- [x] `src/pages/weather_page.py` — 新增 `on_resume()` 在 overlay 關閉後即時套用新設定
- [x] `src/ui/page.py` — 新增 `on_resume()` 基類 hook
- [x] `src/ui/app.py` — overlay 收起完成後呼叫 `current_page.on_resume()`
