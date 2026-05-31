# Enhance Pomodoro Alert — Walkthrough

- **分支:** `feat/enhance-pomodoro-alert`
- **日期:** 2026-05-31

## 變更摘要

讓番茄鐘在階段切換與整段結束時的提示更醒目：新增 `pomodoro_alert` 設定
（`off` / `normal` / `loud`，預設 `loud`），`loud` 模式同時閃爍 7 顆 RGB LED
並以壓電共振頻率（~3 kHz）掃頻蜂鳴，「讓大家都注意到」。提示強度可於 Web 設定頁
調整。

## 修改的檔案

- `src/config_manager.py` — `DEFAULT_SETTINGS` 新增 `"pomodoro_alert": "loud"`。
- `src/templates/settings.html` — Pomodoro 區塊新增 Alert 下拉選單（Off/Normal/
  Loud）；載入設定時回填 `pomodoro_alert`；`savePomodoro()` 一併送出。
- `src/pages/pomodoro_page.py` — 主要變更：
  - 新增 loud 提示常數 `_LOUD_FREQ=3000`、`_LOUD_FREQ_HI=3800`。
  - `__init__` 載入 `self._alert`、初始化 `self._alert_seq` 世代序號；`on_enter`
    重新讀取 `pomodoro_alert`（網頁端可能已變更）。
  - 改寫 `_signal_phase` / `_signal_done` 為三級提示。
  - 新增非阻塞協程 `_blink_leds(seq, color, times, on_ms, off_ms)` 與
    `_alarm(seq, cycles)`（共振頻率掃頻）。
  - `_stop_feedback` 遞增 `_alert_seq`，使在飛行中的閃爍/警報協程自行結束。

## 技術細節

- **硬體限制與「更大聲」策略**：Presto 蜂鳴器為壓電式，`Buzzer.set_tone()` 無音量
  參數，無法在軟體層提高振幅。壓電元件在共振峰（約 2.7–4 kHz）同驅動下聽感最大，
  故 `loud` 模式改用 3000↔3800 Hz 急促掃頻取代原 660–880 Hz，並搭配 LED 閃爍，
  以「更響亮 + 視覺」達成引人注意的效果。
- **三級行為**（階段切換與結束皆觸發）：
  - `off` — 僅設定穩定階段燈色，無聲。
  - `normal` — 維持原行為（880 Hz 單響 / 660 Hz 三響，靜態燈）。
  - `loud` — LED 閃爍（phase 6 次 / done 12 次）+ 掃頻警報（phase 4 輪 / done 8 輪）。
- **世代序號守護 `_alert_seq`**：閃爍與蜂鳴皆以 `asyncio.create_task` 背景執行；
  每次發出提示前遞增序號並傳入協程，協程每步比對 `seq != self._alert_seq` 即中止，
  確保使用者於提示進行中離開/重置頁面時不會殘留亮燈或誤動倒數迴圈的燈色。
- **`settings_server.py` 無需修改**：`_handle_set_settings` 對每個值先嘗試
  `float()`，失敗則保留原字串，故 `pomodoro_alert` 的字串值（off/normal/loud）
  本就正確儲存。
- **驗證**：host 端 `py_compile` 通過；裝置端 `mpremote exec` import 冒煙測試通過
  （模組可載入、`_blink_leds`/`_alarm` 與常數齊備）。實際聲光需於 Pomodoro 頁面
  手動觸發階段邊界確認。
