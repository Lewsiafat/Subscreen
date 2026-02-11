# Presto AI Coding Reference Guide

This guide provides concise, verified code patterns for the Presto (RP2350) device. Use these snippets as the foundation for generating new applications.

## 1. Basic Setup & Display

**Boilerplate (240x240):**
```python
from presto import Presto

# Initialize (ambient_light=True enables the light sensor)
presto = Presto(ambient_light=True)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()

# Main Loop
while True:
    display.set_pen(display.create_pen(0, 0, 0)) # Black
    display.clear()
    
    display.set_pen(display.create_pen(255, 255, 255)) # White
    display.text("Hello AI", 10, 10, WIDTH, 4) # Scale=4
    
    presto.update()
```

**Full Resolution (480x480) - Requires Memory Care:**
```python
# Use palette=True to save RAM when using full_res
presto = Presto(full_res=True, palette=True)
display = presto.display
WIDTH, HEIGHT = display.get_bounds() # Returns 480, 480
```

## 2. Touch Interaction

**Using `Button` Helper:**
```python
from presto import Presto
from touch import Button

presto = Presto()
display = presto.display
touch = presto.touch

# Define button area: x, y, width, height
btn_ok = Button(20, 100, 100, 50)

while True:
    touch.poll() # Must poll in every loop
    
    display.set_pen(display.create_pen(0,0,0))
    display.clear()
    
    # Check state
    if btn_ok.is_pressed():
        display.set_pen(display.create_pen(0, 255, 0)) # Green
    else:
        display.set_pen(display.create_pen(255, 0, 0)) # Red
        
    # Draw button bounds
    display.rectangle(*btn_ok.bounds)
    
    presto.update()
```

**Raw Touch Data:**
```python
if touch.state:
    print(f"Touched at: {touch.x}, {touch.y}")
```

## 3. Graphics & Vectors (`PicoVector`)

For high-quality anti-aliased shapes.

```python
from picovector import PicoVector, Polygon, Transform, ANTIALIAS_BEST

vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()
vector.set_transform(t)

# Define a shape (Triangle)
tri = Polygon()
tri.path((0, -20), (15, 10), (-15, 10))

# Drawing
display.set_pen(display.create_pen(255, 255, 0)) # Yellow

t.reset()
t.translate(120, 120)  # Move to center
t.rotate(45)           # Rotate 45 degrees

vector.draw(tri)
```

## 4. WiFi & Networking

**Simple Connect (Blocking):**
```python
presto.connect() # Uses SSID/PASSWORD from secrets.py
```

**Async Connect (Non-blocking):**
```python
import asyncio
# In async main():
await presto.async_connect()
```

**HTTP Get (using `requests`):**
```python
import requests
req = requests.get("http://api.example.com/data.json")
data = req.json()
req.close()
print(data)
```

## 5. Sensors & LEDs

**Accelerometer/Gyro (LSM6DS3):**
```python
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
import machine

i2c = machine.I2C()
sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)

# In loop:
ax, ay, az, gx, gy, gz = sensor.get_readings()
```

**Light Sensor (LTR-559):**
```python
from breakout_ltr559 import BreakoutLTR559
import machine

# LTR-559 is on the internal I2C bus
ltr = BreakoutLTR559(machine.I2C())

# Read Lux
reading = ltr.get_reading()
if reading:
    lux = reading[BreakoutLTR559.LUX]
```

**RGB LEDs (7 LEDs):**
```python
# Set LED 0 to Red
presto.set_led_rgb(0, 255, 0, 0)

# Set LED 1 to Blue (HSV)
presto.set_led_hsv(1, 0.66, 1.0, 1.0)
```

**Backlight:**
```python
presto.set_backlight(0.5) # 0.0 to 1.0
```

## 6. Audio (Piezo Buzzer)

**Setup & Tone:**
```python
from presto import Buzzer

# Buzzer is on Pin 43
buzzer = Buzzer(43)

# Play 440Hz tone
buzzer.set_tone(440)

# Stop sound
buzzer.set_tone(-1)
```

## 7. Storage (SD Card)

**Setup & Mount:**
```python
import machine
import sdcard
import uos

# SPI0 Setup for SD Card
sd_spi = machine.SPI(0, 
    sck=machine.Pin(34, machine.Pin.OUT), 
    mosi=machine.Pin(35, machine.Pin.OUT), 
    miso=machine.Pin(36, machine.Pin.OUT))
    
sd = sdcard.SDCard(sd_spi, machine.Pin(39))
uos.mount(sd, "/sd")
```

**Read/Write File:**
```python
# Write
with open("/sd/test.txt", "w") as f:
    f.write("Hello Presto!")

# Read
with open("/sd/test.txt", "r") as f:
    print(f.read())
```

**Load Image from SD:**
```python
import jpegdec
j = jpegdec.JPEG(display)
j.open_file("/sd/image.jpg")
j.decode(0, 0, jpegdec.JPEG_SCALE_FULL)
```
