# AP Mode Page — AP 模式頁面

- **分支:** `feat/add-ap-mode-page`
- **日期:** 2026-02-11

## 描述
當 WiFi 進入 AP Mode 時，顯示 AP 連接資訊頁面（SSID、Password、IP），引導使用者連接設定。頁面路由由 main.py 透過 WiFiManager 事件系統驅動，降低頁面間耦合度。同時重構 SplashPage 移除跳轉邏輯。

## 任務清單
- [x] 建立 `src/pages/ap_mode_page.py` — 顯示 AP SSID / Password / IP 連接資訊
- [x] 簡化 `src/pages/splash_page.py` — 移除 `next_page_class` 和自動跳轉邏輯
- [x] 修改 `src/main.py` — 用 `wm.on()` 事件系統驅動頁面路由
- [x] 在裝置上測試 AP Mode 頁面顯示與頁面切換
