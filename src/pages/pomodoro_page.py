"""Pomodoro Page — 番茄鐘，支援總時長與工作/休息間隔控制。

Tomato clock with total-session control and work/break interval control.
Cycles Work → Break → Work … until the total session time elapses,
giving buzzer + RGB LED feedback at each boundary.
"""

import math
import time
import uasyncio as asyncio
from config_manager import ConfigManager
from ui.page import Page
from ui.widget import Label, Button
from ui.theme import (
    WHITE, GRAY, GREEN, DARK_GRAY,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE,
)

# 階段常數 / Phase constants
PHASE_IDLE = 0
PHASE_WORK = 1
PHASE_BREAK = 2
PHASE_DONE = 3

# 番茄紅 / Tomato red (work), 葉綠 / leaf green is theme GREEN (break)
TOMATO = (255, 99, 71)

# 蜂鳴器接腳 / Buzzer GPIO pin
_BUZZER_PIN = 43

# 工作時長預設清單（分）/ Work duration presets — -/+ steps through these
_WORK_PRESETS = (10, 15, 30, 45)
# 設定範圍 (min, max, step) / Setting bounds（break/total 仍用範圍）
_BREAK_BOUNDS = (0, 30, 1)
_TOTAL_BOUNDS = (5, 480, 15)

# 響亮提示參數 / Loud-alert tuning. 壓電蜂鳴器在共振峰附近聽感最大，
# 故 loud 模式用 ~3kHz 掃頻而非低頻，以「更大聲」引起注意。
_LOUD_FREQ = 3000
_LOUD_FREQ_HI = 3800


class PomodoroPage(Page):
    """番茄鐘頁面。

    IDLE 狀態用 [-]/[+] 調整工作/休息/總時長並按 START 開始；
    運行中點擊任意處暫停/恢復，DONE 後按 RESET 歸零。

    Args:
        app: App 實例。
    """

    def __init__(self, app):
        super().__init__(app)
        # 從設定載入三個可調值 / Load the three editable values
        self._work_min = ConfigManager.get_setting("pomodoro_work", 30)
        self._break_min = ConfigManager.get_setting("pomodoro_break", 5)
        self._total_min = ConfigManager.get_setting("pomodoro_total", 120)
        self._snap_work()  # 對齊到預設清單
        # 提示強度 off/normal/loud / Alert intensity
        self._alert = ConfigManager.get_setting("pomodoro_alert", "loud")
        # 提示世代序號：切換頁面/重置時遞增，讓進行中的閃爍/警報協程自行結束
        self._alert_seq = 0

        # 計時狀態 / Timer state
        self._phase = PHASE_IDLE
        self._paused = False
        self._phase_remaining = 0.0   # 當前階段剩餘秒數
        self._total_remaining = 0.0   # 整段剩餘秒數
        self._round = 0               # 已完成的工作回合數
        self._last_tick_ms = 0

        # 蜂鳴器（非 Presto 環境時為 None）
        try:
            from presto import Buzzer
            self._buzzer = Buzzer(_BUZZER_PIN)
        except Exception:
            self._buzzer = None

        # 進度環三角函數表 / Progress-ring trig table（60 格）
        self._sin_table = []
        self._cos_table = []
        for i in range(60):
            angle = math.radians(i * 6 - 90)
            self._sin_table.append(math.sin(angle))
            self._cos_table.append(math.cos(angle))

        # --- 編輯群組 widgets（IDLE 時可見）---
        self._edit_widgets = []
        self._work_val = self._build_edit_row(
            "Work", 70, lambda: self._adjust("work", -1),
            lambda: self._adjust("work", 1),
        )
        self._break_val = self._build_edit_row(
            "Break", 105, lambda: self._adjust("break", -1),
            lambda: self._adjust("break", 1),
        )
        self._total_val = self._build_edit_row(
            "Total", 140, lambda: self._adjust("total", -1),
            lambda: self._adjust("total", 1),
        )
        self._start_btn = Button(
            x=70, y=185, w=100, h=42, text="START",
            on_press=self._start,
        )
        self.add(self._start_btn)
        self._edit_widgets.append(self._start_btn)

        # --- 運行群組 widgets（運行/DONE 時可見）---
        self._reset_btn = Button(
            x=85, y=195, w=70, h=34, text="RESET",
            bg=DARK_GRAY, scale=FONT_SMALL,
            on_press=self._reset,
        )
        self.add(self._reset_btn)

        self._refresh_edit_labels()
        self._apply_visibility()

    def _build_edit_row(self, label_text, y, on_minus, on_plus):
        """建立一列「label [-] value [+]」編輯控制，回傳 value Label。"""
        lbl = Label(
            x=20, y=y + 8, text=label_text,
            color=GRAY, scale=FONT_MEDIUM,
        )
        minus = Button(
            x=95, y=y, w=34, h=30, text="-",
            on_press=on_minus,
        )
        val = Label(
            x=137, y=y + 8, text="", color=WHITE, scale=FONT_MEDIUM,
        )
        plus = Button(
            x=186, y=y, w=34, h=30, text="+",
            on_press=on_plus,
        )
        for w in (lbl, minus, val, plus):
            self.add(w)
            self._edit_widgets.append(w)
        return val

    # ------------------------------------------------------------------
    # 編輯控制 / Edit controls
    # ------------------------------------------------------------------

    def _adjust(self, which, direction):
        """調整工作/休息/總時長。work 走預設清單（clamp），其餘依範圍 clamp。"""
        if which == "work":
            idx = self._work_index()
            idx = max(0, min(len(_WORK_PRESETS) - 1, idx + direction))
            self._work_min = _WORK_PRESETS[idx]
        elif which == "break":
            lo, hi, step = _BREAK_BOUNDS
            self._break_min = self._clamp(
                self._break_min + direction * step, lo, hi)
        else:
            lo, hi, step = _TOTAL_BOUNDS
            self._total_min = self._clamp(
                self._total_min + direction * step, lo, hi)
        self._refresh_edit_labels()

    def _work_index(self):
        """回傳目前 work 值最接近的預設索引。"""
        best_i, best_d = 0, 999999
        for i in range(len(_WORK_PRESETS)):
            d = abs(_WORK_PRESETS[i] - self._work_min)
            if d < best_d:
                best_d, best_i = d, i
        return best_i

    def _snap_work(self):
        """將 work 值對齊到最接近的預設值（處理舊存檔的非預設值）。"""
        self._work_min = _WORK_PRESETS[self._work_index()]

    @staticmethod
    def _clamp(value, lo, hi):
        return max(lo, min(hi, value))

    def _refresh_edit_labels(self):
        self._work_val.set_text("{}m".format(self._work_min))
        self._break_val.set_text("{}m".format(self._break_min))
        self._total_val.set_text("{}m".format(self._total_min))

    def _apply_visibility(self):
        """依狀態切換編輯群組 / 運行群組的可見性。"""
        editing = self._phase == PHASE_IDLE
        for w in self._edit_widgets:
            w.visible = editing
        self._reset_btn.visible = not editing

    # ------------------------------------------------------------------
    # 計時控制 / Timer control
    # ------------------------------------------------------------------

    def _start(self):
        """開始番茄鐘：持久化設定並進入工作階段。"""
        # 按下 START 時一次性寫入設定，避免每次 ± 都寫 flash
        ConfigManager.set_setting("pomodoro_work", self._work_min)
        ConfigManager.set_setting("pomodoro_break", self._break_min)
        ConfigManager.set_setting("pomodoro_total", self._total_min)

        self._round = 0
        self._total_remaining = self._total_min * 60
        self._paused = False
        self._last_tick_ms = time.ticks_ms()
        self._enter_phase(PHASE_WORK)
        self._apply_visibility()

    def _reset(self):
        """歸零回到 IDLE 編輯狀態。"""
        self._phase = PHASE_IDLE
        self._paused = False
        self._stop_feedback()
        self._apply_visibility()

    def _enter_phase(self, phase):
        """進入指定階段並設定其剩餘秒數與燈光。"""
        self._phase = phase
        if phase == PHASE_WORK:
            self._phase_remaining = self._work_min * 60
        elif phase == PHASE_BREAK:
            self._phase_remaining = self._break_min * 60
        self._signal_phase()

    def on_enter(self):
        # 重新讀取設定（網頁端可能已變更）
        self._work_min = ConfigManager.get_setting(
            "pomodoro_work", self._work_min)
        self._break_min = ConfigManager.get_setting(
            "pomodoro_break", self._break_min)
        self._total_min = ConfigManager.get_setting(
            "pomodoro_total", self._total_min)
        self._alert = ConfigManager.get_setting(
            "pomodoro_alert", self._alert)
        self._snap_work()  # 對齊到預設清單
        self._refresh_edit_labels()
        self._reset()
        # 停用自動環境光燈，避免覆蓋階段燈色
        try:
            self.app.presto.auto_ambient_leds(False)
        except Exception:
            pass

    def on_exit(self):
        # 關閉蜂鳴器與燈光，恢復環境光設定
        self._stop_feedback()
        self._clear_leds()
        try:
            ambient = ConfigManager.get_setting("ambient_leds", False)
            self.app.presto.auto_ambient_leds(bool(ambient))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 每幀更新 / Per-frame update
    # ------------------------------------------------------------------

    def update(self):
        if self._phase in (PHASE_IDLE, PHASE_DONE):
            return

        now = time.ticks_ms()
        delta = time.ticks_diff(now, self._last_tick_ms) / 1000.0
        self._last_tick_ms = now

        if self._paused:
            return

        self._phase_remaining -= delta
        self._total_remaining -= delta

        # 總時間到 → 結束 / Total elapsed → DONE
        if self._total_remaining <= 0:
            self._total_remaining = 0
            self._phase = PHASE_DONE
            self._signal_done()
            return

        # 當前階段結束 → 切換工作/休息
        if self._phase_remaining <= 0:
            if self._phase == PHASE_WORK:
                self._round += 1
                # 休息為 0 則跳過，直接下一段工作
                if self._break_min > 0:
                    self._enter_phase(PHASE_BREAK)
                else:
                    self._enter_phase(PHASE_WORK)
            else:
                self._enter_phase(PHASE_WORK)

    # ------------------------------------------------------------------
    # 繪製 / Drawing
    # ------------------------------------------------------------------

    def draw(self, display, vector, offset_x=0):
        self._draw_background(display)

        if self._phase == PHASE_IDLE:
            self._draw_title(display, "POMODORO", TOMATO, offset_x)
        else:
            self._draw_timer(display, offset_x)

        # widgets（按鈕、編輯標籤）支援滑動位移
        self._draw_widgets(display, offset_x)

    def _draw_title(self, display, text, color, offset_x):
        display.set_pen(display.create_pen(*color))
        tw = display.measure_text(text, FONT_LARGE)
        cx = (self.app.width - tw) // 2 + offset_x
        display.text(text, cx, 30, self.app.width, FONT_LARGE)

    def _draw_timer(self, display, offset_x):
        cx = self.app.width // 2 + offset_x
        cy = 100

        # 階段標題與顏色
        if self._phase == PHASE_WORK:
            label, color = "WORK", TOMATO
        elif self._phase == PHASE_BREAK:
            label, color = "BREAK", GREEN
        else:
            label, color = "DONE", WHITE

        # 進度環（剩餘比例）
        if self._phase in (PHASE_WORK, PHASE_BREAK):
            total = (self._work_min if self._phase == PHASE_WORK
                     else self._break_min) * 60
            frac = self._phase_remaining / total if total else 0
            self._draw_progress_ring(display, cx, cy, color, frac)

        # 階段名稱
        display.set_pen(display.create_pen(*color))
        lw = display.measure_text(label, FONT_MEDIUM)
        display.text(label, cx - lw // 2, 38, self.app.width, FONT_MEDIUM)

        # 大字 MM:SS（當前階段剩餘，DONE 時顯示 00:00）
        secs = int(self._phase_remaining if self._phase != PHASE_DONE else 0)
        secs = max(secs, 0)
        mmss = "{:02d}:{:02d}".format(secs // 60, secs % 60)
        display.set_pen(display.create_pen(*WHITE))
        mw = display.measure_text(mmss, FONT_LARGE * 2)
        display.text(mmss, cx - mw // 2, cy - 24,
                     self.app.width, FONT_LARGE * 2)

        # 次要資訊：回合數 + 總剩餘
        tsec = int(self._total_remaining)
        tsec = max(tsec, 0)
        info = "Round {}  Total {}:{:02d}:{:02d}".format(
            self._round, tsec // 3600, (tsec % 3600) // 60, tsec % 60)
        display.set_pen(display.create_pen(*GRAY))
        iw = display.measure_text(info, FONT_SMALL)
        display.text(info, cx - iw // 2, 160, self.app.width, FONT_SMALL)

        # 暫停提示
        if self._paused:
            ptxt = "PAUSED  (tap to resume)"
        elif self._phase != PHASE_DONE:
            ptxt = "tap to pause"
        else:
            ptxt = ""
        if ptxt:
            display.set_pen(display.create_pen(*DARK_GRAY))
            pw = display.measure_text(ptxt, FONT_SMALL)
            display.text(ptxt, cx - pw // 2, 175,
                         self.app.width, FONT_SMALL)

    def _draw_progress_ring(self, display, cx, cy, color, frac):
        """以點陣繪製進度環，frac 為剩餘比例（0..1）。"""
        r = 70
        lit = int(frac * 60 + 0.5)
        for i in range(60):
            if i < lit:
                display.set_pen(display.create_pen(*color))
            else:
                display.set_pen(display.create_pen(*DARK_GRAY))
            x = cx + int(r * self._cos_table[i])
            y = cy + int(r * self._sin_table[i])
            display.pixel(x, y)
            display.pixel(x + 1, y)
            display.pixel(x, y + 1)

    # ------------------------------------------------------------------
    # 觸控 / Touch
    # ------------------------------------------------------------------

    def handle_touch(self, tx, ty):
        # 先讓按鈕消費（START / RESET / ± 編輯）
        if super().handle_touch(tx, ty):
            return True
        # 運行中點擊任意處 → 暫停/恢復
        if self._phase in (PHASE_WORK, PHASE_BREAK):
            self._paused = not self._paused
            self._last_tick_ms = time.ticks_ms()
            return True
        return False

    # ------------------------------------------------------------------
    # 蜂鳴器 + LED 回饋 / Buzzer + LED feedback
    # ------------------------------------------------------------------

    def _phase_color(self):
        if self._phase == PHASE_WORK:
            return TOMATO
        if self._phase == PHASE_BREAK:
            return GREEN
        return (0, 80, 255)

    def _set_leds(self, color):
        try:
            for i in range(7):
                self.app.presto.set_led_rgb(i, color[0], color[1], color[2])
        except Exception:
            pass

    def _clear_leds(self):
        self._set_leds((0, 0, 0))

    def _signal_phase(self):
        """階段切換：依提示強度給予聲光回饋。"""
        self._alert_seq += 1
        seq = self._alert_seq
        color = self._phase_color()
        if self._alert == "off":
            self._set_leds(color)
            return
        if self._alert == "loud":
            asyncio.create_task(self._blink_leds(seq, color, 6, 120, 100))
            asyncio.create_task(self._alarm(seq, 4))
        else:  # normal — 維持原行為
            self._set_leds(color)
            asyncio.create_task(self._beep(880, 150, 1))

    def _signal_done(self):
        """結束：依提示強度給予更強的聲光回饋。"""
        self._alert_seq += 1
        seq = self._alert_seq
        done = (0, 80, 255)
        if self._alert == "off":
            self._set_leds(done)
            return
        if self._alert == "loud":
            asyncio.create_task(self._blink_leds(seq, done, 12, 150, 120))
            asyncio.create_task(self._alarm(seq, 8))
        else:  # normal — 維持原行為
            self._set_leds(done)
            asyncio.create_task(self._beep(660, 200, 3))

    def _stop_feedback(self):
        # 遞增世代序號，使進行中的閃爍/警報協程下次檢查時自行結束
        self._alert_seq += 1
        if self._buzzer:
            try:
                self._buzzer.set_tone(-1)
            except Exception:
                pass

    async def _blink_leds(self, seq, color, times, on_ms, off_ms):
        """非阻塞閃爍 7 顆 LED times 次，結束後維持 color。

        以 seq 對照 self._alert_seq；若期間頁面重置/離開則中止並不再動燈。
        """
        for _ in range(times):
            if seq != self._alert_seq:
                return
            self._set_leds(color)
            await asyncio.sleep_ms(on_ms)
            if seq != self._alert_seq:
                return
            self._set_leds((0, 0, 0))
            await asyncio.sleep_ms(off_ms)
        if seq == self._alert_seq:
            self._set_leds(color)

    async def _alarm(self, seq, cycles):
        """警報式蜂鳴：在壓電共振頻率附近快速掃頻，急促且聽感最大。"""
        if not self._buzzer:
            return
        for _ in range(cycles):
            if seq != self._alert_seq:
                break
            for freq in (_LOUD_FREQ, _LOUD_FREQ_HI):
                try:
                    self._buzzer.set_tone(freq)
                except Exception:
                    return
                await asyncio.sleep_ms(90)
        try:
            self._buzzer.set_tone(-1)
        except Exception:
            pass

    async def _beep(self, freq, dur_ms, count):
        """非阻塞蜂鳴：響 count 次，每次 dur_ms 毫秒。"""
        if not self._buzzer:
            return
        for _ in range(count):
            try:
                self._buzzer.set_tone(freq)
            except Exception:
                return
            await asyncio.sleep_ms(dur_ms)
            try:
                self._buzzer.set_tone(-1)
            except Exception:
                return
            await asyncio.sleep_ms(120)
