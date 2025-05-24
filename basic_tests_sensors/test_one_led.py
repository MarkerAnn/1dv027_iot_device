from machine import Pin
import time

led = Pin(18, Pin.OUT)
print("Tänder LED...")
led.on()
time.sleep(3)
led.off()
print("Släckte LED.")

led = Pin(19, Pin.OUT)
print("Tänder LED...")
led.on()
time.sleep(3)
led.off()
print("Släckte LED.")

led = Pin(20, Pin.OUT)
print("Tänder LED...")
led.on()
time.sleep(3)
led.off()
print("Släckte LED.")
