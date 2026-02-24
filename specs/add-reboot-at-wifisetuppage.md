# WiFi Setup 頁面新增 Reconnect / Reboot 按鈕

- **分支:** `feat/add-reboot-at-wifisetuppage`
- **日期:** 2026-02-24

## 描述
在 WiFi setup 設定頁面 (ApModePage) 中，當設定檔案存在但連接不上 WiFi 時，增加 Reconnect 和 Reboot 按鈕，讓使用者可以透過觸控螢幕重新嘗試連線或重啟裝置，而不用拔電源重新啟動。

## 任務清單
- [x] 修改 `ap_mode_page.py`：使用 ConfigManager 偵測是否有已存 WiFi 設定
- [x] 有設定時顯示 Reconnect 和 Reboot 按鈕，無設定時維持原有畫面
- [x] Reconnect 按鈕：透過 `machine.reset()` 重啟裝置重新連線
- [x] Reboot 按鈕：透過 `machine.reset()` 重啟裝置
- [x] 清理 `main.py`：移除不需要的 state_change 監聽器
- [x] 部署測試驗證功能正常
