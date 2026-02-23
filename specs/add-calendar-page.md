# 新增日曆頁面 (Calendar Page)

- **分支:** `feat/add-calendar-page`
- **日期:** 2026-02-23

## 描述

在 Subscreen 中新增一個月曆頁面，使用 `time.localtime()` 顯示當月月曆。
頁面無需網路，今日日期以高亮色塊標示，支援左右觸控切換月份。
新頁面加入主頁面序列（Clock → Weather → Calendar），可左右滑動切換。

## 版面配置（240×240）

```
┌─────────────────────────┐
│   <   February 2026  >  │  ← 35px：月份標題 + 左右切換觸控區
│ Mo Tu We Th Fr Sa Su   │  ← 22px：星期標題列
├─────────────────────────┤
│  2  3  4  5  6  7  8   │
│  9 10 11 12 13 14 15   │  ← 月曆格（最多 6 列）
│ 16 17 18 19 20 21 22   │     今日以 PRIMARY 色方框標示
│ 23 24 25 26 27 28       │
└─────────────────────────┘
```

## 技術細節

- 繼承 `Page` 基類，不使用 Label widgets，直接呼叫 `display.text()` 和 `display.rectangle()` 繪製
- 以 `time.localtime()` 取得今日日期；以 `time.mktime()` 計算月份第一天是星期幾
- 觸控左側 1/3 → 上個月，觸控右側 1/3 → 下個月（覆寫 `handle_touch()`）
- `update()` 每分鐘檢查日期是否跨天，如有則重繪

## 任務清單

- [x] 建立 `src/pages/calendar_page.py`，實作 `CalendarPage` 類別
- [x] 實作月曆格繪製邏輯：計算月份第一天星期幾、每月天數、6×7 格線
- [x] 今日日期高亮（`PRIMARY` 色方框），週末以不同顏色區分（`CYAN`）
- [x] 標題列顯示月份和年份，左右各設觸控熱區切換月份
- [x] 覆寫 `handle_touch()` 處理左右切換月份觸控
- [x] 覆寫 `update()` 偵測日期跨天自動重繪
- [x] 修改 `src/main.py`，在 `on_connected` 頁面序列中加入 `CalendarPage`
