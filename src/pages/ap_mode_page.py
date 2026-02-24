"""AP Mode Page — 顯示 AP 連接資訊，引導使用者設定 WiFi。"""

import machine
from ui.page import Page
from ui.widget import Label, Container, Button
from ui.theme import (
    WHITE, GRAY, DARK_GRAY, CYAN, FONT_SMALL, FONT_MEDIUM, PADDING,
)
from config_manager import ConfigManager


class ApModePage(Page):
    """AP Mode 設定引導頁面。

    顯示 AP 的 SSID、Password、IP，引導使用者連接並設定 WiFi。
    """

    def __init__(self, app):
        super().__init__(app)

        # 取得 AP 資訊
        ssid, password, ip = "N/A", "", "192.168.4.1"
        wm = getattr(app, 'wm', None)
        if wm:
            ssid, password, ip = wm.get_ap_config()

        # 標題
        self.add(Label(
            x=60, y=20, text="WiFi Setup",
            color=CYAN, scale=FONT_MEDIUM,
        ))

        # 說明文字
        self.add(Label(
            x=20, y=55, text="Connect to the AP below",
            color=GRAY, scale=FONT_SMALL,
        ))
        self.add(Label(
            x=20, y=70, text="to configure WiFi:",
            color=GRAY, scale=FONT_SMALL,
        ))

        # AP 資訊區塊
        info_box = Container(
            x=15, y=95, w=210, h=100,
            bg=DARK_GRAY, padding=PADDING,
        )

        info_box.add(Label(
            x=25, y=105, text="SSID:",
            color=GRAY, scale=FONT_SMALL,
        ))
        info_box.add(Label(
            x=25, y=120, text=ssid,
            color=WHITE, scale=FONT_SMALL,
        ))

        if password:
            info_box.add(Label(
                x=25, y=140, text="Password:",
                color=GRAY, scale=FONT_SMALL,
            ))
            info_box.add(Label(
                x=25, y=155, text=password,
                color=WHITE, scale=FONT_SMALL,
            ))
        else:
            info_box.add(Label(
                x=25, y=140, text="(No password)",
                color=GRAY, scale=FONT_SMALL,
            ))

        info_box.add(Label(
            x=25, y=170, text=f"Open http://{ip}",
            color=CYAN, scale=FONT_SMALL,
        ))

        self.add(info_box)

        # 底部狀態或按鈕
        saved_ssid, _ = ConfigManager.get_wifi_credentials()
        if saved_ssid:
            self.add(Button(
                x=20, y=202, w=95, h=30, text="Reconnect",
                scale=FONT_SMALL, on_press=lambda: machine.reset()
            ))

            self.add(Button(
                x=125, y=202, w=95, h=30, text="Reboot",
                scale=FONT_SMALL, on_press=lambda: machine.reset()
            ))
        else:
            self.add(Label(
                x=30, y=215, text="Waiting for setup...",
                color=GRAY, scale=FONT_SMALL,
            ))
