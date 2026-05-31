# Enhance Pomodoro Alert — 更醒目的番茄鐘提示

- **分支:** `feat/enhance-pomodoro-alert`
- **日期:** 2026-05-31

## 描述

讓番茄鐘在階段切換（Work ↔ Break）與整段結束時的提示更醒目，「讓大家都注意到」：
同時強化蜂鳴器與閃爍 7 顆 RGB LED。新增 `pomodoro_alert` 設定（`off` / `normal`
/ `loud`），可在 Web 設定頁調整提示強度，預設 `loud`。

硬體限制：Presto 蜂鳴器為壓電式，`Buzzer.set_tone()` 無音量參數。因此「更大聲」
透過 (1) 將頻率提高到壓電共振峰（約 3 kHz，同驅動下聽感最大）、(2) 採用警報式
連續/掃頻節奏 來達成，而非實際提高振幅。

## 任務清單

- [x] `config_manager.py`：`DEFAULT_SETTINGS` 新增 `"pomodoro_alert": "loud"`
      （值域 `off` / `normal` / `loud`）。
- [x] `settings_server.py`：確認 `_handle_set_settings` 能正確儲存字串型設定值。
      現行 `float()` 轉換失敗即保留原字串，故 **無需修改**。
- [x] `templates/settings.html`：Pomodoro 區塊新增 Alert 下拉選單（Off / Normal /
      Loud），載入時回填、`savePomodoro()` 一併送出 `pomodoro_alert`。
- [x] `pomodoro_page.py`：`__init__` 載入 `self._alert =
      ConfigManager.get_setting("pomodoro_alert", "loud")`，並於 `on_enter` 重載。
- [x] `pomodoro_page.py`：新增 loud 提示常數（共振頻率 `_LOUD_FREQ = 3000`、
      `_LOUD_FREQ_HI = 3800`），保留 normal 為現行 880/660 Hz 行為。
- [x] `pomodoro_page.py`：新增 `_blink_leds(seq, color, times, on_ms, off_ms)` 非阻塞
      協程，閃爍 7 顆 LED 後還原為當前階段色。
- [x] `pomodoro_page.py`：改寫 `_signal_phase` / `_signal_done`，依 `self._alert`
      分級：`off` 無提示；`normal` 現行行為；`loud` LED 閃爍 + 警報式掃頻蜂鳴。
- [x] 以 `_alert_seq` 世代序號守護：閃爍/蜂鳴皆為 `asyncio.create_task` 非阻塞，
      頁面重置/離開時遞增序號使在飛行中的協程自行結束並還原 LED 狀態。
- [x] `/deploy` 到 Pico；裝置端 import 冒煙測試通過（helpers/常數齊備）。
      三種模式的實機聲光表現需於 Pomodoro 頁面手動觸發階段邊界驗證。
