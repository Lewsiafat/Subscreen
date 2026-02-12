# 新增天氣頁面（即時天氣 + 多日預報）

- **分支:** `feat/add-weather-page`
- **日期:** 2025-02-12

## 描述
新增天氣頁面，透過 Open-Meteo API（免費、無需 API key）取得即時天氣資訊（溫度、濕度、天氣狀況）和 4 日天氣預報，顯示在 240x240 螢幕上。頁面間透過左右滑動手勢切換（時鐘 ↔ 天氣）。經緯度先硬編碼台北預設值。

## 任務清單
- [x] 建立 `src/pages/weather_page.py` — 天氣頁面主體
  - [x] 繼承 Page，實作 lifecycle（on_enter, update, draw, on_exit）
  - [x] 上半部：即時天氣（天氣符號 + 大字溫度 + 濕度/風速）
  - [x] 下半部：4 日預報（橫向排列，日期 + 天氣符號 + 高低溫）
  - [x] Open-Meteo API 整合（async fetch，10~15 分鐘自動刷新）
  - [x] WMO weather code 對應文字符號
  - [x] 無資料/錯誤狀態的 UI 處理
- [x] 實作左右滑動手勢切換頁面
  - [x] 在 Page 或 App 層級加入滑動偵測邏輯
  - [x] 時鐘頁 ↔ 天氣頁 雙向切換
- [x] 修改 `src/main.py` — 註冊天氣頁面到頁面序列中
