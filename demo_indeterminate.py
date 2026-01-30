"""Demo using indeterminate progress mode (unknown total)."""
import sys
import time
import os

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar


def run_demo():
    """Demo indeterminate progress mode."""
    print("\n\033[1m🚀 Zobar Indeterminate Progress Demo\033[0m")
    print("Processing items of unknown count...\n")

    # Simulate processing where we don't know the total upfront
    with AnimatedProgressBar(total=None, desc="Streaming", color='cyan') as pbar:
        items_processed = 0
        for i in range(75):  # In real use, we wouldn't know this number
            time.sleep(0.04)
            items_processed += 1
            pbar.update(1)
            if i % 15 == 0:
                pbar.set_suffix(f"batch {i // 15 + 1}")

    print("✓ Streaming complete\n")

    # Another example: polling for completion
    print("Polling for external process completion...\n")
    with AnimatedProgressBar(total=None, desc="Waiting", color='green') as pbar:
        for i in range(50):
            time.sleep(0.03)
            pbar.update(1)
            pbar.set_suffix(f"check #{i + 1}")

    print("✓ Process completed\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        print("Demo cancelled.")
