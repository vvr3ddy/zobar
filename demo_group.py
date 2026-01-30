"""Demo using the new ProgressBarGroup API."""
import sys
import time
import os

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import ProgressBarGroup

def run_demo():
    """Demo the new ProgressBarGroup feature."""
    print("\n\033[1m🚀 Zobar Progress Bar Group Demo\033[0m\n")
    print("Using the new first-class parallel progress API\n")

    with ProgressBarGroup() as group:
        # Create multiple progress bars
        bar1 = group.add_bar(total=100, desc="Downloading", bar_style='gradient', color='cyan', width=30)
        bar2 = group.add_bar(total=50, desc="Processing", bar_style='classic', color='green', width=30)
        bar3 = group.add_bar(total=75, desc="Uploading", bar_style='braille', color='magenta', width=30)

        # Simulate work
        while any(p.current < p.total for p in [bar1, bar2, bar3]):
            # Update bars at different rates
            if bar1.current < bar1.total:
                bar1.update(1)
                if bar1.current % 20 == 0:
                    bar1.set_suffix(f"file={bar1.current // 20}")

            if bar2.current < bar2.total and bar2.current < bar1.current // 2:
                bar2.update(1)
                if bar2.current % 10 == 0:
                    bar2.set_suffix(f"item={bar2.current}")

            if bar3.current < bar3.total and bar1.current > 50:
                bar3.update(1)
                if bar3.current % 15 == 0:
                    bar3.set_suffix(f"chunk={bar3.current // 15}")

            time.sleep(0.03)

    print("\n✨ \033[1mAll tasks complete!\033[0m\n")

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\n")
        print("Demo cancelled.")
