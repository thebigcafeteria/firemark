# ens161_probe.py – Brute-force I2C probing script for ENS161 or unknown Click boards

import smbus2
import time

bus = smbus2.SMBus(1)
common_addresses = list(range(0x03, 0x78))

# Helper to write 2-byte values
def write_reg(addr, reg, value):
    try:
        hi = (value >> 8) & 0xFF
        lo = value & 0xFF
        msg = smbus2.i2c_msg.write(addr, [reg, hi, lo])
        bus.i2c_rdwr(msg)
        return True
    except:
        return False

# Helper to read a register block
def read_block(addr, start_reg, length):
    try:
        bus.write_byte(addr, start_reg)
        data = bus.read_i2c_block_data(addr, start_reg, length)
        return data
    except:
        return []

print("[🔍] Starting I2C probe...")

for addr in common_addresses:
    try:
        bus.write_quick(addr)
        print(f"[✓] Device detected at 0x{addr:02X}")

        print(f"    → Sending known wakeup writes to 0x{addr:02X}...")
        write_reg(addr, 0x4B, 0x80)  # try Smoke2 clock enable
        write_reg(addr, 0x0F, 0x01)  # try software reset
        write_reg(addr, 0x10, 0x01)  # try program mode

        print(f"    → Reading registers 0x00–0x1F...")
        regs = read_block(addr, 0x00, 32)
        for i in range(0, len(regs), 8):
            chunk = regs[i:i+8]
            if any(b not in (0x00, 0xFF) for b in chunk):
                hex_chunk = ' '.join(f"{b:02X}" for b in chunk)
                print(f"    [0x{addr:02X}] 0x{i:02X}: {hex_chunk}")
    except:
        pass

print("[✓] Probe complete.")
