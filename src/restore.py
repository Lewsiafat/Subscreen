import os
import machine

try:
    os.remove('wifi_config.json')
    print("Config deleted.")
except OSError:
    print("Config not found.")
# Optional: also reset the device
machine.reset()
