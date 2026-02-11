# Splash Screen — 開機畫面

- **分支:** `feat/splash-screen`
- **日期:** 2026-02-11

## 描述
新增開機畫面，在 WiFi 連線前呈現品牌名稱與 loading 進度條動畫，即時顯示 WiFi 連線狀態。連線成功後自動跳轉至主頁面。字體簡潔大方，不過大。

## 任務清單
- [x] 建立 `src/pages/splash_page.py` — Splash 畫面含進度條與狀態文字
- [x] 更新 `src/main.py` — 掛載 wm 到 app，初始頁面改為 SplashPage
- [x] 在裝置上測試開機流程與自動跳轉
