"""
Enhanced Rich-style progress bar with Terminal Hygiene.

Implements the 6 rules:
1. Single ownership of stdout (logs → stderr)
2. Clear line before redraw (\\r\\033[K)
3. Clean exit with newline
4. ANSI-aware width calculation
5. Never truncate structural characters
6. Graceful TTY degradation
"""
from __future__ import annotations

import os
import re
import sys
import threading
import time
from typing import Any, AsyncIterable, AsyncIterator, Iterable, Iterator, Literal, Sequence, TypeVar

# ANSI escape pattern for width calculation
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

# Type aliases for better readability
ColorType = Literal['cyan', 'green', 'yellow', 'blue', 'magenta', 'red', 'reset', 'bold']
BarStyleType = Literal['classic', 'gradient', 'braille', 'circles', 'blocks']
UnitScaleType = Literal['none', 'kmg', 'binary']

# Color type for custom colors
CustomColorInput = str | tuple[int, int, int]  # hex string "#FF5733" or RGB tuple (255, 87, 51)

T = TypeVar('T')


def visible_len(s: str) -> int:
    """Return visible length (excluding ANSI codes).

    Args:
        s: String that may contain ANSI escape codes.

    Returns:
        The visible length of the string with ANSI codes removed.
    """
    return len(ANSI_RE.sub('', s))


def format_number(n: float, scale: UnitScaleType = 'none') -> str:
    """Format a number with appropriate scale suffix.

    Args:
        n: The number to format.
        scale: The scaling mode: 'none', 'kmg' (K/M/B), or 'binary' (KiB/MiB/GiB).

    Returns:
        Formatted string with scale suffix.
    """
    if scale == 'none':
        return f"{n:.0f}"

    if scale == 'binary':
        # Binary (IEC) units for bytes: KiB, MiB, GiB, TiB
        suffixes = ['', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
        threshold = 1024
    else:
        # KMG (decimal) units: K, M, B, T
        suffixes = ['', 'K', 'M', 'B', 'T']
        threshold = 1000

    for suffix in suffixes:
        if abs(n) < threshold:
            if suffix:
                return f"{n:.1f}{suffix}"
            return f"{n:.0f}"
        n /= threshold

    return f"{n:.1f}{suffixes[-1]}"


def format_bytes(n: float) -> str:
    """Format a byte count with binary unit suffix.

    Args:
        n: Number of bytes.

    Returns:
        Formatted string (e.g., "1.2MiB", "450KiB").
    """
    return format_number(n, scale='binary')


def parse_color(color: str | tuple[int, int, int]) -> str:
    """Convert a color to ANSI escape code.

    Args:
        color: Color as named color ('cyan', 'red', etc.),
                hex string ('#FF5733'), or RGB tuple ((255, 87, 51)).

    Returns:
        ANSI escape code for the color.
    """
    # Named colors
    if isinstance(color, str) and not color.startswith('#'):
        named_colors = {
            'cyan': '\033[96m', 'green': '\033[92m', 'yellow': '\033[93m',
            'blue': '\033[94m', 'magenta': '\033[95m', 'red': '\033[91m',
            'reset': '\033[0m', 'bold': '\033[1m',
            'white': '\033[97m', 'black': '\033[90m',
        }
        if color in named_colors:
            return named_colors[color]
        raise ValueError(f"Unknown color name: {color}")

    # RGB tuple
    if isinstance(color, tuple) and len(color) == 3:
        r, g, b = color
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError(f"RGB values must be 0-255: {color}")
        return f'\033[38;2;{r};{g};{b}m'

    # Hex string
    if isinstance(color, str) and color.startswith('#'):
        hex_color = color.lstrip('#')
        if len(hex_color) not in (3, 6):
            raise ValueError(f"Hex color must be 3 or 6 digits: {color}")

        # Expand 3-digit hex to 6-digit
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except ValueError:
            raise ValueError(f"Invalid hex color: {color}")

        return f'\033[38;2;{r};{g};{b}m'

    raise ValueError(f"Invalid color format: {color}")


class AnimatedProgressBar:
    """
    Progress bar with colors, animations, and terminal hygiene.
    No external dependencies required.
    """
    
    BAR_STYLES = {
        'classic': ['█', '░'],
        'gradient': ['█', '▓', '▒', '░'],
        'braille': ['⣿', '⣤', '⣄', '⡤', '⠤', '⠔', '⠒', '⠉', ' '],
        'circles': ['●', '○'],
        'blocks': ['▓', '▒', '░'],
    }
    
    SPINNERS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    # Indeterminate mode animation patterns
    INDETERMINATE_PATTERNS = {
        'bouncing': ['[=   ]', '[ =  ]', '[  = ]', '[   =]', '[  = ]', '[ =  ]'],
        'dots': ['.  ', '.. ', '...'],
        'classic': ['|', '/', '-', '\\'],
    }
    
    COLORS = {
        'cyan': '\033[96m', 'green': '\033[92m', 'yellow': '\033[93m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'red': '\033[91m',
        'reset': '\033[0m', 'bold': '\033[1m',
    }
    
    CLEAR_LINE = '\033[K'  # Clear from cursor to end of line
    CLEAR_DOWN = '\033[J'  # Clear from cursor to end of screen
    
    def __init__(
        self,
        total: int | None,
        desc: str = "",
        bar_style: BarStyleType = 'gradient',
        color: CustomColorInput = 'cyan',
        width: int = 35,
        unit: str = "it",
        unit_scale: UnitScaleType = 'none',
        smoothing: float = 0.3,
        log_interval: float = 30.0,
        log_timestamp: bool = False,
        thread_safe: bool = False,
    ) -> None:
        """Initialize the progress bar.

        Args:
            total: Total number of items/iterations, or None for indeterminate mode.
            desc: Description text to display before the bar.
            bar_style: Visual style of the progress bar.
            color: Color as name ('cyan', 'red', etc.), hex ('#FF5733'), or RGB tuple ((255, 87, 51)).
            width: Width of the progress bar in characters.
            unit: Unit label for the progress display (e.g., "it", "file", "B").
            unit_scale: Auto-scale large numbers: 'none', 'kmg' (K/M/B), or 'binary' (KiB/MiB).
            smoothing: EMA smoothing factor for ETA (0=more smoothing, 1=no smoothing).
            log_interval: Seconds between log updates in non-TTY mode.
            log_timestamp: Add timestamps to non-TTY log messages.
            thread_safe: Enable thread-safe operations with locking (has performance overhead).
        """
        self.total = total
        self.desc = desc
        self.bar_style = bar_style
        self._color_input = color  # Store original input
        self._color_code = parse_color(color)  # Parse to ANSI code
        self.width = width
        self.unit = unit
        self.unit_scale = unit_scale
        self.smoothing = smoothing
        self.log_timestamp = log_timestamp
        self.thread_safe = thread_safe
        self.current: int = 0
        self.start_time: float | None = None
        self.spinner_idx: int = 0
        self.suffix: str = ""
        self.log_interval = log_interval
        self.last_log_time: float = 0

        # EMA for rate smoothing
        self._ema_rate: float | None = None
        self._last_update_time: float | None = None

        # Thread safety
        self._lock: threading.Lock | None = threading.Lock() if thread_safe else None

        # Rule 6: TTY detection
        self.is_tty: bool = sys.stdout.isatty()
        self._last_drawn: int = -1  # For deduplication
        self._last_line_count: int = 1  # Track number of lines for clearing

        # Issue 2 fix: Use stdout fd for terminal size
        try:
            self.term_width: int = os.get_terminal_size(sys.stdout.fileno()).columns
        except OSError:
            self.term_width = 80

        # Group support for parallel bars
        self._group: ProgressBarGroup | None = None
            
    def __enter__(self) -> AnimatedProgressBar:
        """Enter the context manager and start the progress bar.

        Returns:
            The progress bar instance.
        """
        self.start_time = time.time()
        self.last_log_time = self.start_time
        self._display()
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context manager and display completion message.

        Args:
            *args: Exception info if an exception was raised (ignored).
        """
        # Issue 1 fix: Don't redraw twice, just show final message
        c = self.COLORS
        if self.is_tty:
            # Clear previous lines if multiline
            if self._last_line_count > 1:
                sys.stdout.write(f"\033[{self._last_line_count - 1}A")
            sys.stdout.write(f"\r{self.CLEAR_DOWN}{c['green']}✓ Done{c['reset']}\n")
            sys.stdout.flush()
        else:
            print("✓ Done", file=sys.stderr)

    async def __aenter__(self) -> AnimatedProgressBar:
        """Async enter the context manager and start the progress bar.

        Returns:
            The progress bar instance.
        """
        self.start_time = time.time()
        self.last_log_time = self.start_time
        self._display()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async exit the context manager and display completion message.

        Args:
            *args: Exception info if an exception was raised (ignored).
        """
        # Same logic as sync __exit__
        c = self.COLORS
        if self.is_tty:
            if self._last_line_count > 1:
                sys.stdout.write(f"\033[{self._last_line_count - 1}A")
            sys.stdout.write(f"\r{self.CLEAR_DOWN}{c['green']}✓ Done{c['reset']}\n")
            sys.stdout.flush()
        else:
            print("✓ Done", file=sys.stderr)

    def update(self, n: int = 1) -> None:
        """Update the progress by n steps.

        Args:
            n: Number of steps to increment progress by.
        """
        if self._lock:
            with self._lock:
                self._update_unsafe(n)
        else:
            self._update_unsafe(n)

    def _update_unsafe(self, n: int) -> None:
        """Internal update method without locking.

        Args:
            n: Number of steps to increment progress by.
        """
        self.current += n
        if self.total is not None:
            self.current = min(self.current, self.total)

        # If part of a group, let the group handle display
        if self._group and self._group.is_tty:
            self._group.refresh()
        else:
            self._display()

    def set_suffix(self, suffix: str) -> None:
        """Set a suffix to display after the progress bar.

        Args:
            suffix: The suffix text to display.
        """
        if self._lock:
            with self._lock:
                self.suffix = suffix
        else:
            self.suffix = suffix
    
    def _get_bar(self, progress: float) -> str:
        """Generate the progress bar visual representation.

        Args:
            progress: Progress value between 0.0 and 1.0.

        Returns:
            String representation of the progress bar.
        """
        style = self.BAR_STYLES.get(self.bar_style, self.BAR_STYLES['gradient'])
        filled = int(progress * self.width)
        
        if self.bar_style == 'braille':
            # Issue 4 fix: Clamp both min and max to prevent underflow
            bar = ''.join(
                style[min(max(int((progress * self.width - i) * len(style) / 2), 0), len(style)-1)]
                for i in range(self.width)
            )
        elif len(style) > 2:
            partial = progress * self.width - filled
            partial_idx = min(int(partial * (len(style) - 2)) + 1, len(style) - 2)
            bar = style[0] * filled
            if filled < self.width:
                bar += style[partial_idx] + style[-1] * (self.width - filled - 1)
        else:
            bar = style[0] * filled + style[-1] * (self.width - filled)
        return bar
    
    def _truncate(self, s: str, width: int) -> str:
        """Truncate string to width, preserving structure.

        Args:
            s: String to truncate.
            width: Maximum visible width allowed.

        Returns:
            Truncated string with "..." appended if truncated.
        """
        if visible_len(s) <= width:
            return s
        
        max_len = width - 3
        truncated = ""
        for char in s:
            if visible_len(truncated + char + "...") > max_len:
                break
            truncated += char
        return truncated + "..."

    def _build_indeterminate_line(self) -> str:
        """Build the progress line for indeterminate mode (total is None).

        Returns:
            The formatted indeterminate progress line.
        """
        elapsed = time.time() - self.start_time if self.start_time else 0
        c = self.COLORS
        col = self._color_code

        # Use bouncing animation for indeterminate mode
        pattern = self.INDETERMINATE_PATTERNS['bouncing']
        anim = pattern[self.spinner_idx % len(pattern)]

        # Build parts for indeterminate display
        if self.unit_scale != 'none':
            count_str = format_number(self.current, scale=self.unit_scale)
        else:
            count_str = str(self.current)

        parts = [
            anim,
            f"{col}{self.desc}{c['reset']}" if self.desc else "",
            f"{count_str} {self.unit}",
            f"{elapsed:.1f}s",
        ]
        main_line = " ".join(p for p in parts if p)
        suffix_part = f"{c['yellow']}{self.suffix}{c['reset']}" if self.suffix else ""

        # Check if everything fits on one line
        full_line = main_line + (" " + suffix_part if suffix_part else "")

        if visible_len(full_line) <= self.term_width - 2:
            line = full_line
        else:
            # Wrap mode
            if visible_len(main_line) > self.term_width - 2:
                main_line = self._truncate(main_line, self.term_width - 2)

            if suffix_part:
                if visible_len(suffix_part) > self.term_width - 2:
                    suffix_part = self._truncate(suffix_part, self.term_width - 2)
                line = main_line + "\n" + suffix_part
            else:
                line = main_line

        # Always end with color reset
        if not line.endswith(c['reset']):
            line += c['reset']

        return line

    def _build_line(self) -> str:
        """Build the progress line with proper structure.

        Returns:
            The formatted progress line, potentially with newlines for wrapping.
        """
        # Handle indeterminate mode (total is None)
        if self.total is None:
            return self._build_indeterminate_line()

        progress = min(self.current / max(self.total, 1), 1.0)
        elapsed = time.time() - self.start_time if self.start_time else 0
        c = self.COLORS
        col = self._color_code

        # Spinner (advance only happens in _display for TTY)
        spinner = self.SPINNERS[self.spinner_idx % len(self.SPINNERS)] if self.current < self.total else '✓'

        # Speed & ETA with EMA smoothing
        speed = self.current / elapsed if elapsed > 0 else 0

        # Apply EMA smoothing to rate if enabled
        if self.smoothing < 1.0 and speed > 0:
            if self._ema_rate is None:
                self._ema_rate = speed
            else:
                # EMA: new_ema = alpha * new_value + (1 - alpha) * old_ema
                # We use smoothing as alpha, so lower smoothing = more averaging
                alpha = self.smoothing
                self._ema_rate = alpha * speed + (1 - alpha) * self._ema_rate
            display_speed = self._ema_rate
        else:
            display_speed = speed

        eta = (self.total - self.current) / display_speed if display_speed > 0 and self.current < self.total else 0

        bar = self._get_bar(progress)

        # Format counts based on unit_scale
        if self.unit_scale != 'none':
            current_str = format_number(self.current, scale=self.unit_scale)
            total_str = format_number(self.total, scale=self.unit_scale)
            speed_str = format_number(display_speed, scale=self.unit_scale)
        else:
            current_str = str(self.current)
            total_str = str(self.total)
            speed_str = f"{display_speed:.1f}"

        # Rule 5: Build parts with structural characters preserved
        parts = [
            spinner,
            f"{col}{self.desc}{c['reset']}" if self.desc else "",
            f"[{col}{bar}{c['reset']}]",  # Brackets always preserved
            f"{progress*100:5.1f}%",
            f"{current_str}/{total_str}",
            f"{speed_str} {self.unit}/s",
            f"{elapsed:.1f}s",
            f"ETA: {eta:.0f}s" if self.current < self.total else "",
        ]
        main_line = " ".join(p for p in parts if p)
        suffix_part = f"{c['yellow']}{self.suffix}{c['reset']}" if self.suffix else ""
        
        # Check if everything fits on one line
        full_line = main_line + (" " + suffix_part if suffix_part else "")
        
        if visible_len(full_line) <= self.term_width - 2:
            line = full_line
        else:
            # Wrap mode
            # 1. Truncate main line if it's too long
            if visible_len(main_line) > self.term_width - 2:
                main_line = self._truncate(main_line, self.term_width - 2)
            
            # 2. Add suffix on new line
            # Truncate suffix if it's too long for the line
            if suffix_part:
                if visible_len(suffix_part) > self.term_width - 2:
                    suffix_part = self._truncate(suffix_part, self.term_width - 2)
                line = main_line + "\n" + suffix_part
            else:
                line = main_line # Should have been caught by full_line check, but safe fallback

        # Rule 5: Always end with color reset
        if not line.endswith(c['reset']):
            line += c['reset']
        
        return line
    
    def _display(self, force: bool = False) -> None:
        """Display the progress bar.

        Args:
            force: Force display even if progress hasn't changed.
        """
        # Improvement 1: Avoid redraw if nothing changed (reduces flicker)
        if not force and self.current == self._last_drawn:
            return
        self._last_drawn = self.current
        
        # Rule 6: Graceful degradation for non-TTY
        if not self.is_tty:
            now = time.time()
            should_log = False

            # Log if finished
            if force or (self.total is not None and self.current == self.total):
                should_log = True
            # Log if interval passed
            elif self.log_interval and (now - self.last_log_time >= self.log_interval):
                should_log = True
                self.last_log_time = now

            if should_log:
                # Add timestamp if enabled
                timestamp = ""
                if self.log_timestamp:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S") + " | "

                if self.total is None:
                    # Indeterminate mode logging
                    msg = f"{timestamp}{self.desc}: {self.current} {self.unit} processed"
                else:
                    progress = min(self.current / max(self.total, 1), 1.0)
                    msg = f"{timestamp}{self.desc}: {progress*100:.1f}% ({self.current}/{self.total})"
                if self.suffix:
                    msg += f" {self.suffix}"
                print(msg, file=sys.stderr)
            return
        
        line = self._build_line()
        
        # Improvement 2: Spinner advance only on actual TTY redraw
        self.spinner_idx += 1
        
        # Rule 2: Clear line before redraw
        # Handle multiline clear
        if self._last_line_count > 1:
            sys.stdout.write(f"\033[{self._last_line_count - 1}A")
            
        sys.stdout.write(f"\r{self.CLEAR_DOWN}{line}")
        sys.stdout.flush()
        
        # Update last line count
        self._last_line_count = line.count('\n') + 1


# Backwards compatible alias
ProgressBar = AnimatedProgressBar


class ProgressBarGroup:
    """Manages multiple progress bars with automatic cursor positioning.

    This class enables displaying and updating multiple progress bars
    simultaneously with proper terminal hygiene. Each bar can be
    independently updated and the group handles rendering all bars.

    Example:
        >>> with ProgressBarGroup() as group:
        ...     bar1 = group.add_bar(total=100, desc="Download", color="green")
        ...     bar2 = group.add_bar(total=50, desc="Process", color="blue")
        ...     bar1.update(10)
        ...     bar2.update(5)
    """

    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'

    def __init__(self, refresh_interval: float = 0.05) -> None:
        """Initialize the progress bar group.

        Args:
            refresh_interval: Seconds between automatic refreshes (default: 0.05).
        """
        self.bars: list[AnimatedProgressBar] = []
        self.refresh_interval = refresh_interval
        self.is_tty: bool = sys.stdout.isatty()
        self._active: bool = False
        self._start_time: float | None = None

    def add_bar(
        self,
        total: int,
        desc: str = "",
        bar_style: BarStyleType = 'gradient',
        color: ColorType = 'cyan',
        width: int = 35,
        unit: str = "it",
        unit_scale: UnitScaleType = 'none',
        smoothing: float = 0.3,
        log_timestamp: bool = False,
        thread_safe: bool = False,
    ) -> AnimatedProgressBar:
        """Add a new progress bar to the group.

        Args:
            total: Total number of items/iterations.
            desc: Description text to display before the bar.
            bar_style: Visual style of the progress bar.
            color: Color scheme for the bar.
            width: Width of the progress bar in characters.
            unit: Unit label for the progress display.
            unit_scale: Auto-scale large numbers: 'none', 'kmg' (K/M/B), or 'binary' (KiB/MiB).
            smoothing: EMA smoothing factor for ETA (0=more smoothing, 1=no smoothing).
            log_timestamp: Add timestamps to non-TTY log messages.
            thread_safe: Enable thread-safe operations with locking.

        Returns:
            The created AnimatedProgressBar instance.
        """
        bar = AnimatedProgressBar(
            total=total,
            desc=desc,
            bar_style=bar_style,
            color=color,
            width=width,
            unit=unit,
            unit_scale=unit_scale,
            smoothing=smoothing,
            log_timestamp=log_timestamp,
            thread_safe=thread_safe,
        )
        # Link bar to this group
        bar._group = self
        # Initialize start time if group is already active
        if self._active and self._start_time:
            bar.start_time = self._start_time
            bar.last_log_time = self._start_time
        self.bars.append(bar)
        return bar

    def remove_bar(self, bar: AnimatedProgressBar) -> None:
        """Remove a progress bar from the group.

        Args:
            bar: The progress bar instance to remove.
        """
        if bar in self.bars:
            self.bars.remove(bar)

    def refresh(self) -> None:
        """Refresh the display of all progress bars.

        This method is called automatically when bars are updated,
        but can be called manually to force a refresh.
        """
        if not self.is_tty:
            return

        # Move cursor to the top of our display area
        if self.bars:
            # Calculate total lines (each bar may have multiple lines due to wrapping)
            total_lines = sum(self._count_lines(bar) for bar in self.bars)
            sys.stdout.write(f"\033[{total_lines}A")

        # Redraw all bars
        for bar in self.bars:
            line = bar._build_line()
            sys.stdout.write(f"\r\033[K{line}\n")
            # Advance spinner for animation
            bar.spinner_idx += 1

        sys.stdout.flush()

    def _count_lines(self, bar: AnimatedProgressBar) -> int:
        """Count the number of lines a bar will occupy.

        Args:
            bar: The progress bar to count lines for.

        Returns:
            Number of lines the bar occupies.
        """
        line = bar._build_line()
        return line.count('\n') + 1

    def __enter__(self) -> ProgressBarGroup:
        """Enter the context manager and start displaying bars.

        Returns:
            The ProgressBarGroup instance.
        """
        self._active = True
        self._start_time = time.time()
        for bar in self.bars:
            bar.start_time = self._start_time
            bar.last_log_time = self._start_time

        if self.is_tty:
            sys.stdout.write(self.HIDE_CURSOR)
            sys.stdout.flush()

        self.refresh()
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context manager and clean up.

        Args:
            *args: Exception info if an exception was raised (ignored).
        """
        self._active = False

        if self.is_tty:
            # Show final state
            self.refresh()
            # Show cursor
            sys.stdout.write(self.SHOW_CURSOR)
            # Move to a new line
            sys.stdout.write("\n")
            sys.stdout.flush()
        else:
            # Non-TTY: log completion for all bars
            for bar in self.bars:
                progress = min(bar.current / max(bar.total, 1), 1.0)
                print(f"{bar.desc}: {progress*100:.1f}% ({bar.current}/{bar.total}) - Done", file=sys.stderr)


def progress_bar(
    iterable: Iterable[T],
    desc: str = "",
    total: int | None = None,
    **kwargs: Any,
) -> Iterator[T]:
    """Iterator wrapper with progress bar.

    Args:
        iterable: An iterable to wrap with progress tracking.
        desc: Description text to display before the bar.
        total: Total number of items (auto-detected from len() if not provided).
        **kwargs: Additional arguments passed to AnimatedProgressBar.

    Yields:
        Items from the iterable while showing progress.

    Example:
        >>> for item in progress_bar(range(100), desc="Processing"):
        ...     process(item)
    """
    total = total or len(iterable)
    with AnimatedProgressBar(total=total, desc=desc, **kwargs) as pbar:
        for item in iterable:
            yield item
            pbar.update(1)


async def async_progress_bar(
    iterable: AsyncIterable[T],
    desc: str = "",
    total: int | None = None,
    **kwargs: Any,
) -> AsyncIterator[T]:
    """Async iterator wrapper with progress bar.

    Args:
        iterable: An async iterable to wrap with progress tracking.
        desc: Description text to display before the bar.
        total: Total number of items (auto-detected if possible).
        **kwargs: Additional arguments passed to AnimatedProgressBar.

    Yields:
        Items from the async iterable while showing progress.

    Example:
        >>> async for item in async_progress_bar(async_gen(), desc="Processing"):
        ...     await process(item)

    Note:
        If the iterable doesn't support __len__, you must provide total explicitly.
    """
    # Try to get total from __len__ if available
    if total is None:
        if hasattr(iterable, '__len__'):
            total = len(iterable)  # type: ignore
        else:
            raise ValueError(
                "total must be specified for async iterables that don't support __len__"
            )

    pbar = AnimatedProgressBar(total=total, desc=desc, **kwargs)
    await pbar.__aenter__()

    try:
        async for item in iterable:
            yield item
            pbar.update(1)
    finally:
        await pbar.__aexit__(None, None, None)