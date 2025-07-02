# ENV3 Python Test – MikroE Environment 3 Click (BME688)

import time
import board
import busio
import adafruit_bme680

# Create I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# BME688 is likely at address 0x76
bme = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)

# Optional oversampling settings
bme.sea_level_pressure = 1013.25  # Adjust if known for better altitude

while True:
    print("--- ENV3 Click Sensor Readings ---")
    print(f"Temperature: {bme.temperature:.1f} C")
    print(f"Humidity: {bme.relative_humidity:.1f}%")
    print(f"Pressure: {bme.pressure:.1f} hPa")
    print(f"Gas (VOC resistance): {bme.gas:.1f} ohms")
    print("----------------------------------")
    time.sleep(2)
