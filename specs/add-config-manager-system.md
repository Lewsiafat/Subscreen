# 新增設定管理系統（Config Manager System）

- **分支:** `feat/add-config-manager-system`
- **日期:** 2026-02-24

## 描述
新增設定介面，提供參數管理和設定同步。使用者可在裝置螢幕上掃描 QR Code 進入網頁設定介面，透過大按鈕操作背光開關、重啟裝置、重置 WiFi 設定等功能。設定伺服器僅在 WiFi CONNECTED 狀態下啟動，不影響現有 AP_MODE provisioning 流程。

## 任務清單
- [x] 擴展 `config_manager.py`：新增通用設定區塊（backlight、timezone 等），支援讀寫設定項
- [x] 新增 `settings_server.py`：復用 `WebServer`，在 CONNECTED 狀態下提供設定 API（GET/POST 路由）
- [x] 新增 `templates/settings.html`：響應式網頁設定介面，大按鈕風格（背光開關、重啟、重置 WiFi）
- [x] 新增 `pages/settings_page.py`：裝置端設定頁面，繪製 QR Code 點陣圖 + 顯示 IP 位址
- [x] 修改 `main.py`：將 SettingsPage 加入頁面導航列表
- [x] 整合測試：確認 WiFi 連線後可掃描 QR Code 進入網頁、操作按鈕功能正常
