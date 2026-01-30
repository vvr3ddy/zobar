# zobar

**Zero Overhead Bar**

![zobar demo](https://raw.githubusercontent.com/vvr3ddy/zobar/refs/heads/master/media/demo_parallel.gif)

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

### Parallel Progress Bars

For tracking multiple concurrent tasks, use `ProgressBarGroup`:

```python
import time
from zobar import ProgressBarGroup

with ProgressBarGroup() as group:
    download = group.add_bar(total=100, desc="Download", color="green")
    process = group.add_bar(total=50, desc="Process", color="blue")
    upload = group.add_bar(total=75, desc="Upload", color="magenta")

    # Update each bar independently
    for i in range(100):
        download.update(1)
        if i % 2 == 0:
            process.update(1)
        if i > 50 and i % 3 == 0:
            upload.update(1)
        time.sleep(0.05)
```

Each bar can be updated independently, and the group handles all cursor positioning automatically.

### Async Support

For async/await codebases, use the async context manager or async iterator:

```python
import asyncio
from zobar import AnimatedProgressBar, async_progress_bar

# Async context manager
async with AnimatedProgressBar(total=100, desc="Processing") as pbar:
    for i in range(100):
        await asyncio.sleep(0.05)
        pbar.update(1)

# Async iterator wrapper
async for item in async_progress_bar(async_items, total=100, desc="Processing"):
    await process(item)
```

### Styles

Available styles: `classic`, `gradient`, `braille`, `circles`, `blocks`.

## Changelog

### v0.1.4
*   Fixed suffix truncation by implementing multi-line wrapping and proper cursor management.

### v0.1.3
*   Added `log_interval` parameter for realtime logging in non-TTY environments (default: 30s).

### v0.1.2
*   Added suffix support in non-TTY logs.

## License

MIT
