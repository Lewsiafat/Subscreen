"""Market Page — 加密貨幣（WebSocket 即時）+ 股票行情。"""

import gc
import ssl
import struct
import time
import json
import uos
import ubinascii
import uasyncio as asyncio
from ui.page import Page
from ui.widget import Label
from ui.theme import (
    WHITE, GREEN, RED, DARK_GRAY, GRAY,
    FONT_SMALL, FONT_MEDIUM,
)

# Binance WebSocket combined stream（即時推送，無需 API key）
_WS_HOST = "stream.binance.com"
_WS_PORT = 9443
_WS_PATH = (
    "/stream?streams="
    "btcusdt@miniTicker/ethusdt@miniTicker"
)

# Stooq CSV API（股票每日資料，市場收盤時顯示 --）
_STOOQ_HOST = "stooq.com"
_STOOQ_PATH = "/q/l/?s={}&f=sd2t2ohlcv&e=csv"
_STOCK_SYMBOLS = [
    ("SPY",  "spy"),
    ("AAPL", "aapl"),
    ("TWII", "%5etwii"),
    ("2330", "2330.tw"),
]

_STOCK_INTERVAL = 300   # 股票刷新間隔（5 分鐘）
_WS_PING_INTERVAL = 30  # WebSocket ping 間隔（秒）


# ---------------------------------------------------------------------------
# WebSocket 工具函式
# ---------------------------------------------------------------------------

async def _ws_recv_frame(reader):
    """讀取一個 WebSocket frame。

    Returns:
        (opcode, data) 或 None（連線關閉）。
    """
    header = await reader.read(2)
    if len(header) < 2:
        return None
    opcode = header[0] & 0x0F
    length = header[1] & 0x7F

    if length == 126:
        ext = await reader.read(2)
        length = struct.unpack(">H", ext)[0]
    elif length == 127:
        ext = await reader.read(8)
        length = struct.unpack(">Q", ext)[0]

    # Server→Client frames 不加 mask
    data = await reader.read(length)
    return opcode, data


async def _ws_send_frame(writer, opcode, data):
    """發送一個 WebSocket frame（Client→Server，需 mask）。"""
    mask_key = uos.urandom(4)
    payload = bytes(
        b ^ mask_key[i % 4] for i, b in enumerate(data)
    )
    length = len(payload)
    if length < 126:
        header = bytes([0x80 | opcode, 0x80 | length])
    else:
        header = bytes(
            [0x80 | opcode, 0x80 | 126]
        ) + struct.pack(">H", length)
    writer.write(header + mask_key + payload)
    await writer.drain()


# ---------------------------------------------------------------------------
# HTTPS 工具函式（Stooq 股票用）
# ---------------------------------------------------------------------------

async def _async_https_get(host, path):
    """非阻塞 HTTPS GET，支援 chunked encoding。

    Returns:
        回應 body 的 bytes。

    Raises:
        OSError: HTTP 狀態非 200。
    """
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.verify_mode = ssl.CERT_NONE
    reader, writer = await asyncio.open_connection(
        host, 443, ssl=ssl_ctx
    )
    request = (
        "GET {} HTTP/1.1\r\n"
        "Host: {}\r\n"
        "User-Agent: MicroPython/1.0\r\n"
        "Accept: */*\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, host)
    writer.write(request.encode())
    await writer.drain()

    status_line = await reader.readline()
    if b"200" not in status_line:
        writer.close()
        raise OSError("HTTP " + status_line.decode().strip())

    is_chunked = False
    while True:
        line = await reader.readline()
        if not line or line == b"\r\n":
            break
        if b"transfer-encoding: chunked" in line.lower():
            is_chunked = True

    if is_chunked:
        chunks = []
        while True:
            size_line = await reader.readline()
            try:
                size = int(size_line.strip(), 16)
            except Exception:
                break
            if size == 0:
                break
            chunks.append(await reader.read(size))
            await reader.read(2)
        body = b"".join(chunks)
    else:
        chunks = []
        while True:
            chunk = await reader.read(512)
            if not chunk:
                break
            chunks.append(chunk)
        body = b"".join(chunks)

    writer.close()
    await asyncio.sleep_ms(50)
    return body


async def _fetch_stooq(display_name, symbol):
    """取得 Stooq 股票報價（日資料）。

    Returns:
        (display_name, price, change_pct) 或 None。
    """
    try:
        body = await _async_https_get(
            _STOOQ_HOST, _STOOQ_PATH.format(symbol)
        )
        gc.collect()
        text = body.decode()
        lines = text.strip().split("\n")
        data_line = lines[-1].strip()
        vals = data_line.split(",")
        if len(vals) < 7:
            return None
        if "N/D" in vals:
            return (display_name, 0.0, 0.0)
        open_p = float(vals[3])
        close_p = float(vals[6])
        if open_p == 0:
            return (display_name, close_p, 0.0)
        change = (close_p - open_p) / open_p * 100
        return (display_name, close_p, change)
    except Exception as e:
        print("Stooq {} err: {}".format(symbol, e))
        return None


# ---------------------------------------------------------------------------
# MarketPage
# ---------------------------------------------------------------------------

class MarketPage(Page):
    """行情頁面：BTC/ETH WebSocket 即時 + 股票每日資料。

    Args:
        app: App 實例。
    """

    def __init__(self, app):
        super().__init__(app)

        # WebSocket 狀態
        self._ws_task = None
        self._ws_connected = False

        # 加密貨幣報價（WebSocket 更新）
        # {"BTCUSDT": (price, change_pct), ...}
        self._crypto_data = {}

        # 股票報價（HTTPS 輪詢）
        self._stock_data = []  # [(name, price, change), ...]
        self._stock_last_fetch = 0
        self._stock_fetching = False

        # 標題列
        self._title_label = Label(
            x=10, y=10, text="Market",
            color=WHITE, scale=FONT_MEDIUM,
        )
        self._time_label = Label(
            x=180, y=10, text="--:--",
            color=GRAY, scale=FONT_MEDIUM,
        )
        self.add(self._title_label)
        self.add(self._time_label)

        # 行情列（2 crypto + 4 stock = 6 列）
        self._row_labels = []
        start_y = 50
        row_h = 28
        for i in range(6):
            y = start_y + i * row_h
            sym_lbl = Label(
                x=10, y=y, text="",
                color=GRAY, scale=FONT_SMALL,
            )
            prc_lbl = Label(
                x=85, y=y, text="",
                color=WHITE, scale=FONT_SMALL,
            )
            chg_lbl = Label(
                x=165, y=y, text="",
                color=GRAY, scale=FONT_SMALL,
            )
            self.add(sym_lbl)
            self.add(prc_lbl)
            self.add(chg_lbl)
            self._row_labels.append((sym_lbl, prc_lbl, chg_lbl))

        # 狀態列
        self._status_label = Label(
            x=0, y=220, text="Connecting...",
            color=DARK_GRAY, scale=FONT_SMALL,
        )
        self.add(self._status_label)

    def on_enter(self):
        self._update_time()
        # 啟動 WebSocket（僅建立一次，背景持續運行）
        if self._ws_task is None:
            self._ws_task = asyncio.create_task(self._ws_run())
        # 觸發股票資料抓取
        if not self._stock_fetching:
            asyncio.create_task(self._fetch_stocks())

    def _update_time(self):
        lt = time.localtime()
        self._time_label.set_text(
            "{:02d}:{:02d}".format(lt[3], lt[4])
        )

    # --- WebSocket ---

    async def _ws_run(self):
        """WebSocket 背景 task，自動重連。"""
        while True:
            try:
                self._status_label.set_text("WS Connecting...")
                self._status_label.color = GRAY
                await self._ws_session()
            except Exception as e:
                print("WS err:", e)
            self._ws_connected = False
            self._status_label.set_text("WS Reconnecting...")
            self._status_label.color = RED
            gc.collect()
            await asyncio.sleep(5)

    async def _ws_session(self):
        """建立 WebSocket 連線並持續接收 frames。"""
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_ctx.verify_mode = ssl.CERT_NONE
        reader, writer = await asyncio.open_connection(
            _WS_HOST, _WS_PORT, ssl=ssl_ctx
        )

        # WebSocket HTTP Upgrade 握手
        key = ubinascii.b2a_base64(uos.urandom(16)).strip()
        handshake = (
            "GET {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: {}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).format(_WS_PATH, _WS_HOST, _WS_PORT, key.decode())
        writer.write(handshake.encode())
        await writer.drain()

        # 讀取握手回應 headers
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break

        self._ws_connected = True
        self._status_label.set_text("Live")
        self._status_label.color = GREEN

        last_ping = time.time()

        while True:
            # 定期發送 ping 保持連線
            now = time.time()
            if now - last_ping > _WS_PING_INTERVAL:
                await _ws_send_frame(writer, 0x9, b"ping")
                last_ping = now

            frame = await _ws_recv_frame(reader)
            if frame is None:
                break

            opcode, data = frame
            if opcode == 0x8:    # Close
                break
            elif opcode == 0xA:  # Pong（忽略）
                pass
            elif opcode == 0x9:  # Ping（回應 Pong）
                await _ws_send_frame(writer, 0xA, data)
            elif opcode == 0x1:  # Text frame
                self._on_ws_message(data)

        writer.close()

    def _on_ws_message(self, data):
        """處理 Binance miniTicker 推送。"""
        try:
            msg = json.loads(data)
            # Combined stream 格式：{"stream":..., "data":{...}}
            ticker = msg.get("data", msg)
            sym = ticker.get("s", "")
            close_p = float(ticker.get("c", 0))
            open_p = float(ticker.get("o", 0))
            if open_p > 0:
                change = (close_p - open_p) / open_p * 100
            else:
                change = 0.0
            self._crypto_data[sym] = (close_p, change)
            self._update_display()
        except Exception:
            pass

    # --- 股票輪詢 ---

    async def _fetch_stocks(self):
        """HTTPS 輪詢 Stooq 股票資料。"""
        now = time.time()
        if (self._stock_fetching
                or now - self._stock_last_fetch < _STOCK_INTERVAL):
            return
        self._stock_fetching = True
        new_data = []
        try:
            for name, sym in _STOCK_SYMBOLS:
                result = await _fetch_stooq(name, sym)
                if result:
                    new_data.append(result)
                await asyncio.sleep_ms(300)
                gc.collect()
            if new_data:
                self._stock_data = new_data
                self._stock_last_fetch = time.time()
                self._update_display()
        except Exception as e:
            print("Stock fetch err:", e)
        finally:
            self._stock_fetching = False
            gc.collect()

    # --- 顯示更新 ---

    def _update_display(self):
        """合併加密貨幣與股票資料，更新所有行情 widgets。"""
        rows = []
        for sym, display in (
            ("BTCUSDT", "BTC"),
            ("ETHUSDT", "ETH"),
        ):
            if sym in self._crypto_data:
                price, change = self._crypto_data[sym]
                rows.append((display, price, change))
            else:
                rows.append((display, 0.0, 0.0))

        for item in self._stock_data:
            rows.append(item)

        for i, (name, price, change) in enumerate(rows):
            if i >= len(self._row_labels):
                break
            sym_lbl, prc_lbl, chg_lbl = self._row_labels[i]
            sym_lbl.set_text(name[:6])

            if price == 0.0:
                prc_lbl.set_text("--")
                chg_lbl.set_text("--")
                chg_lbl.color = GRAY
            else:
                if price >= 10000:
                    prc_str = "{:.0f}".format(price)
                elif price >= 100:
                    prc_str = "{:.1f}".format(price)
                else:
                    prc_str = "{:.2f}".format(price)
                prc_lbl.set_text(prc_str)
                arrow = "+" if change >= 0 else ""
                chg_lbl.set_text("{}{:.2f}%".format(arrow, change))
                if change > 0:
                    chg_lbl.color = GREEN
                elif change < 0:
                    chg_lbl.color = RED
                else:
                    chg_lbl.color = WHITE

    def update(self):
        self._update_time()
        now = time.time()
        if (now - self._stock_last_fetch > _STOCK_INTERVAL
                and not self._stock_fetching
                and self._ws_task is not None):
            asyncio.create_task(self._fetch_stocks())

    def draw(self, display, vector, offset_x=0):
        self._draw_background(display)

        display.set_pen(display.create_pen(*DARK_GRAY))
        display.rectangle(10 + offset_x, 38, 220, 1)

        sw = display.measure_text(
            self._status_label.text, FONT_SMALL
        )
        self._status_label.x = (240 - sw) // 2

        self._draw_widgets(display, offset_x)
