# 新增股市行情與虛擬貨幣行情頁面

- **分支:** `feat/add-stock-cryptocurrency-price-display`
- **日期:** 2026-02-23

## 描述

在 Subscreen 新增一個 `MarketPage`，顯示加密貨幣（BTC/ETH via Binance）與股票（美股 SPY/AAPL、台股 ^TWII/2330.TW via Yahoo Finance）的即時行情，包含現價與漲跌幅（%）。顏色採西式風格：漲綠跌紅。

## API 規格

| 類型 | 來源 | 端點（HTTP） |
|------|------|-------------|
| 加密貨幣 | Binance Public API | `api.binance.com/api/v3/ticker/24hr?symbols=["BTCUSDT","ETHUSDT"]` |
| 美股 + 台股 | Yahoo Finance（非官方） | `query1.finance.yahoo.com/v7/finance/quote?symbols=SPY,AAPL,^TWII,2330.TW` |

刷新間隔：每 **5 分鐘**（300 秒）。

## UI 佈局（240x240）

```
[ Market            12:34 ]   ← 標題列（FONT_MEDIUM）
─────────────────────────────
 BTC    95,000  ▲ +1.25%      ← 綠色（GREEN）
 ETH     3,200  ▼ -0.52%      ← 紅色（RED）
─────────────────────────────
 SPY       512  ▲ +0.33%
 AAPL      195  ▲ +0.12%
 TWII   21,000  ▼ -0.18%
 2330      900  ▲ +0.88%
─────────────────────────────
[ Updated 12:34 ]             ← 狀態列（FONT_SMALL，DARK_GRAY）
```

- 每行：左側標的名稱、中間現價、右側漲跌幅（含方向箭頭）
- 顏色：漲幅 > 0 → 綠（GREEN），漲幅 < 0 → 紅（RED），0 → 白（WHITE）

## 任務清單

- [x] 建立 `src/pages/market_page.py` 基本架構（繼承 `Page`）
- [x] 實作 `_async_https_get` 工具函式（HTTPS + chunked encoding 支援）
- [x] 實作 Binance WebSocket 即時推送（BTC/ETH miniTicker，自動重連）
- [x] 實作 Stooq CSV API fetch（美股 + 台股，替代 Yahoo Finance）
- [x] 實作 `_update_display()` 繪製行情列表（名稱、價格、漲跌幅）
- [x] 實作漲跌顏色邏輯（綠漲紅跌，零為白，N/D 顯示 --）
- [x] 實作定時刷新機制（股票每 5 分鐘，WebSocket 即時）
- [x] 修改 `src/main.py`，將 `MarketPage` 加入頁面輪播清單
- [x] 部署到 Pico 測試 API 連線與顯示
