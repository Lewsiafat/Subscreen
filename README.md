# Subscreen

基於 [Pimoroni Presto](https://shop.pimoroni.com/products/presto) (RP2350) 的桌面副螢幕裝置。透過 240x240 觸控顯示器，在桌面上即時顯示各類資訊。

## 硬體需求

- **Pimoroni Presto** — RP2350 + 240x240 IPS 觸控螢幕、WiFi、7 RGB LEDs、加速度計、蜂鳴器、SD 卡槽
- USB-C 傳輸線（部署與供電）

## 功能特色

- **WiFi 自動管理** — 連線失敗自動重試，超過上限後進入 AP 模式
- **Captive Portal 設定** — AP 模式下透過手機瀏覽器設定 WiFi 密碼
- **觸控介面** — 支援觸控按鈕互動
- **Debug 儀表板** — 即時顯示 WiFi 狀態、設定、日誌（需 Pico Explorer）

## 快速開始

### 安裝工具

```bash
pip install mpremote
```

### 部署到裝置

將 Presto 透過 USB 連接電腦，然後：

```bash
# 使用 Claude Code skill
/deploy

# 或手動
mpremote cp -r src/ :
```

### 執行

```bash
# 使用 Claude Code skill
/run
```

## 專案結構

```
src/                    # 原始碼（部署至 Pico 根目錄）
  wifi_manager.py       # WiFi 狀態機核心
  provisioning.py       # Web 設定介面
  config_manager.py     # 設定檔管理
  web_server.py         # Async HTTP 伺服器
  dns_server.py         # Captive Portal DNS
  logger.py             # 日誌系統
  main.py               # 主程式進入點
  main_debug.py         # Debug 模式進入點
  templates/            # 設定頁面 HTML
ref_doc/                # 參考文件
specs/                  # 功能規格文件
```

## 技術架構

建立在 **Picore-W** WiFi 基礎設施之上，使用 MicroPython + `uasyncio` 非同步架構。

WiFi 生命週期：

```
IDLE → CONNECTING → CONNECTED（每 2 秒健康檢查）
                  ↘ FAIL → AP_MODE（Captive Portal 設定）
```
