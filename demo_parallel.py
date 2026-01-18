import time
import sys
import os
import random

# Ensure we can import zobar if running from source
sys.path.insert(0, os.path.abspath("src"))

from zobar import AnimatedProgressBar

def run_parallel_demo():
    styles = [
        ("gradient", "cyan", "Training Model"),
        ("classic", "green", "Downloading"),
        ("braille", "magenta", "Processing"),
        ("circles", "blue", "Uploading"),
        ("blocks", "yellow", "Compiling"),
    ]
    
    # Initialize bars
    bars = []
    for style, color, desc in styles:
        pbar = AnimatedProgressBar(total=100, desc=desc, bar_style=style, color=color, width=30)
        pbar.start_time = time.time()
        bars.append(pbar)
        
    print("\n\033[1m🚀 Zobar Parallel Demo\033[0m\n")
    
    # Hide cursor
    sys.stdout.write("\033[?25l")
    
    try:
        # We run until all bars are complete
        while any(p.current < p.total for p in bars):
            output_lines = []
            
            for i, pbar in enumerate(bars):
                # Update state with some randomness to simulate real work
                if pbar.current < pbar.total:
                    # Random speed variation
                    if random.random() > (0.1 * i): # bias speeds slightly
                        pbar.current += 1
                    
                    pbar.spinner_idx += 1
                    
                    # Update suffix occasionally
                    if pbar.current % 10 == 0:
                        pbar.set_suffix(f"item={pbar.current}")
                
                # Get the visual line
                # Note: We bypass pbar.update() to avoid its internal print(\r...) 
                # and directly use the internal _build_line()
                line = pbar._build_line()
                output_lines.append(line)
            
            # Render all lines
            for line in output_lines:
                # \r to start of line, \033[K to clear rest of line
                sys.stdout.write(f"\r\033[K{line}\n")
            
            # Move cursor back up N lines to prepare for next frame
            # Only do this if we are going to draw again
            if any(p.current < p.total for p in bars):
                sys.stdout.write(f"\033[{len(bars)}A")
            
            sys.stdout.flush()
            time.sleep(0.05)
            
    finally:
        # Show cursor again
        sys.stdout.write("\033[?25h")
        print("\n")

if __name__ == "__main__":
    try:
        run_parallel_demo()
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\n")
        print("Demo cancelled.")
