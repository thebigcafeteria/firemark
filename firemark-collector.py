#!/usr/bin/env python3
"""Combined Firemark sensor reporter and health checker."""

import time
import requests
import board
import busio
import socket
import json
import subprocess
import os

import adafruit_bme280
import adafruit_ens160
import adafruit_scd4x
import adafruit_scd30
import neopixel

from sensirion_i2c_driver import I2cConnection
from sensirion_i2c_driver.linux_i2c_transceiver import LinuxI2cTransceiver
from sensirion_i2c_sgp4x.sgp41 import Sgp41I2cDevice

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ENDPOINTS = ["http://ferrix.local:5000/ingest", "http://ghorman.local:5000/ingest"]
DEVICE_ID = socket.gethostname()
POST_HISTORY = []
LOCAL_DUMP_PATH = "/home/thebigcafeteria/latest.json"

LED_PIN = board.D18
PIXEL_COUNT = 8
PIXELS = neopixel.NeoPixel(LED_PIN, PIXEL_COUNT, brightness=0.2, auto_write=False)

# LED index mapping
LED_BOOT = 0
LED_BME280 = 1
LED_ENS160 = 2
LED_SCD41 = 3
LED_SCD30 = 4
LED_SGP41 = 5
LED_ENDPOINT_A = 6
LED_ENDPOINT_B = 7

GREEN = (0, 50, 0)
RED = (50, 0, 0)
BLUE = (0, 0, 50)

PIXELS.fill((0, 0, 0))
PIXELS[LED_BOOT] = BLUE
PIXELS.show()

# ---------------------------------------------------------------------------
# Sensor Setup
# ---------------------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)

bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
ens160 = adafruit_ens160.ENS160(i2c)
scd41 = adafruit_scd4x.SCD4X(i2c)
scd41.start_periodic_measurement()
scd30 = adafruit_scd30.SCD30(i2c)

sgp_conn = I2cConnection(LinuxI2cTransceiver('/dev/i2c-1'))
sgp41 = Sgp41I2cDevice(sgp_conn)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def collect_health():
    def get_temp():
        try:
            out = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
            return float(out.strip().split("=")[1].replace("'C", ""))
        except Exception:
            return None

    def get_uptime():
        try:
            with open("/proc/uptime", "r") as f:
                return float(f.readline().split()[0])
        except Exception:
            return None

    def get_rssi():
        try:
            out = subprocess.check_output(["iwconfig", "wlan0"]).decode()
            for line in out.split("\n"):
                if "Signal level" in line:
                    return int(line.split("Signal level=")[1].split(" ")[0])
        except Exception:
            return None

    def get_latency():
        try:
            out = subprocess.check_output([
                "ping", "-c", "1", "-W", "1", "ferrix.local"
            ]).decode()
            for line in out.split("\n"):
                if "time=" in line:
                    return float(line.split("time=")[1].split(" ")[0])
        except Exception:
            return None

    def get_throttled():
        try:
            out = subprocess.check_output(["vcgencmd", "get_throttled"]).decode()
            return out.strip().split("=")[1]
        except Exception:
            return None

    return {
        "cpu_temp": get_temp(),
        "uptime": get_uptime(),
        "rssi": get_rssi(),
        "latency_ms": get_latency(),
        "throttled": get_throttled(),
    }


def post_payload(data):
    timestamp = time.strftime("%H:%M:%S")
    for idx, url in enumerate(ENDPOINTS):
        try:
            resp = requests.post(url, json=data, timeout=5)
            status = resp.status_code
            PIXELS[LED_ENDPOINT_A + idx] = GREEN if status == 200 else RED
            POST_HISTORY.append((url.split("//")[1].split(".")[0], status, timestamp))
        except Exception:
            PIXELS[LED_ENDPOINT_A + idx] = RED
            POST_HISTORY.append((url.split("//")[1].split(".")[0], "ERR", timestamp))
    PIXELS.show()
    while len(POST_HISTORY) > 5:
        POST_HISTORY.pop(0)

    try:
        os.makedirs(os.path.dirname(LOCAL_DUMP_PATH), exist_ok=True)
        with open(LOCAL_DUMP_PATH, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("[!] Failed to write local latest.json:", e)


def read_sensors():
    readings = {}

    # BME280
    try:
        readings["bme280"] = {
            "temperature": round(bme280.temperature, 1),
            "humidity": round(bme280.relative_humidity, 1),
            "pressure": round(bme280.pressure, 1),
        }
        PIXELS[LED_BME280] = GREEN
    except Exception:
        readings["bme280"] = None
        PIXELS[LED_BME280] = RED

    # ENS160
    try:
        ens160.temperature = bme280.temperature
        ens160.humidity = bme280.relative_humidity
        readings["ens160"] = {
            "air_quality_index": ens160.AQI,
            "tvoc": ens160.TVOC,
            "eco2": ens160.eCO2,
        }
        PIXELS[LED_ENS160] = GREEN
    except Exception:
        readings["ens160"] = None
        PIXELS[LED_ENS160] = RED

    # SCD41
    try:
        if scd41.data_ready:
            readings["scd41"] = {
                "co2": scd41.CO2,
                "temperature": scd41.temperature,
                "humidity": scd41.relative_humidity,
            }
        PIXELS[LED_SCD41] = GREEN
    except Exception:
        readings.setdefault("scd41", None)
        PIXELS[LED_SCD41] = RED

    # SCD30
    try:
        if scd30.data_available:
            readings["scd30"] = {
                "co2": scd30.CO2,
                "temperature": scd30.temperature,
                "humidity": scd30.relative_humidity,
            }
        PIXELS[LED_SCD30] = GREEN
    except Exception:
        readings.setdefault("scd30", None)
        PIXELS[LED_SCD30] = RED

    # SGP41
    try:
        voc, nox = sgp41.measure_raw(
            relative_humidity=bme280.relative_humidity,
            temperature=bme280.temperature,
        )
        readings["sgp41"] = {"voc_raw": voc.raw, "nox_raw": nox.raw}
        PIXELS[LED_SGP41] = GREEN
    except Exception:
        readings["sgp41"] = None
        PIXELS[LED_SGP41] = RED

    PIXELS.show()
    return readings


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

PIXELS[LED_BOOT] = GREEN
PIXELS.show()

while True:
    sensor_data = read_sensors()
    health = collect_health()
    payload = {
        "device": DEVICE_ID,
        "ts": int(time.time()),
        "sensors": sensor_data,
        "health": health,
    }

    post_payload(payload)

    print(json.dumps(payload, indent=2))

    time.sleep(30)
