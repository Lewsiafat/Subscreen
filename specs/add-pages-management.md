# Add Pages Management

- **分支:** `feat/add-pages-management`
- **日期:** 2026-02-25

## 描述

透過 Web UI 設定介面，讓使用者決定哪些頁面要啟用，以及頁面的顯示順序。
可管理的頁面：Clock、Weather、Calendar、Market。
SettingsPage 永遠固定在最後，不可移除或移動。

## 設計細節

### 資料格式

`settings.json` 中新增 `pages` 欄位，儲存已啟用頁面的有序清單：

```json
{
  "pages": ["clock", "weather", "calendar"]
}
```

- 陣列順序 = 裝置上的滑動順序
- 不在陣列中的頁面 = 停用
- 預設值：`["clock", "weather", "calendar"]`（market 預設停用）

### Page Registry（main.py）

```python
PAGE_REGISTRY = {
    "clock": ClockPage,
    "weather": WeatherPage,
    "calendar": CalendarPage,
    "market": MarketPage,
}
```

### API 端點（settings_server.py）

| 路由 | 方法 | 說明 |
|------|------|------|
| `/api/pages` | GET | 回傳可用頁面清單與目前設定 |
| `/api/pages` | POST | 儲存新的頁面順序 |

GET 回應格式：
```json
{
  "available": ["clock", "weather", "calendar", "market"],
  "enabled": ["clock", "weather", "calendar"]
}
```

POST body（URL-encoded）：
```
pages=clock%2Cweather%2Ccalendar%2Cmarket
```

### Web UI（settings.html）

Pages 管理區塊：
- 每行顯示：`[checkbox] 頁面名稱 [▲][▼]`
- 未啟用頁面排在清單最下方
- 底部固定顯示「Settings — always last」提示
- 「Save Pages」按鈕儲存設定

## 任務清單

- [ ] 在 `config_manager.py` 的 `DEFAULT_SETTINGS` 加入 `"pages": ["clock", "weather", "calendar"]`
- [ ] 在 `settings_server.py` 加入 `GET /api/pages` 路由，回傳可用頁面與目前啟用清單
- [ ] 在 `settings_server.py` 加入 `POST /api/pages` 路由，驗證並儲存頁面順序
- [ ] 在 `main.py` 加入 `PAGE_REGISTRY` 字典
- [ ] 修改 `main.py` 的 `on_connected()` 改為從設定動態載入頁面，並固定在最後加入 `SettingsPage`
- [ ] 在 `settings.html` 加入 Pages 管理區塊（checkbox + ▲▼ 按鈕 + Save 按鈕）
- [ ] 在 `settings.html` 加入 `/api/pages` 的 GET（載入設定）與 POST（儲存設定）JavaScript 邏輯
