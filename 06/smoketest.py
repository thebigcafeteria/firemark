from smbus2 import SMBus
import time

I2C_ADDR = 0x64

# Register addresses (8-bit from MikroElektronika driver)
REG_STATUS              = 0x00
REG_INT_MASK            = 0x01
REG_GPIO_DRV            = 0x02
REG_SW_RESET            = 0x0F
REG_MODE                = 0x10
REG_SLOT_EN             = 0x11
REG_FSAMPLE             = 0x12
REG_PD_LED_SELECT       = 0x14
REG_NUM_AVG             = 0x15
REG_INT_SEQ_A           = 0x17
REG_SLOTA_CH1_OFFSET    = 0x18
REG_SLOTA_CH2_OFFSET    = 0x19
REG_SLOTA_CH3_OFFSET    = 0x1A
REG_SLOTA_CH4_OFFSET    = 0x1B
REG_INT_SEQ_B           = 0x1D
REG_SLOTB_CH1_OFFSET    = 0x1E
REG_SLOTB_CH2_OFFSET    = 0x1F
REG_SLOTB_CH3_OFFSET    = 0x20
REG_SLOTB_CH4_OFFSET    = 0x21
REG_ILED3_COARSE        = 0x22
REG_ILED1_COARSE        = 0x23
REG_ILED2_COARSE        = 0x24
REG_ILED_FINE           = 0x25
REG_SLOTA_LED_PULSE     = 0x30
REG_SLOTA_NUM_PULSES    = 0x31
REG_SLOTB_LED_PULSE     = 0x35
REG_SLOTB_NUM_PULSES    = 0x36
REG_SLOTA_AFE_WINDOW    = 0x39
REG_SLOTB_AFE_WINDOW    = 0x3B
REG_AFE_PWR_CFG1        = 0x3C
REG_SLOTA_TIA_CFG       = 0x42
REG_SLOTA_AFE_CFG       = 0x43
REG_SLOTB_TIA_CFG       = 0x44
REG_SLOTB_AFE_CFG       = 0x45
REG_AFE_PWR_CFG2        = 0x54
REG_MATH                = 0x58
REG_DATA_ACCESS_CTL     = 0x5F
REG_SLOTA_CH1           = 0x64
REG_SLOTA_CH2           = 0x65
REG_SLOTA_CH3           = 0x66
REG_SLOTA_CH4           = 0x67

# Basic register helpers

def write_reg16(bus, reg, value):
    bus.write_i2c_block_data(I2C_ADDR, reg, [value >> 8, value & 0xFF])


def read_reg16(bus, reg):
    data = bus.read_i2c_block_data(I2C_ADDR, reg, 2)
    return (data[0] << 8) | data[1]


def set_bit(bus, reg, bit, val):
    tmp = read_reg16(bus, reg)
    if val:
        tmp |= (1 << bit)
    else:
        tmp &= ~(1 << bit)
    write_reg16(bus, reg, tmp)


def soft_reset(bus):
    write_reg16(bus, REG_SW_RESET, 0x0001)
    time.sleep(0.1)


def set_mode(bus, mode):
    write_reg16(bus, REG_MODE, mode & 0x03)


def default_cfg(bus):
    sequence = [
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
    for reg, val in sequence:
        write_reg16(bus, reg, val)

    set_mode(bus, 1)  # program mode
    set_bit(bus, 0x4B, 7, 1)  # SAMPLE_CLK bit 7
    set_bit(bus, REG_DATA_ACCESS_CTL, 0, 1)
    set_bit(bus, REG_INT_MASK, 5, 0)
    set_bit(bus, REG_INT_MASK, 6, 1)
    set_bit(bus, REG_INT_MASK, 8, 1)
    set_bit(bus, REG_GPIO_DRV, 0, 1)
    set_bit(bus, REG_GPIO_DRV, 1, 1)
    set_bit(bus, REG_GPIO_DRV, 2, 1)
    write_reg16(bus, REG_SLOT_EN, 0x3001)
    set_mode(bus, 2)  # normal mode


def read_slot_a(bus):
    # enable data access for slot A
    set_bit(bus, REG_DATA_ACCESS_CTL, 1, 1)
    values = [read_reg16(bus, reg) for reg in (REG_SLOTA_CH1, REG_SLOTA_CH2,
                                               REG_SLOTA_CH3, REG_SLOTA_CH4)]
    set_bit(bus, REG_DATA_ACCESS_CTL, 1, 0)
    return values


with SMBus(1) as bus:
    print("Initializing Smoke 2 Click (ADPD188BI)...")
    soft_reset(bus)
    set_mode(bus, 0)  # idle
    devid = read_reg16(bus, 0x08)
    print(f"Device ID: 0x{devid:04X}")
    default_cfg(bus)
    print("Starting readout...")

    while True:
        try:
            vals = read_slot_a(bus)
            print("CH1=%d  CH2=%d  CH3=%d  CH4=%d" % tuple(vals))
        except Exception as e:
            print(f"Error reading sensor: {e}")
        time.sleep(2)

