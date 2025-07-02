# Smoke 2 Click (ADPD188BI) – Direct I2C Config + Read in Python

from smbus2 import SMBus
import time

I2C_ADDR = 0x64  # Smoke 2 Click (ADPD188BI) default address

# Register map (8-bit addresses)
REG_STATUS = 0x00
REG_INT_MASK = 0x01
REG_GPIO_DRV = 0x02
REG_SW_RESET = 0x0F
REG_MODE = 0x10
REG_SLOT_EN = 0x11
REG_PD_LED_SELECT = 0x14
REG_SAMPLE_CLK = 0x4B
REG_DATA_ACCESS_CTL = 0x5F
REG_SLOTA_CH1 = 0x64
REG_SLOTA_CH2 = 0x65
REG_SLOTA_CH3 = 0x66
REG_SLOTA_CH4 = 0x67

def write_reg16(bus, reg, value):
    """Write a 16-bit value to an 8-bit register."""
    bus.write_i2c_block_data(I2C_ADDR, reg, [value >> 8, value & 0xFF])

def read_reg16(bus, reg):
    """Read a 16-bit value from an 8-bit register."""
    res = bus.read_i2c_block_data(I2C_ADDR, reg, 2)
    return (res[0] << 8) | res[1]

def set_bit(bus, reg, bit, val):
    current = read_reg16(bus, reg)
    if val:
        current |= 1 << bit
    else:
        current &= ~(1 << bit)
    write_reg16(bus, reg, current)

def default_cfg(bus):
    """Apply the Smoke 2 Click default configuration."""
    sequence = [
        (0x11, 0x30A9),
        (0x12, 0x0200),
        (0x14, 0x011D),
        (0x15, 0x0000),
        (0x17, 0x0009),
        (0x18, 0x0000),
        (0x19, 0x3FFF),
        (0x1A, 0x3FFF),
        (0x1B, 0x3FFF),
        (0x1D, 0x0009),
        (0x1E, 0x0000),
        (0x1F, 0x3FFF),
        (0x20, 0x3FFF),
        (0x21, 0x3FFF),
        (0x22, 0x3539),
        (0x23, 0x3536),
        (0x24, 0x1530),
        (0x25, 0x630C),
        (0x30, 0x0320),
        (0x31, 0x040E),
        (0x35, 0x0320),
        (0x36, 0x040E),
        (0x39, 0x22F0),
        (0x3B, 0x22F0),
        (0x3C, 0x31C6),
        (0x42, 0x1C34),
        (0x43, 0xADA5),
        (0x44, 0x1C34),
        (0x45, 0xADA5),
        (0x58, 0x0544),
        (0x54, 0x0AA0),
        (0x5F, 0x0007),
    ]
    for reg, val in sequence:
        write_reg16(bus, reg, val)

    write_reg16(bus, REG_MODE, 0x0001)  # Program mode
    set_bit(bus, REG_SAMPLE_CLK, 7, 1)
    set_bit(bus, REG_DATA_ACCESS_CTL, 0, 1)
    set_bit(bus, REG_INT_MASK, 5, 0)
    set_bit(bus, REG_INT_MASK, 6, 1)
    set_bit(bus, REG_INT_MASK, 8, 1)
    set_bit(bus, REG_GPIO_DRV, 0, 1)
    set_bit(bus, REG_GPIO_DRV, 1, 1)
    set_bit(bus, REG_GPIO_DRV, 2, 1)
    write_reg16(bus, REG_SLOT_EN, 0x3001)
    write_reg16(bus, REG_MODE, 0x0002)  # Normal mode

with SMBus(1) as bus:
    print("Initializing Smoke 2 Click (ADPD188BI)...")
    write_reg16(bus, REG_SW_RESET, 0x0001)
    time.sleep(0.1)
    default_cfg(bus)

    print("Reading Smoke Sensor Values:")
    while True:
        try:
            readings = []
            for reg in range(REG_SLOTA_CH1, REG_SLOTA_CH4 + 1):
                val = read_reg16(bus, reg)
                readings.append(f"0x{reg:02X}: {val}")
            print("  ".join(readings))
        except Exception as e:
            print(f"Error reading sensor: {e}")
        time.sleep(2)
