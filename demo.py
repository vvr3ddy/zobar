import time
import sys
import os

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar

def run_demo():
    demos = [
        ("gradient", "cyan", "Training Model"),
        ("classic", "green", "Downloading"),
        ("braille", "magenta", "Processing"),
        ("circles", "blue", "Uploading"),
        ("blocks", "yellow", "Compiling"),
    ]

    print("\n\033[1m🚀 Zobar Demo\033[0m - Zero-dependency Progress Bar\n")

    for style, color, desc in demos:
        # Create a progress bar for each style
        with AnimatedProgressBar(total=100, desc=desc, bar_style=style, color=color, width=40) as pbar:
            for i in range(100):
                time.sleep(0.04)  # 4 seconds per bar
                
                # Demonstrate suffix updates
                if i % 20 == 0:
                    loss = 0.5 - (i * 0.004)
                    pbar.set_suffix(f"loss={loss:.3f}")
                
                pbar.update(1)
        
        time.sleep(0.2) # Pause between bars

    print("\n✨ \033[1mReady for PyPI!\033[0m\n")

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\n\033[K")
        print("Demo cancelled.")
