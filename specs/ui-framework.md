# UI Framework — 基礎顯示框架

- **分支:** `feat/ui-framework`
- **日期:** 2025-02-11

## 描述
建立基礎的 UI 顯示框架，讓後續功能頁面（天氣、行事曆、通知等）能快速開發。框架基於 Presto 240x240 觸控螢幕，採用 Page + Widget 架構，整合 PicoVector 向量繪圖，與現有 async WiFi 基礎設施共存。

### 核心設計

- **預設解析度:** 240x240（可透過 `full_res=True` 開啟 480x480，需搭配 `palette=True`）
- **架構:** App → Page → Widget 三層
- **繪圖:** PicoGraphics + PicoVector，支援向量字型
- **非同步:** render loop 使用 `uasyncio`，不阻塞背景任務
- **效能:** dirty flag 機制，僅在需要時重繪

### 檔案結構

```
src/ui/
  __init__.py       # 匯出主要類別
  app.py            # App — Presto 初始化、async render loop、Page 管理
  page.py           # Page 基類 — draw/update 生命週期
  widget.py         # Widget 基類 + 內建元件（Label, Button, Container）
  theme.py          # 顏色、字型大小、間距等統一定義
```

### Page API

```python
class Page:
    def __init__(self, app): ...
    def update(self):
        """邏輯更新（資料、狀態）"""
    def draw(self, display, vector, offset_x=0):
        """繪製畫面，offset_x 預留滑動換頁"""
    def on_enter(self): ...   # 頁面進入時
    def on_exit(self): ...    # 頁面離開時
```

### App API

```python
class App:
    def __init__(self, full_res=False): ...
    def set_screen(self, page): ...   # 切換頁面
    async def run(self, initial_page_class): ...  # 啟動主迴圈
```

### 內建 Widgets

- **Label** — 文字顯示（位置、顏色、字型大小）
- **Button** — 觸控按鈕（文字、按壓回呼、pressed 狀態視覺回饋）
- **Container** — 群組化子元件，可設背景色

### 不在此次範圍

- 滑動手勢 / 換頁動畫
- 複雜佈局引擎（使用絕對座標或簡單排列）
- 圖片 / JPEG 顯示
- 向量字型載入（先用內建字型，後續再加）

## 任務清單
- [x] 建立 `src/ui/` 目錄結構與 `__init__.py`
- [x] 實作 `theme.py` — 定義顏色常數、字型大小、間距
- [x] 實作 `widget.py` — Widget 基類 + Label, Button, Container
- [x] 實作 `page.py` — Page 基類，含 draw/update 生命週期與 widget 管理
- [x] 實作 `app.py` — App 類別，Presto 初始化、async render loop、Page 切換
- [x] 建立 `ui/__init__.py` 匯出公開 API
- [x] 更新 `main.py` — 整合 UI 框架，建立示範 HomePage
- [x] 在裝置上測試基本顯示與觸控互動
