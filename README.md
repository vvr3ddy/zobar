# zobar

**Zero Overhead Bar**

A zero-dependency, high-performance, hygienically correct progress bar for Python. Designed for HPC environments, workstations, and anywhere you need a progress bar that just works without breaking your terminal logs.

## Features

*   **Zero Dependencies:** strictly standard library (`sys`, `time`, `os`, `re`).
*   **Terminal Hygiene:**
    *   Single ownership of stdout (logs go to stderr).
    *   Clears lines properly before redrawing.
    *   Clean exit with newline.
*   **Robust:**
    *   ANSI-aware width calculation (doesn't break on colored text).
    *   Graceful degradation on non-TTY environments (e.g., piped output, CI/CD logs).
*   **Customizable:** Supports various styles (classic, gradient, braille, etc.) and colors.

## Installation

```bash
pip install zobar
```

## Usage

### Basic Usage

The simplest way to use it is with the `progress_bar` wrapper:

```python
import time
from zobar import progress_bar

items = range(100)
for item in progress_bar(items, desc="Processing"):
    time.sleep(0.05)
```

### Manual Control

For more control, use the `AnimatedProgressBar` context manager:

```python
import time
from zobar import AnimatedProgressBar

total_steps = 50
with AnimatedProgressBar(total=total_steps, desc="Downloading", bar_style='braille', color='green') as pbar:
    for i in range(total_steps):
        time.sleep(0.1)
        pbar.update(1)
        if i % 10 == 0:
            pbar.set_suffix(f"Current file: {i}")
```

### Styles

Available styles: `classic`, `gradient`, `braille`, `circles`, `blocks`.

## License

MIT
