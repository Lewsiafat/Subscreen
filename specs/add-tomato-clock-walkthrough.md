# Tomato Clock (Pomodoro) — Walkthrough

- **分支:** `add-tomato-clock`
- **日期:** 2026-05-30

## 變更摘要

新增「番茄鐘」Pomodoro 頁面，循環 Work → Break 直到可設定的總時長結束，
每個階段邊界以蜂鳴器 + RGB LED 回饋。支援總時長（total）與工作/休息間隔
（work/break interval）三項控制，可在頁面 IDLE 狀態就地調整，亦可由 Web
設定頁預設。

## 修改的檔案

- `src/pages/pomodoro_page.py` — **新增** (422 行)。`PomodoroPage`：IDLE 狀態用
  `[-]/[+]` 調整 work/break/total 並按 START；運行中倒數搭配進度環，點擊任意
  處暫停/恢復；DONE 後 RESET 歸零。階段切換時觸發蜂鳴器與 LED 訊號。
- `src/main.py` — 在事件驅動頁面建構器註冊 `"pomodoro"` → `PomodoroPage(app)`。
- `src/settings_server.py` — `_AVAILABLE_PAGES` 加入 `"pomodoro"`，使其可在
  `/api/pages` 啟用/排序。
- `src/config_manager.py` — `DEFAULT_SETTINGS` 新增 `pomodoro_work` (25)、
  `pomodoro_break` (5)、`pomodoro_total` (120)。
- `src/templates/settings.html` — 新增 Pomodoro 設定區塊（work/break/total 數值
  輸入 + Save 按鈕）、`savePomodoro()` 透過 `/api/settings` 儲存、`PAGE_NAMES`
  加入 `pomodoro: 'Pomodoro'` 標籤。

## 技術細節

- **三項可調值** 來源優先序：頁面開啟時從 `ConfigManager` 載入
  `pomodoro_work / break / total` 作為初值；IDLE 狀態的 `[-]/[+]` 可即時覆寫，
  範圍受 `_WORK_BOUNDS=(1,90,5)`、`_BREAK_BOUNDS=(0,30,1)`、
  `_TOTAL_BOUNDS=(5,480,15)` 限制。
- **階段狀態機**：`PHASE_IDLE / WORK / BREAK / DONE`。維護 `_phase_remaining`
  （當前階段剩餘秒）與 `_total_remaining`（整段剩餘秒）雙計時，總時長耗盡即進入
  DONE，避免最後一個 work/break 區段超出總時長。
- **硬體回饋**：蜂鳴器以 `from presto import Buzzer`（GPIO 43）取得，於非 Presto
  環境（如 main_debug）以 `try/except` 退化為 `None`，不影響邏輯。
- **進度環** 預先建立 60 格 sin 表避免每幀重算三角函數，符合 RP2350 記憶體與
  效能約束。
- **顏色**：work 用番茄紅 `TOMATO=(255,99,71)`，break 用主題 `GREEN`。
- 設定區塊 hint 標明「Applied when you open the Pomodoro page」——設定僅在下次
  開啟頁面時套用為初值，運行中以頁面內就地控制為準。
