#!/usr/bin/env python3

import argparse
import importlib.util
import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Optional


GPIOZERO_AVAILABLE = importlib.util.find_spec("gpiozero") is not None
RPIGPIO_AVAILABLE = importlib.util.find_spec("RPi.GPIO") is not None
SERIAL_AVAILABLE = importlib.util.find_spec("serial") is not None

if GPIOZERO_AVAILABLE:
    from gpiozero import LED as GPIOZeroLED

if RPIGPIO_AVAILABLE:
    import RPi.GPIO as RPiGPIO

if SERIAL_AVAILABLE:
    import serial


LOGGER = logging.getLogger("firemark-click-monitor")


class LedDriver:
    def on(self) -> None:
        raise NotImplementedError

    def off(self) -> None:
        raise NotImplementedError

    def blink_once(self, duration: float = 0.2) -> None:
        self.on()
        time.sleep(duration)
        self.off()


class GPIOZeroLedDriver(LedDriver):
    def __init__(self, pin: int) -> None:
        self._led = GPIOZeroLED(pin)

    def on(self) -> None:
        self._led.on()

    def off(self) -> None:
        self._led.off()


class RPIGPIOLedDriver(LedDriver):
    def __init__(self, pin: int) -> None:
        self._pin = pin
        RPiGPIO.setwarnings(False)
        RPiGPIO.setmode(RPiGPIO.BCM)
        RPiGPIO.setup(self._pin, RPiGPIO.OUT, initial=RPiGPIO.LOW)

    def on(self) -> None:
        RPiGPIO.output(self._pin, RPiGPIO.HIGH)

    def off(self) -> None:
        RPiGPIO.output(self._pin, RPiGPIO.LOW)


def build_led_driver(pin: int) -> LedDriver:
    if GPIOZERO_AVAILABLE:
        return GPIOZeroLedDriver(pin)
    if RPIGPIO_AVAILABLE:
        return RPIGPIOLedDriver(pin)
    raise RuntimeError("No GPIO backend available (install gpiozero or RPi.GPIO)")


class SpeakerDriver:
    def say(self, text: str) -> None:
        raise NotImplementedError


class SerialSpeakerDriver(SpeakerDriver):
    def __init__(self, port: str, baudrate: int, voice: int, volume: int) -> None:
        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        self._voice = voice
        self._volume = volume
        self._configure()

    def _configure(self) -> None:
        # Command set based on MikroE Speaker 2 Click (UART text-to-speech).
        # Adjust values to match the MikroSDK definitions if needed.
        self._write_command(f"N{self._voice}")
        self._write_command(f"V{self._volume}")

    def _write_command(self, command: str) -> None:
        self._serial.write(f"{command}\n".encode("utf-8"))
        time.sleep(0.05)

    def say(self, text: str) -> None:
        self._write_command(f"S{text}")


class EspeakSpeakerDriver(SpeakerDriver):
    def __init__(self, voice: str, volume: int) -> None:
        self._voice = voice
        self._volume = volume

    def say(self, text: str) -> None:
        subprocess.run(
            [
                "espeak",
                "-v",
                self._voice,
                "-a",
                str(self._volume),
                text,
            ],
            check=False,
        )


def build_speaker_driver(args: argparse.Namespace) -> Optional[SpeakerDriver]:
    if args.speaker_backend == "serial":
        if not SERIAL_AVAILABLE:
            raise RuntimeError("pyserial not available for serial speaker backend")
        return SerialSpeakerDriver(
            port=args.speaker_port,
            baudrate=args.speaker_baudrate,
            voice=args.speaker_voice,
            volume=args.speaker_volume,
        )
    if args.speaker_backend == "espeak":
        return EspeakSpeakerDriver(
            voice=args.speaker_voice_name,
            volume=args.speaker_volume,
        )
    return None


def get_default_gateway() -> Optional[str]:
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        parts = line.split()
        if "via" in parts:
            via_index = parts.index("via")
            if via_index + 1 < len(parts):
                return parts[via_index + 1]
    return None


def wifi_connected(interface: str) -> bool:
    try:
        result = subprocess.run(
            ["iwgetid", "-r", interface],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        result = subprocess.run(
            ["ip", "-4", "addr", "show", "dev", interface],
            check=False,
            capture_output=True,
            text=True,
        )
        return "inet " in result.stdout

    return result.returncode == 0 and result.stdout.strip() != ""


def ping_host(host: str) -> bool:
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", host],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False

    return result.returncode == 0


@dataclass
class MonitorConfig:
    interface: str
    wifi_led_pin: int
    ping_led_pin: int
    ping_interval_s: float
    ping_flash_s: float
    speak_interval_s: float
    phrase: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor Pi click hat bargraph and speaker clicks.",
    )
    parser.add_argument("--interface", default="wlan0")
    parser.add_argument("--wifi-led-pin", type=int, default=17)
    parser.add_argument("--ping-led-pin", type=int, default=27)
    parser.add_argument("--ping-interval", type=float, default=30.0)
    parser.add_argument("--ping-flash", type=float, default=0.2)
    parser.add_argument("--speak-interval", type=float, default=60.0)
    parser.add_argument("--phrase", default="give me some ham")
    parser.add_argument(
        "--speaker-backend",
        choices=("serial", "espeak", "none"),
        default="serial" if SERIAL_AVAILABLE else "espeak",
    )
    parser.add_argument("--speaker-port", default="/dev/ttyS0")
    parser.add_argument("--speaker-baudrate", type=int, default=9600)
    parser.add_argument(
        "--speaker-voice",
        type=int,
        default=0,
        help="Numeric voice ID for the Speaker 2 Click UART command set.",
    )
    parser.add_argument(
        "--speaker-voice-name",
        default="en+m7",
        help="Voice name for the espeak backend.",
    )
    parser.add_argument("--speaker-volume", type=int, default=200)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s")
    config = MonitorConfig(
        interface=args.interface,
        wifi_led_pin=args.wifi_led_pin,
        ping_led_pin=args.ping_led_pin,
        ping_interval_s=args.ping_interval,
        ping_flash_s=args.ping_flash,
        speak_interval_s=args.speak_interval,
        phrase=args.phrase,
    )

    wifi_led = build_led_driver(config.wifi_led_pin)
    ping_led = build_led_driver(config.ping_led_pin)
    speaker = build_speaker_driver(args)
    gateway = get_default_gateway()

    last_ping = 0.0
    last_speak = 0.0

    LOGGER.info("Starting click monitor (gateway=%s)", gateway)

    while True:
        if wifi_connected(config.interface):
            wifi_led.on()
        else:
            wifi_led.off()

        now = time.monotonic()
        if gateway and (now - last_ping) >= config.ping_interval_s:
            last_ping = now
            if ping_host(gateway):
                LOGGER.info("Gateway ping succeeded (%s)", gateway)
                ping_led.blink_once(config.ping_flash_s)
            else:
                LOGGER.warning("Gateway ping failed (%s)", gateway)

        if speaker and (now - last_speak) >= config.speak_interval_s:
            last_speak = now
            LOGGER.info("Speaking phrase")
            speaker.say(config.phrase)

        time.sleep(0.5)


if __name__ == "__main__":
    main()
