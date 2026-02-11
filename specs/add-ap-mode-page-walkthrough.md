# AP Mode Page — Walkthrough

- **分支:** `feat/add-ap-mode-page`
- **日期:** 2026-02-11

## 變更摘要
新增 AP Mode 頁面，當 WiFi 連線失敗進入 AP 模式時顯示 SSID、Password、IP 等連接資訊。同時重構頁面路由架構，將跳轉邏輯從 SplashPage 移至 main.py，透過 WiFiManager 事件系統驅動，降低頁面間耦合度。

## 修改的檔案
- `src/pages/ap_mode_page.py` — **新增** AP Mode 頁面，顯示 WiFi Setup 標題、AP SSID/Password/IP 資訊與設定引導
- `src/pages/splash_page.py` — **修改** 移除 `next_page_class` 跳轉邏輯，改用 `ready` 旗標供外部查詢動畫完成狀態；修正 ready 條件改為「接近目標值」而非「接近 100%」
- `src/main.py` — **修改** 改用 `wm.on("connected")` 和 `wm.on("ap_mode_started")` 事件驅動頁面路由，等待 Splash 動畫完成後再切換
- `specs/add-ap-mode-page.md` — **新增** 功能規格文件

## 技術細節
- **事件驅動路由**：頁面切換由 main.py 集中管理，透過 WiFiManager 的 `on()` 事件系統觸發，SplashPage 和 ApModePage 互不知道彼此存在
- **非同步等待**：事件回呼中建立 async task，輪詢 `splash.ready` 確保動畫播放完畢再切換頁面
- **Ready 條件修正**：原先 `self._progress > 0.95` 在 AP Mode（目標 50%）時永遠不成立，改為 `abs(target - progress) < 0.02` 判斷進度條已接近目標值
- **AP 資訊來源**：透過 `wm.get_ap_config()` 取得 SSID、Password、IP，在 ApModePage 建構時一次性讀取
