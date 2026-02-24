# WiFi Setup 頁面新增 Reconnect / Reboot 按鈕 — Walkthrough

- **分支:** `feat/add-reboot-at-wifisetuppage`
- **日期:** 2026-02-24

## 變更摘要
在 ApModePage 中新增 Reconnect 和 Reboot 按鈕，當裝置有已存的 WiFi 設定但連線失敗進入 AP 模式時，使用者可透過觸控按鈕重啟裝置重新嘗試連線，無需手動拔插電源。

## 修改的檔案
- `src/pages/ap_mode_page.py` — 新增 ConfigManager 偵測已存設定，有設定時顯示 Reconnect / Reboot 按鈕，無設定時維持原有 "Waiting for setup..." 文字
- `specs/add-reboot-at-wifisetuppage.md` — 任務規格文件

## 技術細節
- 初版嘗試在 Reconnect 按鈕中直接呼叫 `wm.connect()` 做 in-process 重連，但測試發現從 AP 模式切回 STA 模式後，網路路由殘留且記憶體不足（EHOSTUNREACH / ENOMEM），導致後續所有 API 和 WebSocket 連線失敗
- 最終方案：Reconnect 和 Reboot 按鈕均透過 `machine.reset()` 重啟裝置，確保記憶體和網路介面完全重置，重啟後裝置自動讀取已存設定重新連線
- 首次設定（無已存設定）時維持原有畫面，不顯示按鈕
