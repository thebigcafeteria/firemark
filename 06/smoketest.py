# Smoke 2 Click (ADPD188BI) – Direct I2C Config + Read in Python
#codex
from smbus2 import SMBus
import time

I2C_ADDR = 0x64  # Smoke 2 Click (ADPD188BI) default address

# Register map from ADPD188BI datasheet
REG_SYS_CTL     = 0x0000
REG_OP_MODE     = 0x0001
REG_INT_MASK    = 0x0020
REG_INT_STATUS  = 0x0021
REG_SLOT_EN     = 0x0040
REG_PD_LED_SELECT = 0x004F
REG_CH1         = 0x0014
REG_CH2         = 0x0016

# Helper: set register page
REG_PAGE_SEL = 0x000F

def set_page(bus, page):
    write_reg16(bus, REG_PAGE_SEL, page)
    time.sleep(0.01)

# Helper: write 16-bit to 16-bit register
from smbus2 import i2c_msg

def write_reg16(bus, reg, value):
    data = [reg >> 8, reg & 0xFF, value >> 8, value & 0xFF]
    msg = i2c_msg.write(I2C_ADDR, data)
    bus.i2c_rdwr(msg)

# Helper: read 16-bit from 16-bit register
def read_reg16(bus, reg):
    write = i2c_msg.write(I2C_ADDR, [reg >> 8, reg & 0xFF])
    read = i2c_msg.read(I2C_ADDR, 2)
    bus.i2c_rdwr(write, read)
    res = list(read)
    return (res[0] << 8) | res[1]

with SMBus(1) as bus:
    print("Initializing Smoke 2 Click (ADPD188BI)...")

    # ----------------------
    # PAGE 0x00 – Reset + Program Mode
    # ----------------------
    set_page(bus, 0x00)
    write_reg16(bus, REG_SYS_CTL, 0x0002)  # Soft reset
    time.sleep(0.1)
    write_reg16(bus, REG_OP_MODE, 0x0002)  # Program mode
    time.sleep(0.05)

    # ----------------------
    # PAGE 0x01 – LED + Signal Chain Config (Minimal Clock + LED Init)
    # ----------------------
    set_page(bus, 0x01)
    time.sleep(0.01)
    write_reg16(bus, 0x0100, 0x1010)  # Shorter pulse width
    write_reg16(bus, 0x0101, 0x1010)  # Moderate LED current
    write_reg16(bus, 0x0102, 0x0008)  # Fewer pulses
    write_reg16(bus, 0x0103, 0x0001)  # Sample every cycle  # Sample freq
    time.sleep(0.01)

    write_reg16(bus, 0x0053, 0x0001)  # LED pulse count
    write_reg16(bus, 0x0054, 0x0001)  # LED offset
    write_reg16(bus, 0x0104, 0x0003)  # Minimal viable clock bits
    val = read_reg16(bus, 0x0104)
    print(f"Post-write clock register 0x0104: 0x{val:04X}")  # Clock settings

    write_reg16(bus, 0x004F, 0x0030)  # IR + GREEN
    write_reg16(bus, 0x0050, 0x0001)  # Repeat LED1
    write_reg16(bus, 0x0051, 0x0001)  # Repeat LED2
    write_reg16(bus, 0x0052, 0x0001)  # Repeat LED3
    time.sleep(0.01)

    # ----------------------
    # SLOT A Setup
    # ----------------------
    write_reg16(bus, 0x0110, 0x0010)  # Slot A Start
    write_reg16(bus, 0x0111, 0x0040)  # Slot A End
    write_reg16(bus, 0x0112, 0x0003)  # Enable Ch1 + Ch2
    write_reg16(bus, 0x0040, 0x0001)  # Enable Slot A

    # ----------------------
    # PAGE 0x02 – AFE + Offset
    # ----------------------
    set_page(bus, 0x02)
    time.sleep(0.01)
    write_reg16(bus, 0x0200, 0x0000)  # AFE offset
    write_reg16(bus, 0x0201, 0x0002)  # Gain = 100k

    # ----------------------
    # PAGE 0x01 – FIFO, Interrupt, Output Buffers
    # ----------------------
    set_page(bus, 0x01)
    time.sleep(0.01)
    write_reg16(bus, 0x0004, 0x0019)  # FIFO config
    write_reg16(bus, 0x0006, 0x0400)  # Decimation
    write_reg16(bus, 0x010A, 0x0000)  # Force register mode instead of FIFO  # Output buffer config
    write_reg16(bus, 0x010B, 0x0001)
    write_reg16(bus, 0x0020, 0x8000)  # Clear INT mask
    write_reg16(bus, 0x0021, 0x8000)  # Clear INT status
    write_reg16(bus, 0x000F, 0x0001)  # Page again
    write_reg16(bus, REG_PD_LED_SELECT, 0x0030)

    # ----------------------
    # PAGE 0x00 – Start Sampling
    # ----------------------
    set_page(bus, 0x00)
    time.sleep(0.01)
    write_reg16(bus, REG_OP_MODE, 0x0001)  # Normal sampling
    time.sleep(0.1)

    # ----------------------
    # Begin Readout
    # ----------------------
    set_page(bus, 0x02)
    print("Reading Smoke Sensor Values:")
    current_mode = read_reg16(bus, REG_OP_MODE)
    print(f"REG_OP_MODE current value: 0x{current_mode:04X}")
    fifo_count = read_reg16(bus, 0x0000)
    print(f"FIFO Samples (from 0x0000 upper byte): {(fifo_count >> 8) & 0xFF}")
    int_status = read_reg16(bus, 0x0021)
    print(f"INT_STATUS: 0x{int_status:04X}")
    print("Reading registers 0x0064 to 0x0067...")

    while True:
        try:
            # Page 0x00 contains the photodiode data registers
            set_page(bus, 0x00)
            time.sleep(0.05)
            for reg in range(0x0064, 0x0068):
                val = read_reg16(bus, reg)
                print(f"0x{reg:04X}: {val}", end='  ')
            print("")
        except Exception as e:
            print(f"Error reading sensor: {e}")

        time.sleep(2)
