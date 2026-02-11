# Add Clock Page — Walkthrough

- **分支:** `feat/add-clock-page`
- **日期:** 2026-02-11

## 變更摘要
新增時鐘頁面（ClockPage），支援數位與類比兩種顯示模式。數位模式以大字體顯示時間與日期，搭配螢幕保護式漂移動畫；類比模式繪製完整錶面含指針、刻度與中央日期。點擊螢幕可線性滑動切換模式。WiFi 連線後自動透過 NTP 同步時間。

## 修改的檔案
- **`src/pages/clock_page.py`** (新增) — 時鐘頁面主體，包含 Digital/Analog 雙模式、NTP 同步、螢幕保護漂移、滑動切換動畫
- **`src/main.py`** (修改) — WiFi 連線後導航到 ClockPage（取代 DemoPage）
- **`src/pages/__init__.py`** (修改) — 匯出 ClockPage
- **`specs/add-clock-page.md`** (新增) — 任務規格文件

## 技術細節
- **雙模式架構:** `MODE_DIGITAL` / `MODE_ANALOG` 常數切換，draw() 根據模式分派不同繪製路徑
- **PicoVector 指針:** 使用 Polygon.path() 預建時/分/秒針形狀，搭配 Transform.rotate() 旋轉繪製；提供 display.line() 的 fallback 路徑
- **三角函數快取:** 預計算 60 格 sin/cos 查表，避免每幀重複計算
- **螢幕保護漂移:** 數位模式下文字塊以固定速度漂移，碰到邊界反彈，使用 `display.measure_text()` 精確計算邊界
- **線性滑動動畫:** 模式切換時每幀固定 20px 位移，約 400ms 完成過渡
- **觸控防抖:** 每幀遞減冷卻計數器（10 幀 ≈ 300ms），避免重複觸發
- **NTP 同步:** on_enter 時以 asyncio task 背景同步，失敗則 fallback 到系統時間
- **時區參數:** `tz_offset` 建構子參數（預設 UTC+8），為後續設定介面預留擴充
- **類比錶面中央日期:** 指針下方顯示 MM/DD 與星期（灰色小字）
