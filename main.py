from machine import I2C, Pin, PWM
import time
import json
from umqtt_simple import MQTTClient
import network

# ==== Sensor Library ====
# Import SCD40 CO2 sensor driver and STEMMA Soil Sensor driver
from lib.scd40 import SCD4X
from lib.stemma_soil_sensor import StemmaSoilSensor

# ==== Configuration ====
# Import configuration settings
from config import (
    WIFI_SSID,
    WIFI_PASSWORD,
    MQTT_SERVER,
    MQTT_PORT,
    MQTT_CLIENT_ID,
    MQTT_TOPIC_BASE,
    MEASUREMENT_INTERVAL,
)


# ==== WiFi Connection ====
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        print("Connecting to WiFi...")
        time.sleep(1)

    print("Connected to WiFi:", wlan.ifconfig())
    return wlan


# Connect to WiFi
connect_wifi(WIFI_SSID, WIFI_PASSWORD)
print("WiFi connection established.")
time.sleep(5)  # Allow time for connection to stabilize


# ==== MQTT Client ====
client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, MQTT_PORT)
client.connect()
print("Connected to MQTT broker:", MQTT_SERVER)

# ==== I2C and Sensors ====
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
scd = SCD4X(i2c)
soil = StemmaSoilSensor(i2c)
scd.start_periodic_measurement()


# ==== CO2 LEDs ====
led_red = Pin(18, Pin.OUT)
led_yellow = Pin(19, Pin.OUT)
led_green = Pin(20, Pin.OUT)


# ==== RGB LED for soil moisturizer ====
rgb_red = PWM(Pin(22))
rgb_green = PWM(Pin(26))
rgb_blue = PWM(Pin(27))

# Set PWM frequency for RGB (standard for LEDs)
for pwm in [rgb_red, rgb_green, rgb_blue]:
    pwm.freq(1000)

print("Waiting for first sensor values...")
time.sleep(10)

# ===== Recovery Tracking =====
scd40_fail_count = 0
soil_fail_count = 0
MAX_SENSOR_FAILS = 5  # Max consecutive failures before recovery, RESET
last_scd40_read = time.time()  # FIXED: Removed double underscore
last_soil_read = time.time()
SENSOR_TIMEOUT = 300  # 5 minutes timeout data -> reset sensor


def set_rgb(r: int, g: int, b: int):
    # r, g, b values: 0 (on) to 65535 (off) for common cathode
    rgb_red.duty_u16(r)
    rgb_green.duty_u16(g)
    rgb_blue.duty_u16(b)


# Update CO2 LEDs based on CO2 value
def update_co2_leds(co2_value: int):
    # Turn on one LED depending on CO2 range
    led_red.value(0)
    led_yellow.value(0)
    led_green.value(0)

    if co2_value < 600:
        led_green.value(1)
    elif 600 <= co2_value <= 1400:
        led_yellow.value(1)
    else:
        led_red.value(1)


def update_soil_rgb(moisture: int):
    # Adjusted RGB mapping for correct GPIO configuration
    if moisture < 400:
        set_rgb(
            65535,
            0,
            0,
        )  # Red
    elif 400 <= moisture < 800:
        set_rgb(65535, 65535, 65535)  # White, all colors on
    elif 800 <= moisture <= 1200:
        set_rgb(0, 65535, 0)  # Green
    else:
        set_rgb(0, 0, 65535)  # Blue (very wet)


def reset_scd40():
    """Reset SCD40 sensor when it gets stuck"""
    global scd40_fail_count, last_scd40_read
    print("🔄 Resetting SCD40 sensor...")
    try:
        scd.stop_periodic_measurement()
        time.sleep(1)
        scd.start_periodic_measurement()
        time.sleep(2)
        scd40_fail_count = 0
        print("✅ SCD40 reset complete")
    except Exception as e:
        print(f"❌ SCD40 reset failed: {e}")


def reset_soil_sensor():
    """Reset STEMMA Soil sensor by reinitializing"""
    global soil_fail_count, last_soil_read, soil
    print("🔄 Resetting STEMMA Soil sensor...")
    try:
        # Reinitialize the soil sensor
        soil = StemmaSoilSensor(i2c)
        time.sleep(1)
        soil_fail_count = 0
        print("✅ Soil sensor reset complete")
    except Exception as e:
        print(f"❌ Soil sensor reset failed: {e}")


def read_scd40_with_recovery():
    """Read SCD40 with automatic recovery on failures"""
    global scd40_fail_count, last_scd40_read

    try:
        # Check if too much time has passed without successful read
        if time.time() - last_scd40_read > SENSOR_TIMEOUT:
            print(f"⏰ SCD40 timeout ({SENSOR_TIMEOUT}s), forcing reset...")
            reset_scd40()
            return None

        # Try to read data
        if scd.data_ready:
            co2 = scd.co2
            temp_air = round(scd.temperature, 2)
            rh_air = round(scd.relative_humidity, 1)

            # Validate readings (basic sanity check)
            if co2 is None or co2 < 300 or co2 > 5000:
                raise ValueError(f"Invalid CO2 reading: {co2}")
            if temp_air is None or temp_air < -20 or temp_air > 60:
                raise ValueError(f"Invalid temperature reading: {temp_air}")
            if rh_air is None or rh_air < 0 or rh_air > 100:
                raise ValueError(f"Invalid humidity reading: {rh_air}")

            print(f"CO2: {co2} ppm, Air temp: {temp_air}°C, Humidity: {rh_air}%")
            update_co2_leds(co2)

            # Reset fail counter on successful read
            scd40_fail_count = 0
            last_scd40_read = time.time()

            return {
                "co2": co2,
                "temp_air": temp_air,
                "rh_air": rh_air,
            }
        else:
            print("SCD40 data not ready yet...")
            scd40_fail_count += 1

            # Reset sensor if too many consecutive failures
            if scd40_fail_count >= MAX_SENSOR_FAILS:
                print(f"⚠️ SCD40 failed {MAX_SENSOR_FAILS} times, resetting...")
                reset_scd40()

            return None

    except Exception as e:
        print(f"❌ SCD40 error: {e}")
        scd40_fail_count += 1

        if scd40_fail_count >= MAX_SENSOR_FAILS:
            reset_scd40()

        return None


def read_soil_with_recovery():
    """Read STEMMA Soil sensor with automatic recovery on failures"""
    global soil_fail_count, last_soil_read

    try:
        # Check timeout
        if time.time() - last_soil_read > SENSOR_TIMEOUT:
            print(f"⏰ Soil sensor timeout ({SENSOR_TIMEOUT}s), forcing reset...")
            reset_soil_sensor()
            return None

        # Read moisture and temperature
        moisture = soil.get_moisture()
        temp_soil = round(soil.get_temp(), 2)

        # Validate readings
        if moisture is None or moisture < 0 or moisture > 4095:
            raise ValueError(f"Invalid moisture reading: {moisture}")
        if temp_soil is None or temp_soil < -20 or temp_soil > 60:
            raise ValueError(f"Invalid soil temperature: {temp_soil}")

        print(f"Soil moisture: {moisture}, Soil temp: {temp_soil}°C")
        update_soil_rgb(moisture)

        # Reset fail counter on successful read
        soil_fail_count = 0
        last_soil_read = time.time()

        return {
            "moisture": moisture,
            "temp_soil": temp_soil,
        }

    except Exception as e:
        print(f"❌ Soil sensor error: {e}")
        soil_fail_count += 1

        if soil_fail_count >= MAX_SENSOR_FAILS:
            print(f"⚠️ Soil sensor failed {MAX_SENSOR_FAILS} times, resetting...")
            reset_soil_sensor()

        return None


# ==== Main Loop ====
while True:
    try:
        data = {}

        # Read SCD40 with recovery
        scd40_data = read_scd40_with_recovery()
        if scd40_data:
            data.update(scd40_data)

        # Read soil sensor with recovery
        soil_data = read_soil_with_recovery()
        if soil_data:
            data.update(soil_data)

        # Send data to MQTT broker
        if data:
            client.publish(MQTT_TOPIC_BASE.encode(), json.dumps(data))
            print(f"📡 Data sent to MQTT: {data}")
        else:
            print("No data to send.")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    time.sleep(MEASUREMENT_INTERVAL)
