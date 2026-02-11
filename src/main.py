import uasyncio as asyncio
from wifi_manager import WiFiManager
from constants import STATE_IDLE, STATE_CONNECTING, STATE_CONNECTED, STATE_FAIL, STATE_AP_MODE

async def blink_led():
    """
    Simulates a background user application task.
    """
    while True:
        await asyncio.sleep(2)

async def monitor_status(wm):
    """
    Monitor and report WiFi state changes.
    """
    last_state = -1
    while True:
        current_state = wm.get_status()
        if current_state != last_state:
            state_name = "UNKNOWN"
            if current_state == STATE_IDLE: state_name = "IDLE"
            elif current_state == STATE_CONNECTING: state_name = "CONNECTING"
            elif current_state == STATE_CONNECTED: state_name = "CONNECTED (Station)"
            elif current_state == STATE_FAIL: state_name = "FAIL"
            elif current_state == STATE_AP_MODE: state_name = "AP MODE (Provisioning)"

            print(f"System: State -> {state_name}")
            last_state = current_state

            if current_state == STATE_AP_MODE:
                print("Action: Connect to 'Picore-W-Setup' to configure the device.")

        await asyncio.sleep(1)

async def main():
    """
    Main entry point for the application.
    Initializes the WiFi manager and starts concurrent tasks.
    """
    print("--- Picore-W Initializing ---")

    # Initialize the WiFi Manager (starts its background state machine)
    wm = WiFiManager()

    # Launch concurrent system and application tasks
    asyncio.create_task(blink_led())
    asyncio.create_task(monitor_status(wm))

    # Keep the event loop running
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- System Stopped ---")
