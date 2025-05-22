#!/usr/bin/env python3
"""
Helper script to create test files for the memSim virtual memory simulator
"""

import struct
import random

def create_backing_store(filename="BACKING_STORE.bin", size=65536):
    """Create a sample backing store file"""
    with open(filename, 'wb') as f:
        # Create a pattern where each page has a recognizable pattern
        for page in range(256):  # 256 pages of 256 bytes each
            page_data = bytearray(256)
            for i in range(256):
                # Create a pattern: page number in high byte, offset in low byte
                # This makes it easy to verify correctness
                value = ((page & 0xFF) << 8) | (i & 0xFF)
                page_data[i] = (value & 0xFF)
            f.write(page_data)
    print(f"Created {filename} with {size} bytes")

def create_test_addresses(filename="addresses.txt", count=1000):
    """Create a test file with random addresses"""
    with open(filename, 'w') as f:
        for _ in range(count):
            # Generate 16-bit addresses
            address = random.randint(0, 65535)
            f.write(f"{address}\n")
    print(f"Created {filename} with {count} addresses")

def create_simple_test_addresses(filename="simple_addresses.txt"):
    """Create a simple test file with predictable addresses"""
    addresses = [
        16384,  # Page 64, offset 0
        16639,  # Page 64, offset 255  
        32768,  # Page 128, offset 0
        49152,  # Page 192, offset 0
        16640,  # Page 65, offset 0
        16384,  # Page 64, offset 0 (repeat)
    ]
    
    with open(filename, 'w') as f:
        for addr in addresses:
            f.write(f"{addr}\n")
    print(f"Created {filename} with simple test addresses")

def main():
    print("Creating test files for memSim...")
    create_backing_store()
    create_test_addresses()
    create_simple_test_addresses()
    print("Done! You can now test memSim with:")
    print("  ./memSim addresses.txt")
    print("  ./memSim simple_addresses.txt 4 FIFO")
    print("  ./memSim simple_addresses.txt 4 LRU")

if __name__ == "__main__":
    main()