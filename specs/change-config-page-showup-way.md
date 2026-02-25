# 調整 Config 介面彈出方式：由左右滑動改為由下往上

- **分支:** `feat/change-config-page-showup-way`
- **日期:** 2026-02-25

## 描述

目前 Settings 頁面是水平頁面序列的最後一頁，用戶需一直左滑才能進入。
本任務將 Settings 改為「垂直 Overlay」模式：
- 從任何頁面往上滑 → Settings 由下往上彈出（覆蓋全螢幕）
- 在 Settings 頁面往下滑 → Settings 往下縮回
- Settings 不再出現在水平滑動序列中

### 動畫原理

```
彈出：_overlay_offset_y 從 240 動畫至 0
收起：_overlay_offset_y 從 0 動畫至 240

繪製順序（動畫中）：
  1. 先畫當前主頁面（display.clear() + 正常繪製）
  2. 再畫 overlay（從 offset_y 開始局部清背景 + widget y 偏移）
```

### 手勢判斷

- 水平 vs 垂直判斷：`|dy| > |dx|` 為垂直滑動
- 上滑（`dy < -SWIPE_THRESHOLD`）：彈出 overlay
- 下滑（`dy > SWIPE_THRESHOLD`）且 overlay 可見：收起 overlay

## 任務清單

- [x] `src/ui/widget.py` — 所有 `draw()` 加入 `offset_y=0` 參數，Label/Button/Container 的 y 座標套用偏移
- [x] `src/ui/page.py` — `draw()` / `_draw_background()` / `_draw_widgets()` 加入 `offset_y=0`；`offset_y > 0` 時改用 `display.rectangle(0, offset_y, w, h - offset_y)` 局部清背景
- [x] `src/ui/app.py` — 新增 overlay 狀態欄位（`_overlay_page`, `_overlay_offset_y`, `_overlay_animating`, `_overlay_direction`, `_overlay_visible`）
- [x] `src/ui/app.py` — 新增 Y 軸觸控追蹤（`_touch_start_y`, `_touch_last_y`）
- [x] `src/ui/app.py` — 修改 `_tick()` 的手勢偵測：判斷 H vs V 主軸，垂直上滑觸發 overlay，垂直下滑收起 overlay
- [x] `src/ui/app.py` — 新增 `set_overlay(page)` 方法
- [x] `src/ui/app.py` — 新增 `_update_overlay_animation()` 方法（每幀推進 `_overlay_offset_y`）
- [x] `src/ui/app.py` — 新增 `_draw_with_overlay()` 方法（先畫主頁面，再畫 overlay 於上層）
- [x] `src/pages/settings_page.py` — `draw()` 加入 `offset_y=0` 參數，傳遞至 `_draw_qr()`
- [x] `src/pages/settings_page.py` — `_draw_qr()` 加入 `offset_y=0`，`start_y` 套用偏移
- [x] `src/main.py` — 將 `settings_page` 從 `page_list` 移除，改為 `app.set_overlay(settings_page)`
