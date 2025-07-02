# Smoke 2 Click (ADPD188BI) – Simple initialization and readout using
# MikroElektronika register addresses.

import time
from smbus2 import SMBus

I2C_ADDR = 0x64  # Default I2C address for Smoke 2 Click

# 8-bit register addresses from MikroElektronika driver
REG_STATUS = 0x00
REG_INT_MASK = 0x01
REG_GPIO_DRV = 0x02
REG_SW_RESET = 0x0F
REG_MODE = 0x10
REG_SLOT_EN = 0x11
REG_FSAMPLE = 0x12
REG_PD_LED_SELECT = 0x14
REG_NUM_AVG = 0x15
REG_INT_SEQ_A = 0x17
REG_SLOTA_CH1_OFFSET = 0x18
REG_SLOTA_CH2_OFFSET = 0x19
REG_SLOTA_CH3_OFFSET = 0x1A
REG_SLOTA_CH4_OFFSET = 0x1B
REG_INT_SEQ_B = 0x1D
REG_SLOTB_CH1_OFFSET = 0x1E
REG_SLOTB_CH2_OFFSET = 0x1F
REG_SLOTB_CH3_OFFSET = 0x20
REG_SLOTB_CH4_OFFSET = 0x21
REG_ILED3_COARSE = 0x22
REG_ILED1_COARSE = 0x23
REG_ILED2_COARSE = 0x24
REG_ILED_FINE = 0x25
REG_SLOTA_LED_PULSE = 0x30
REG_SLOTA_NUM_PULSES = 0x31
REG_SLOTB_LED_PULSE = 0x35
REG_SLOTB_NUM_PULSES = 0x36
REG_SLOTA_AFE_WINDOW = 0x39
REG_SLOTB_AFE_WINDOW = 0x3B
REG_AFE_PWR_CFG1 = 0x3C
REG_SLOTA_TIA_CFG = 0x42
REG_SLOTA_AFE_CFG = 0x43
REG_SLOTB_TIA_CFG = 0x44
REG_SLOTB_AFE_CFG = 0x45
REG_SAMPLE_CLK = 0x4B
REG_AFE_PWR_CFG2 = 0x54
REG_MATH = 0x58
REG_DATA_ACCESS_CTL = 0x5F
REG_FIFO_ACCESS = 0x60
REG_SLOTA_CH1 = 0x64
REG_SLOTA_CH2 = 0x65
REG_SLOTA_CH3 = 0x66
REG_SLOTA_CH4 = 0x67
REG_PAGE_SEL = 0x0F


def write_reg16(bus, reg, value):
    """Write a 16-bit value to an 8-bit register."""
    bus.write_i2c_block_data(I2C_ADDR, reg, [value >> 8, value & 0xFF])


def read_reg16(bus, reg):
    """Read a 16-bit value from an 8-bit register."""
    data = bus.read_i2c_block_data(I2C_ADDR, reg, 2)
    return (data[0] << 8) | data[1]


def set_page(bus, page):
    """Select register page."""
    write_reg16(bus, REG_PAGE_SEL, page)
    time.sleep(0.01)


def set_bit(bus, reg, bit, value):
    """Set or clear a single bit in a 16-bit register."""
    reg_val = read_reg16(bus, reg)
    if value:
        reg_val |= (1 << bit)
    else:
        reg_val &= ~(1 << bit)
    write_reg16(bus, reg, reg_val)


def default_cfg(bus):
    """Apply Smoke 2 Click default configuration."""
    cfg = [
        (REG_SLOT_EN, 0x30A9),
        (REG_FSAMPLE, 0x0200),
        (REG_PD_LED_SELECT, 0x011D),
        (REG_NUM_AVG, 0x0000),
        (REG_INT_SEQ_A, 0x0009),
        (REG_SLOTA_CH1_OFFSET, 0x0000),
        (REG_SLOTA_CH2_OFFSET, 0x3FFF),
        (REG_SLOTA_CH3_OFFSET, 0x3FFF),
        (REG_SLOTA_CH4_OFFSET, 0x3FFF),
        (REG_INT_SEQ_B, 0x0009),
        (REG_SLOTB_CH1_OFFSET, 0x0000),
        (REG_SLOTB_CH2_OFFSET, 0x3FFF),
        (REG_SLOTB_CH3_OFFSET, 0x3FFF),
        (REG_SLOTB_CH4_OFFSET, 0x3FFF),
        (REG_ILED3_COARSE, 0x3539),
        (REG_ILED1_COARSE, 0x3536),
        (REG_ILED2_COARSE, 0x1530),
        (REG_ILED_FINE, 0x630C),
        (REG_SLOTA_LED_PULSE, 0x0320),
        (REG_SLOTA_NUM_PULSES, 0x040E),
        (REG_SLOTB_LED_PULSE, 0x0320),
        (REG_SLOTB_NUM_PULSES, 0x040E),
        (REG_SLOTA_AFE_WINDOW, 0x22F0),
        (REG_SLOTB_AFE_WINDOW, 0x22F0),
        (REG_AFE_PWR_CFG1, 0x31C6),
        (REG_SLOTA_TIA_CFG, 0x1C34),
        (REG_SLOTA_AFE_CFG, 0xADA5),
        (REG_SLOTB_TIA_CFG, 0x1C34),
        (REG_SLOTB_AFE_CFG, 0xADA5),
        (REG_MATH, 0x0544),
        (REG_AFE_PWR_CFG2, 0x0AA0),
        (REG_DATA_ACCESS_CTL, 0x0007),
    ]

    for reg, val in cfg:
        write_reg16(bus, reg, val)

    # Mode and interrupt setup
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


def main():
    with SMBus(1) as bus:
        print("Initializing Smoke 2 Click (ADPD188BI)...")

        # Reset device
        write_reg16(bus, REG_SW_RESET, 0x0001)
        time.sleep(0.1)

        default_cfg(bus)

        print("Reading registers 0x64 to 0x67...")
        while True:
            try:
                set_page(bus, 0x00)
                time.sleep(0.05)
                for reg in range(0x0064, 0x0068):
                    val = read_reg16(bus, reg)
                    print(f"0x{reg:04X}: {val}", end="  ")
                print("")
            except Exception as e:
                print(f"Error reading sensor: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
