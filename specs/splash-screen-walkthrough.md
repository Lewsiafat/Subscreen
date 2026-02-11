# Splash Screen — Walkthrough

- **分支:** `feat/splash-screen`
- **日期:** 2026-02-11

## 變更摘要
新增開機 Splash 畫面，顯示 "Subscreen" 品牌名稱、平滑進度條動畫、WiFi 連線狀態文字。進度條根據 WiFi 狀態設定目標值並以緩動動畫趨近，確保視覺流暢。畫面至少顯示 3 秒，WiFi 連線成功且動畫完成後自動跳轉至 DemoPage。

## 修改的檔案
- `src/pages/splash_page.py` — **新增** Splash 頁面，含品牌文字、進度條動畫、WiFi 狀態顯示、自動跳轉邏輯
- `src/main.py` — **修改** 掛載 `wm` 到 `app` 作為共享服務，初始頁面改為 SplashPage → DemoPage 流程
- `specs/splash-screen.md` — **新增** 功能規格文件

## 技術細節
- **平滑進度條**：使用 `diff * 0.08` 緩動公式，進度條逐幀趨近目標值而非直接跳變，即使 WiFi 瞬間連上也有流暢的動畫過渡
- **最少顯示時間**：從 `on_enter()` 開始計時，確保 Splash 至少展示 3 秒（`MIN_DISPLAY_MS = 3000`）
- **跳轉條件三重門檻**：WiFi 已連線 + 超過最少顯示時間 + 進度條 > 95%，三者同時滿足才跳轉
- **共享服務模式**：WiFiManager 透過 `app.wm` 掛載，不改動 App 建構子，所有 Page 可透過 `self.app.wm` 存取
- **Lambda 工廠**：`app.run()` 接受 callable，用 lambda 傳入 `next_page_class` 參數給 SplashPage
