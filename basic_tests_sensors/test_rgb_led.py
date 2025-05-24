# test_rgb_led.py - RGB LED test
from machine import Pin, PWM
import time

print("🌈 Testar RGB LED...")

# Skapa PWM för RGB-pinnarna
red_pwm = PWM(Pin(22))
green_pwm = PWM(Pin(26))
blue_pwm = PWM(Pin(27))

# Sätt PWM-frekvens
red_pwm.freq(1000)
green_pwm.freq(1000)
blue_pwm.freq(1000)


def set_rgb(red, green, blue):
    """Sätt RGB-färg (0-65535)"""
    red_pwm.duty_u16(red)
    green_pwm.duty_u16(green)
    blue_pwm.duty_u16(blue)


def rgb_off():
    """Släck RGB LED"""
    set_rgb(0, 0, 0)


def test_primary_colors():
    """Testar grundfärger"""
    colors = [
        (65535, 0, 0, "🔴 Röd"),
        (0, 65535, 0, "🟢 Grön"),
        (0, 0, 65535, "🔵 Blå"),
    ]

    print("Testing grundfärger...")
    for red, green, blue, name in colors:
        print(f"  {name}")
        set_rgb(red, green, blue)
        time.sleep(1.5)
        rgb_off()
        time.sleep(0.5)


def test_mixed_colors():
    """Testar blandade färger"""
    colors = [
        (65535, 65535, 0, "🟡 Gul (Röd+Grön)"),
        (65535, 0, 65535, "🟣 Magenta (Röd+Blå)"),
        (0, 65535, 65535, "🩵 Cyan (Grön+Blå)"),
        (65535, 65535, 65535, "⚪ Vit (Alla färger)"),
    ]

    print("Testing blandade färger...")
    for red, green, blue, name in colors:
        print(f"  {name}")
        set_rgb(red, green, blue)
        time.sleep(1.5)
        rgb_off()
        time.sleep(0.5)


def fade_effect():
    """Fade-effekt genom färger"""
    print("🌈 Fade-effekt...")

    # Fade från röd till grön
    for i in range(0, 65536, 2000):
        set_rgb(65535 - i, i, 0)
        time.sleep(0.05)

    # Fade från grön till blå
    for i in range(0, 65536, 2000):
        set_rgb(0, 65535 - i, i)
        time.sleep(0.05)

    # Fade från blå till röd
    for i in range(0, 65536, 2000):
        set_rgb(i, 0, 65535 - i)
        time.sleep(0.05)

    rgb_off()


def soil_status_demo():
    """Demonstrerar jordstatusfärger"""
    print("🌱 Jordstatus demo...")

    statuses = [
        (0, 0, 65535, "💧 Blött (Blå)"),
        (0, 65535, 0, "🌱 Lagom fukt (Grön)"),
        (65535, 0, 0, "🔥 Torrt (Röd)"),
    ]

    for red, green, blue, name in statuses:
        print(f"  {name}")
        set_rgb(red, green, blue)
        time.sleep(2)
        rgb_off()
        time.sleep(0.5)


# ===== HUVUDTEST =====
try:
    print("🚀 Startar RGB LED-test...")
    print("=" * 35)

    # Testa grundfärger
    test_primary_colors()
    time.sleep(1)

    # Testa blandade färger
    test_mixed_colors()
    time.sleep(1)

    # Fade-effekt
    fade_effect()
    time.sleep(1)

    # Jordstatus demo
    soil_status_demo()

    print("✅ RGB LED-test klart!")
    print("🌈 Om du såg olika färger = RGB fungerar!")

except KeyboardInterrupt:
    print("\n🛑 Test avbrutet")
finally:
    # Släck RGB LED
    rgb_off()
    print("💡 RGB LED släckt")
