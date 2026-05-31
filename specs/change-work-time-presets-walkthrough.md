# Work Time Presets (10/15/30/45) — Walkthrough

- **分支:** `main`（小型變更，直接於 main 進行）
- **日期:** 2026-05-31

## 變更摘要

將番茄鐘「工作時長」從 1–90 分（step 5）改為固定預設清單 **10 / 15 / 30 / 45 分**，
裝置端 `−`/`+` 在這四個值間切換（兩端 clamp），Web 設定頁的 Work 欄位也改為對應
下拉選單。舊存檔的非預設值會在載入時自動對齊到最接近的預設。

## 修改的檔案

- `src/pages/pomodoro_page.py`
  - 新增 `_WORK_PRESETS = (10, 15, 30, 45)`，移除原 `_WORK_BOUNDS`。
  - `_adjust` 的 work 分支改為走預設清單索引（clamp 於 0..len-1）。
  - 新增 `_work_index()`（找最接近的預設索引）與 `_snap_work()`（對齊到預設）。
  - `__init__` 與 `on_enter` 載入 work 後呼叫 `_snap_work()`。
- `src/config_manager.py` — `DEFAULT_SETTINGS["pomodoro_work"]` 由 25 改為 30
  （25 不在預設清單內）。
- `src/templates/settings.html` — Work 由 number input 改為 `<select>`（10/15/30/45）；
  載入時若儲存值非預設則回退為 30，避免 select 無選取。

## 技術細節

- **為何用「對齊」而非直接拒絕舊值**：work 設定可能來自舊版本或 Web 端任意輸入，
  `_snap_work()` 以最小距離挑選最接近的預設，確保 UI 永遠顯示合法預設值，`−`/`+`
  行為可預期。
- **Clamp 而非 wrap**：與 break/total 既有的範圍 clamp 行為一致（使用者選擇）。
- **break/total 不變**：仍使用 `_BREAK_BOUNDS` / `_TOTAL_BOUNDS` 範圍式調整。
- **裝置端驗證**：`mpremote exec` 確認 snap（1→10, 13→15, 25→30, 100→45）與
  clamp（+ 自 10：10→15→30→45→45；− 自 45：45→30→15→10→10）皆正確。

## 備註

- 本次「番茄鐘在 BREAK 凍結」問題經查為裝置殘留舊版檔案（`ui_framework.py`、
  `pages.py`、巢狀 `src/` 等）造成，已清空裝置檔案系統（保留 `wifi_config.json`、
  `settings.json`）並重新部署解決，**無原始碼變更**。
