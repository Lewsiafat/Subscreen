# Add Clock Page — 時鐘頁面

- **分支:** `feat/add-clock-page`
- **日期:** 2026-02-11

## 描述
新增時鐘頁面，支援數位（Digital）和類比（Analog）兩種顯示模式，點擊螢幕可切換模式。WiFi 連線後透過 NTP 同步時間，時區保留參數可配置（預設 UTC+8）。類比時鐘秒針採逐秒跳動風格。

## 任務清單
- [x] 建立 `src/pages/clock_page.py` 頁面骨架，繼承 Page 基底類別
- [x] 實作 NTP 時間同步（使用 `ntptime` 模組），含時區偏移參數
- [x] 實作 Digital Clock 模式：大字體時間顯示（HH:MM:SS）+ 日期與星期
- [x] 實作 Analog Clock 模式：圓形錶面、時/分/秒針、刻度標記（使用 PicoVector）
- [x] 實作點擊螢幕切換模式的互動邏輯
- [x] 實作模式切換時的滑動過渡動畫（利用 offset_x 機制）
- [x] 修改 `src/main.py`，WiFi 連線後導航到 ClockPage（取代 DemoPage）
- [x] 更新 `src/pages/__init__.py` 匯出 ClockPage
