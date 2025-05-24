# This will scan the I2C bus and print out the addresses of any devices connected to it.
import machine

# Define SDA and SCL pins
sda = machine.Pin(0)
scl = machine.Pin(1)

# Initialize I2C
i2c = machine.I2C(0, sda=sda, scl=scl, freq=400000)

# Scan and print the I2C addresses of connected devices (LCD, in this case)
print("I2C scan result:", i2c.scan())
