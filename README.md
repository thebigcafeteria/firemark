# Firemark Display Test

This repository includes a utility `alpha-tester.py` for exercising a SparkFun Qwiic Alphanumeric display.

## Requirements

Install the SparkFun Qwiic Python package, which provides the required `qwiic_i2c` module:

```bash
pip install sparkfun-qwiic
```

## Running the test

Connect your Qwiic Alphanumeric display to the Raspberry Pi I2C bus (default address `0x70`).
Execute the script with Python 3:

```bash
python3 alpha-tester.py
```

The program cycles through brightness, blink, and update speed tests. For each stage it prints
what is currently shown, what was previously displayed, and what comes next. The full cycle
runs for roughly 15–20 seconds before repeating.
