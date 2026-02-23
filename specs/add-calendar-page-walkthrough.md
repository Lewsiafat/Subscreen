# 新增日曆頁面 (Calendar Page) — Walkthrough

- **分支:** `feat/add-calendar-page`
- **日期:** 2026-02-23

## 變更摘要

新增 `CalendarPage` 頁面，顯示當月月曆並支援左右觸控切換月份。頁面完全離線運作，以 `time.localtime()` 取得今日日期，今日以 PRIMARY 藍色方框高亮。將頁面加入主頁面序列（Clock → Weather → Calendar），可左右滑動切換。

## 修改的檔案

- **`src/pages/calendar_page.py`**（新增）— CalendarPage 主體，包含月曆格繪製、觸控月份切換、跨天偵測邏輯
- **`src/main.py`**（修改）— 加入 CalendarPage import，並在 `on_connected` 的頁面序列末端加入 `calendar` 實例

## 技術細節

### 版面配置

頁面分為三區（240×240）：

| 區域 | y 範圍 | 高度 | 說明 |
|---|---|---|---|
| Header | 0–34 | 35px | 深灰底，顯示 `< February 2026 >` |
| 星期列 | 35–56 | 22px | 深灰底，Mo–Fr 灰色，Sa–Su 青色 |
| 月曆格 | 57–236 | 180px | 最多 6 列 × 7 欄，每格 34×30px |

欄寬 `_COL_W = 34`（34×7=238，保留 2px 邊界），列高 `_ROW_H = 30`（30×6=180）。

### 月曆計算

- `_first_weekday(year, month)`：以 `time.mktime()` 求月份第一天的星期（0=Monday）
- `_days_in_month(year, month)`：純數學計算，含閏年判斷（無需外部模組）
- 繪製時以 `first_wd` 作為起始欄，每填滿 7 格換行

### 今日高亮

以 `display.rectangle()` 在格子內繪製 PRIMARY 色填滿方框（留 2px 內縮），再以白色文字覆蓋日期數字。

### 觸控處理

`handle_touch(tx, ty)` 中：
- `tx < w // 3`（左 1/3）→ 上個月
- `tx > w * 2 // 3`（右 1/3）→ 下個月
- 中間 1/3 不消費，交由 App 的滑動手勢偵測處理

不覆寫 `on_enter` 的重置是刻意設計：每次進入頁面都回到當月，方便查看今日。

### 時區

透過 `tz_offset=8`（UTC+8）調整 `time.time()` 後再轉換，與 ClockPage 保持一致。
