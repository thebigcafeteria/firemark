import time
import random
import qwiic_alphanumeric


def log_and_display(display, prev_msg, msg, next_msg):
    print(f"Prev: {prev_msg} | Now: {msg} | Next: {next_msg}")
    display.print(msg)


def brightness_test(display):
    for level in list(range(16)) + list(range(15, -1, -1)):
        display.set_brightness(level)
        time.sleep(0.1)


def blink_test(display):
    for rate in [2.0, 1.0, 0.5, 0.0]:
        display.set_blink_rate(rate)
        time.sleep(2)
    display.set_blink_rate(0)


def speed_test(display):
    for _ in range(40):
        msg = f"{random.randint(0, 9999):04d}"
        display.print(msg)
        print(f"Displaying: {msg}")
        time.sleep(0.05)


def run_cycle(display):
    phases = [
        ("BRI ", brightness_test),
        ("BLNK", blink_test),
        ("FAST", speed_test),
        ("DONE", lambda d: time.sleep(2)),
    ]

    prev = "----"
    for i, (msg, action) in enumerate(phases):
        next_msg = phases[(i + 1) % len(phases)][0]
        log_and_display(display, prev, msg, next_msg)
        action(display)
        prev = msg


def main():
    display = qwiic_alphanumeric.QwiicAlphanumeric()
    if not display.begin(0x70):
        print("Display not found on I2C bus.")
        return
    while True:
        run_cycle(display)


if __name__ == "__main__":
    main()
