# firemark01_health_server.py – lightweight Flask app serving live health status

from flask import Flask, jsonify
import subprocess
import time
import socket

app = Flask(__name__)

DEVICE_ID = socket.gethostname()


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

    def get_ip():
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "unknown"

    return {
        "device": DEVICE_ID,
        "ts": int(time.time()),
        "ip": get_ip(),
        "uptime": get_uptime(),
        "cpu_temp": get_temp(),
        "rssi": get_rssi(),
        "status": "ok"
    }


@app.route("/health")
def health():
    return jsonify(collect_health())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
