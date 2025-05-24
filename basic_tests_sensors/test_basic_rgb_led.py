from machine import Pin
import time

# Endast en färg testas först
red = Pin(22, Pin.OUT)

print("🔴 Tänder röd...")
red.value(0)  # Tänder vid gemensam katod
time.sleep(2)
print("Släcker röd...")
red.value(1)
