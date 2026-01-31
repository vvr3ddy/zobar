"""Demo ETA smoothing and timestamp features."""
import sys
import os

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar
import time


def run_demo():
    """Demo ETA smoothing with exponential moving average."""
    print("\n\033[1m🚀 Zobar ETA Smoothing Demo\033[0m")
    print("Comparing no smoothing vs EMA smoothing for stable ETA\n")

    # Demo 1: No smoothing (ETA may jitter)
    print("\033[1m1. No smoothing (smoothing=1.0)\033[0m")
    print("Notice how ETA might fluctuate with varying processing times:\n")
    with AnimatedProgressBar(total=100, desc="No Smoothing", smoothing=1.0, log_timestamp=True) as pbar:
        for i in range(100):
            # Simulate variable processing time
            delay = 0.02 if i % 10 != 5 else 0.15
            time.sleep(delay)
            pbar.update(1)

    print()

    # Demo 2: Heavy smoothing (ETA very stable)
    print("\033[1m2. Heavy smoothing (smoothing=0.1)\033[0m")
    print("ETA is smoothed heavily for stability:\n")
    with AnimatedProgressBar(total=100, desc="Heavy Smoothing", smoothing=0.1, log_timestamp=True) as pbar:
        for i in range(100):
            # Same variable processing time
            delay = 0.02 if i % 10 != 5 else 0.15
            time.sleep(delay)
            pbar.update(1)

    print()

    # Demo 3: Default smoothing (balanced)
    print("\033[1m3. Default smoothing (smoothing=0.3)\033[0m")
    print("Balanced between responsiveness and stability:\n")
    with AnimatedProgressBar(total=100, desc="Default Smoothing", smoothing=0.3, log_timestamp=True) as pbar:
        for i in range(100):
            # Same variable processing time
            delay = 0.02 if i % 10 != 5 else 0.15
            time.sleep(delay)
            pbar.update(1)

    print("\n✨ \033[1mDemo complete!\033[0m")
    print("Note: In TTY mode, you'll see the visual progress bars with smoothed ETA.")
    print("With log_timestamp=True, non-TTY output includes timestamps.\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        print("Demo cancelled.")
