"""Demo RGB/true color support for custom colors."""
import sys
import os
import time

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar, ProgressBarGroup


def run_demo():
    """Demo custom color support."""
    print("\n\033[1m🚀 Zobar Custom Color Demo\033[0m")
    print("Using RGB tuples and hex colors for unlimited color options\n")

    print("\033[1m1. RGB Tuple Colors\033[0m")
    print("Vibrant custom colors using RGB tuples:\n")

    colors_rgb = [
        ((255, 87, 51), "Orange"),
        ((51, 255, 87), "Lime Green"),
        ((87, 51, 255), "Purple"),
        ((255, 51, 200), "Hot Pink"),
    ]

    for color, name in colors_rgb:
        with AnimatedProgressBar(total=50, desc=name, color=color, width=30) as pbar:
            for i in range(50):
                time.sleep(0.015)
                pbar.update(1)

    print()

    # Demo 2: Hex colors
    print("\033[1m2. Hex Color Strings\033[0m")
    print("Using web-style hex color codes:\n")

    colors_hex = [
        ("#FF6B6B", "Coral Red"),
        ("#4ECDC4", "Turquoise"),
        ("#FFE66D", "Sunny Yellow"),
        ("#95E1D3", "Mint Green"),
    ]

    for color, name in colors_hex:
        with AnimatedProgressBar(total=50, desc=name, color=color, width=30) as pbar:
            for i in range(50):
                time.sleep(0.015)
                pbar.update(1)

    print()

    # Demo 3: Rainbow parallel bars
    print("\033[1m3. Rainbow Parallel Bars\033[0m")
    print("Multiple custom colors in parallel:\n")

    rainbow = [
        ("#FF0000", "Red"),
        ("#FF7F00", "Orange"),
        ("#FFFF00", "Yellow"),
        ("#00FF00", "Green"),
        ("#0000FF", "Blue"),
        ("#8B00FF", "Violet"),
    ]

    with ProgressBarGroup() as group:
        bars = []
        for color, name in rainbow:
            bar = group.add_bar(total=40, desc=name, color=color, width=25)
            bars.append(bar)

        for i in range(40):
            time.sleep(0.03)
            for bar in bars:
                bar.update(1)

    print("\n✨ \033[1mCustom color demo complete!\033[0m")
    print("Now you can match any brand color or theme!\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        print("Demo cancelled.")
