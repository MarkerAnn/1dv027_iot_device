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
time.sleep(5)


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


# ==== Main Loop ====
while True:
    try:
        data = {}
        if scd.data_ready:
            co2 = scd.co2
            temp_air = round(scd.temperature, 2)
            rh_air = round(scd.relative_humidity, 1)

            print("CO2:", co2, "ppm")
            print("Air temperature:", temp_air, "C")
            print("Air humidity:", rh_air, "%")

            update_co2_leds(co2)

            data.update(
                {
                    "co2": co2,
                    "temp_air": temp_air,
                    "rh_air": rh_air,
                }
            )
        else:
            print("No new air values yet.")

        try:
            moisture = soil.get_moisture()
            temp_soil = round(soil.get_temp(), 2)

            print("Soil moisture:", moisture)
            print("Soil temperature:", temp_soil, "C")

            update_soil_rgb(moisture)

            data.update(
                {
                    "moisture": moisture,
                    "temp_soil": temp_soil,
                }
            )

        except Exception as e:
            print("Soil sensor error:", e)

        # Send data to MQTT broker
        if data:
            client.publish(MQTT_TOPIC_BASE.encode(), json.dumps(data))
            print("Data sent to MQTT:", data)
        else:
            print("No data to send.")

    except Exception as e:
        print("Unexpected error:", e)

    time.sleep(MEASUREMENT_INTERVAL)
