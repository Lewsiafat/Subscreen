# UI Framework — Walkthrough

- **分支:** `feat/ui-framework`
- **日期:** 2026-02-11

## 變更摘要
建立了 Subscreen 的基礎 UI 顯示框架，採用 App → Page → Widget 三層架構。框架基於 Presto 240x240 觸控螢幕，整合 PicoGraphics 與 PicoVector，使用 uasyncio render loop 與現有 WiFi 基礎設施共存。同時建立了 Hello World demo page 驗證框架功能，已在裝置上測試成功。

## 修改的檔案
- `src/ui/__init__.py` — UI 套件入口，匯出 App, Page, Label, Button, Container, theme
- `src/ui/app.py` — App 主程式，負責 Presto 初始化、async render loop、Page 切換管理
- `src/ui/page.py` — Page 基類，提供 draw/update 生命週期、widget 管理、觸控分發
- `src/ui/widget.py` — Widget 基類 + Label（文字）、Button（觸控按鈕）、Container（群組容器）
- `src/ui/theme.py` — 顏色常數、字型大小、間距等統一定義
- `src/pages/__init__.py` — Pages 套件入口
- `src/pages/demo_page.py` — Hello World 示範頁面，含標題、計數器按鈕、底部資訊列
- `src/main.py` — 更新為整合 UI 框架，啟動 DemoPage 作為初始畫面
- `specs/ui-framework.md` — 功能規格文件
- `.claude/skills/finish-task/` — 新增 finish-task skill（結束任務自動化流程）

## 技術細節
- **預設 240x240 解析度**：App 預設使用標準解析度，可透過 `full_res=True` 開啟 480x480（自動搭配 `palette=True` 節省記憶體）
- **PicoVector 可選整合**：App 初始化時嘗試載入 PicoVector，若不可用則 `vector` 為 None，不影響基本繪圖
- **Render loop**：每幀依序執行 touch.poll → page.update → page.draw → presto.update，預設 30fps
- **觸控處理**：Button 支援兩種模式 — 透過硬體 `touch.Button` 註冊或軟體座標判斷
- **Page 生命週期**：on_enter/on_exit hook 供頁面進出時初始化/清理，draw 支援 offset_x 預留滑動效果
- **Dirty flag**：Widget 基類內建 dirty 標記機制，供未來效能優化使用
