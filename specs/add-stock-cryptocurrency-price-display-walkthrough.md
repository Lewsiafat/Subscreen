# 新增股市行情與虛擬貨幣行情頁面 — Walkthrough

- **分支:** `feat/add-stock-cryptocurrency-price-display`
- **日期:** 2026-02-23

## 變更摘要

新增 `MarketPage` 頁面，顯示 BTC/ETH 加密貨幣即時行情（透過 Binance WebSocket 推送）與美股/台股報價（透過 Stooq CSV API 每 5 分鐘輪詢）。加密貨幣採用 WebSocket 持久連線，每秒接收推送更新；股票在市場收盤時顯示 `--`，開盤時顯示當日漲跌幅。

## 修改的檔案

- **`src/pages/market_page.py`**（新增）
  完整的行情頁面實作，包含 Binance WebSocket 即時連線、Stooq HTTPS 輪詢、chunked encoding 處理、漲跌顏色邏輯，以及自動重連機制。

- **`src/main.py`**（修改）
  在 `on_connected` 的頁面序列中加入 `MarketPage`，並新增對應的 import。

- **`specs/add-stock-cryptocurrency-price-display.md`**（新增）
  任務規格文件。

## 技術細節

### API 選型過程

原始規格使用 Binance REST API（HTTP）+ Yahoo Finance API（HTTP），實際部署後遭遇多次問題：

1. **chunked transfer encoding**：最初使用 HTTP/1.0 試圖避免，但部分 API 仍回傳 chunked body，導致 JSON parse 失敗。修正方式：在 `_async_https_get` 中偵測 `Transfer-Encoding: chunked` header，手動解碼 chunk size + data。

2. **HTTP 301 重定向**：Binance 和 Yahoo Finance 均已強制 HTTPS，HTTP port 80 的請求全部回傳 301。改為使用 `ssl.SSLContext(PROTOCOL_TLS_CLIENT)` + `asyncio.open_connection(host, 443, ssl=ssl_ctx)` 實現非阻塞 HTTPS。

3. **Yahoo Finance 401 Unauthorized**：Yahoo Finance v7 API 已要求 CSRF crumb 驗證，無法在嵌入式環境實作。改用 **Stooq CSV API**（`stooq.com`），免費、免金鑰，回傳純 CSV 格式，解析簡單。

4. **Stooq N/D**：市場收盤期間 Stooq 回傳 `N/D`，且 CSV 僅有一行（無 header）。修正為取 `lines[-1]` 作為資料行，並在 `N/D` 時回傳 `(name, 0.0, 0.0)`，顯示層判斷 `price == 0.0` 則顯示 `--`。

### Binance WebSocket 架構

改用 WebSocket 取代 REST API 輪詢，實現 BTC/ETH 即時報價推送：

- 連線端點：`wss://stream.binance.com:9443/stream?streams=btcusdt@miniTicker/ethusdt@miniTicker`
- WebSocket 握手：手動實作 HTTP Upgrade 請求（`Sec-WebSocket-Key` 使用 `uos.urandom(16)` + base64 編碼）
- Frame 解析：`_ws_recv_frame` 處理 opcode、payload length（含 16/64-bit 延伸）、server-to-client 無 mask
- Frame 發送：`_ws_send_frame` 發送 client-to-server frames（需加 4-byte random mask）
- 保活：每 30 秒發送 ping frame（opcode 0x9）
- 自動重連：`_ws_run` 在 `_ws_session` 拋出例外時等待 5 秒後重試

### 記憶體管理

RP2350 記憶體有限，多個 HTTPS 連線同時進行會導致 `[Errno 12] ENOMEM`。解決方式：
- 股票逐筆查詢（每筆間隔 300ms + `gc.collect()`）
- 每次 HTTPS fetch 完成後立即 `gc.collect()`
- WebSocket 採持久連線，避免重複 TLS 握手的記憶體開銷

### 狀態列

WebSocket 連線狀態顯示於頁面底部：
- `WS Connecting...`（灰）：正在建立連線
- `Live`（綠）：WebSocket 已連線，正在接收推送
- `WS Reconnecting...`（紅）：連線斷開，等待重連
