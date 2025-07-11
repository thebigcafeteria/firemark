# firemark01_reporter.py — Unified AQI5 + ENV3 dashboard with POST history and system health

import time
import requests
import board
import busio
import adafruit_bme680
from smbus2 import SMBus
from datetime import datetime
import os
import subprocess
import socket
import json

# ---- AQI5 Setup (ADS1015 via SMBus) ----
AQI5_ADDR = 0x48
CHANNEL_CONFIGS = {
    'CO':   0xC183,
    'NH3':  0xD183,
    'NO2':  0xE183
}

def read_ads1015(bus, config):
    bus.write_i2c_block_data(AQI5_ADDR, 0x01, [(config >> 8) & 0xFF, config & 0xFF])
    time.sleep(0.01)
    raw = bus.read_word_data(AQI5_ADDR, 0x00)
    value = ((raw & 0xFF) << 8) | (raw >> 8)
    if value & 0x8000:
        value -= 1 << 16
    return value

# ---- ENV3 Setup (BME688 via Adafruit lib) ----
i2c = busio.I2C(board.SCL, board.SDA)
bme = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)
bme.sea_level_pressure = 1013.25

# ---- POST Config ----
ENDPOINTS = ["http://ferrix.local:5000/ingest", "http://ghorman.local:5000/ingest"]
DEVICE_ID = socket.gethostname()
POST_HISTORY = []
LOCAL_DUMP_PATH = f"/home/thebigcafeteria/latest.json"

def collect_health():
    def get_temp():
        try:
            out = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
            return float(out.strip().split("=")[1].replace("'C", ""))
        except:
            return None

    def get_uptime():
        try:
            with open("/proc/uptime", "r") as f:
                return float(f.readline().split()[0])
        except:
            return None

    def get_rssi():
        try:
            out = subprocess.check_output(["iwconfig", "wlan0"]).decode()
            for line in out.split("\n"):
                if "Signal level" in line:
                    return int(line.split("Signal level=")[1].split(" ")[0])
        except:
            return None

    def get_latency():
        try:
            out = subprocess.check_output(["ping", "-c", "1", "-W", "1", "ferrix.local"]).decode()
            for line in out.split("\n"):
                if "time=" in line:
                    return float(line.split("time=")[1].split(" ")[0])
        except:
            return None

    return {
        "cpu_temp": get_temp(),
        "uptime": get_uptime(),
        "rssi": get_rssi(),
        "latency_ms": get_latency()
    }

def post_payload(data):
    timestamp = datetime.now().strftime('%H:%M:%S')
    for url in ENDPOINTS:
        try:
            resp = requests.post(url, json=data, timeout=5)
            POST_HISTORY.append((url.split('//')[1].split('.')[0], resp.status_code, timestamp))
        except Exception as e:
            POST_HISTORY.append((url.split('//')[1].split('.')[0], "ERR", timestamp))
    while len(POST_HISTORY) > 5:
        POST_HISTORY.pop(0)

    # Write last known payload to local file for /health server
    try:
        os.makedirs(os.path.dirname(LOCAL_DUMP_PATH), exist_ok=True)
        with open(LOCAL_DUMP_PATH, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("[!] Failed to write local latest.json:", e)

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

# ---- Main Loop ----
bus = SMBus(1)

while True:
    clear()

    # Read AQI5
    aqi_readings = {gas: read_ads1015(bus, cfg) for gas, cfg in CHANNEL_CONFIGS.items()}

    # Read ENV3
    env = {
        "temp": round(bme.temperature, 1),
        "humidity": round(bme.relative_humidity, 1),
        "pressure": round(bme.pressure, 1),
        "gas": round(bme.gas, 1)
    }

    # System health
    health = collect_health()

    # Combine
    payload = {
        "device": DEVICE_ID,
        "ts": int(time.time()),
        "aqi5": aqi_readings,
        "env3": env,
        "health": health
    }

    # POST + dump
    post_payload(payload)

    # Display
    print("╔═══════════════ FIREMARK STATUS ═════════════════╗")
    print(f"║  Device: {DEVICE_ID:<41}║")
    print(f"║  CO: {aqi_readings['CO']:>6}  NH3: {aqi_readings['NH3']:>6}  NO2: {aqi_readings['NO2']:>6}              ║")
    print(f"║  Temp: {env['temp']:>5}°C   Hum: {env['humidity']:>5}%   Pressure: {env['pressure']:>7} hPa  ║")
    print(f"║  VOC Gas: {env['gas']:>7} ohms                             ║")
    print("╠═══════════════ SYSTEM HEALTH ═══════════════════╣")
    print(f"║  CPU Temp: {health['cpu_temp']}°C  RSSI: {health['rssi']}dBm  Latency: {health['latency_ms']}ms  ║")
    print("╠══════════════ POST HISTORY (Last 5) ═════════════╣")
    for name, status, ts in reversed(POST_HISTORY):
        stat = "[✓]" if status == 200 else "[X]"
        print(f"║  {stat} {name:<8} {str(status):<8} @ {ts}                    ║")
    print("╚══════════════════════════════════════════════════╝")

    time.sleep(30)
