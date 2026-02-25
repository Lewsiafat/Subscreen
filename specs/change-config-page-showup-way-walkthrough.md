# 調整 Config 介面彈出方式：由左右滑動改為由下往上 — Walkthrough

- **分支:** `feat/change-config-page-showup-way`
- **日期:** 2026-02-25

## 變更摘要

將 Settings 頁面從水平滑動序列的最後一頁，改為由下往上彈出的垂直 Overlay。使用者可從任何頁面往上滑呼叫 Settings，往下滑收起，水平左右滑動則維持原本的頁面切換行為，兩者互不干擾。

## 修改的檔案

- **`src/ui/widget.py`** — `Widget`、`Label`、`Button`、`Container` 的 `draw()` 加入 `offset_y=0` 參數，y 座標繪製時加上偏移量
- **`src/ui/page.py`** — `draw()` / `_draw_background()` / `_draw_widgets()` 加入 `offset_y=0`；當 `offset_y > 0` 時改用 `display.rectangle()` 局部清背景，保留下方主頁面畫面
- **`src/ui/app.py`** — 新增完整 overlay 系統：狀態欄位、`set_overlay()`、`_show_overlay()`、`_hide_overlay()`、`_update_overlay_animation()`；更新 `_tick()` 加入 Y 軸觸控追蹤與 H vs V 滑動方向判斷
- **`src/pages/settings_page.py`** — `draw()` 和 `_draw_qr()` 加入 `offset_y` 參數，QR code 繪製位置隨動畫偏移
- **`src/main.py`** — `SettingsPage` 從 `page_list` 移除，改用 `app.set_overlay(settings_page)` 註冊為 overlay
- **`specs/change-config-page-showup-way.md`** — 任務規格文件

## 技術細節

### Overlay 動畫系統（app.py）

新增五個狀態欄位管理 overlay 生命週期：

```python
self._overlay_page = None
self._overlay_visible = False
self._overlay_offset_y = 240.0   # 240=隱藏, 0=完全可見
self._overlay_animating = False
self._overlay_direction = 0      # -1=彈出, +1=收起
```

每幀 `_update_overlay_animation()` 以 `_SWIPE_ANIM_SPEED`（20px/frame）推進 `_overlay_offset_y`，動畫完成後更新 `_overlay_visible` 並觸發 `on_enter()` / `on_exit()`。

### 手勢方向判斷

觸控結束時計算 `dx` 和 `dy`，以 `|dy| > |dx|` 決定主軸：

- 垂直主軸：上滑（`dy < -50`）→ `_show_overlay()`；下滑（`dy > 50`）→ `_hide_overlay()`
- 水平主軸：僅在 overlay 未顯示時才執行頁面左右切換

### 繪製順序（動畫中）

動畫進行時，每幀先畫主頁面（`display.clear()` 完整清除），再畫 overlay（以 `offset_y` 局部清背景並偏移 widgets），確保視覺上 overlay 從螢幕下方滑入。

### offset_y 對 background 的影響

`Page._draw_background()` 根據 `offset_y` 決定清除策略：

```python
if offset_y > 0:
    display.rectangle(0, offset_y, 240, 240 - offset_y)
else:
    display.clear()
```

當 `offset_y > 0`（overlay 部分遮蓋時），只清局部區域，避免蓋掉已繪製的主頁面。
