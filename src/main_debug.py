"""
Debug mode entry point for Pico Explorer.

Upload this as main.py to the device to enable the debug dashboard.
Replaces the standard main.py with display-based monitoring.

If startup fails, the onboard LED will flash rapidly and the error
will be shown on the display (if available).
"""
import machine
import time


def _panic(error):
    """Flash LED rapidly and try to show error on display."""
    led = machine.Pin("LED", machine.Pin.OUT)
    msg = str(error)
    print(f"FATAL: {msg}")

    # Try to show on display
    try:
        from picographics import PicoGraphics, DISPLAY_PICO_EXPLORER
        display = PicoGraphics(display=DISPLAY_PICO_EXPLORER)
        display.set_backlight(0.8)
        display.set_font("bitmap8")
        bg = display.create_pen(0, 0, 0)
        red = display.create_pen(255, 0, 0)
        white = display.create_pen(255, 255, 255)
        display.set_pen(bg)
        display.clear()
        display.set_pen(red)
        display.text("STARTUP ERROR", 4, 4, scale=2)
        display.set_pen(white)
        # Wrap error text across lines
        y = 30
        for i in range(0, len(msg), 28):
            display.text(msg[i:i + 28], 4, y, scale=2)
            y += 18
        display.update()
    except Exception:
        pass

    # Flash LED indefinitely
    while True:
        led.toggle()
        time.sleep(0.15)


try:
    import uasyncio as asyncio
    from wifi_manager import WiFiManager
    from debug_display import DebugDisplay
    from logger import Logger, LogLevel

    async def main():
        Logger.set_level(LogLevel.DEBUG)

        wm = WiFiManager()
        debug = DebugDisplay(wm.get_debug_info)
        asyncio.create_task(debug.run())

        # Keep main task alive
        while True:
            await asyncio.sleep(10)

    asyncio.run(main())

except KeyboardInterrupt:
    print("\n--- System Stopped ---")
except Exception as e:
    _panic(e)
