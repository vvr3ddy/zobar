"""Demo showing human-readable unit auto-formatting."""
import sys
import time
import os

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar


def run_demo():
    """Demo unit scaling features."""
    print("\n\033[1m🚀 Zobar Unit Scaling Demo\033[0m")
    print("Auto-formatting large numbers for better readability\n")

    # Demo 1: No scaling (default)
    print("\033[1m1. No scaling (default)\033[0m")
    with AnimatedProgressBar(total=1500000, desc="Items", unit_scale='none') as pbar:
        for i in range(0, 1500000, 15000):
            pbar.update(15000)
            time.sleep(0.0001)

    print()

    # Demo 2: KMG scaling (K/M/B)
    print("\033[1m2. KMG scaling (K, M, B)\033[0m")
    with AnimatedProgressBar(total=1500000, desc="Items", unit_scale='kmg') as pbar:
        for i in range(0, 1500000, 15000):
            pbar.update(15000)
            time.sleep(0.0001)

    print()

    # Demo 3: Binary scaling (KiB, MiB, GiB)
    print("\033[1m3. Binary scaling for bytes (KiB, MiB, GiB)\033[0m")
    # Simulating a 500 MiB file download
    total_bytes = 500 * 1024 * 1024
    chunk_size = 5 * 1024 * 1024  # 5 MiB chunks
    with AnimatedProgressBar(total=total_bytes, desc="Download", unit="B", unit_scale='binary') as pbar:
        for i in range(0, total_bytes, chunk_size):
            pbar.update(chunk_size)
            time.sleep(0.02)

    print()

    # Demo 4: Very large numbers with KMG
    print("\033[1m4. Very large numbers (billions)\033[0m")
    with AnimatedProgressBar(total=2500000000, desc="Records", unit_scale='kmg') as pbar:
        for i in range(0, 2500000000, 25000000):
            pbar.update(25000000)
            time.sleep(0.002)

    print("\n✨ \033[1mUnit scaling demo complete!\033[0m\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        print("Demo cancelled.")
