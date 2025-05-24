# test_basic_leds.py - Enkel test av CO₂ LEDs
from machine import Pin
import time

print("🔴 Testar CO₂ LEDs...")

# Definiera LED-pinnarna
red_led = Pin(18, Pin.OUT)
yellow_led = Pin(19, Pin.OUT)
green_led = Pin(20, Pin.OUT)


def test_single_led(led, name, color_emoji):
    """Testar en enskild LED"""
    print(f"{color_emoji} Testar {name} LED...")

    # Blinka 3 gånger
    for i in range(3):
        led.on()
        print(f"  {name} PÅ")
        time.sleep(0.5)
        led.off()
        print(f"  {name} AV")
        time.sleep(0.5)

    print(f"✅ {name} LED test klar!")
    print()


def test_all_together():
    """Testar alla LEDs samtidigt"""
    print("🌈 Testar alla LEDs samtidigt...")

    # Tänd alla
    red_led.on()
    yellow_led.on()
    green_led.on()
    print("  Alla LEDs PÅ")
    time.sleep(2)

    # Släck alla
    red_led.off()
    yellow_led.off()
    green_led.off()
    print("  Alla LEDs AV")
    time.sleep(1)


def running_light():
    """Springer ljus-effekt"""
    print("🏃 Springer ljus...")

    leds = [red_led, yellow_led, green_led]
    names = ["Röd", "Gul", "Grön"]

    for _ in range(2):  # 2 varv
        for i, (led, name) in enumerate(zip(leds, names)):
            # Tänd denna LED
            led.on()
            print(f"  → {name}")
            time.sleep(0.3)

            # Släck denna LED
            led.off()
            time.sleep(0.1)


# ===== HUVUDTEST =====
try:
    print("🚀 Startar LED-test...")
    print("=" * 30)

    # Test varje LED separat
    test_single_led(red_led, "Röd", "🔴")
    test_single_led(yellow_led, "Gul", "🟡")
    test_single_led(green_led, "Grön", "🟢")

    # Test alla tillsammans
    test_all_together()

    # Springer ljus
    running_light()

    print("✅ Alla LED-tester klara!")
    print("🎉 Om du såg LEDs blinka = kopplingarna fungerar!")

except KeyboardInterrupt:
    print("\n🛑 Test avbrutet")
finally:
    # Släck alla LEDs
    red_led.off()
    yellow_led.off()
    green_led.off()
    print("💡 Alla LEDs släckta")
