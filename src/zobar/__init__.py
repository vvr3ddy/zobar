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
import time
from typing import Any, Iterable, Iterator, Literal, Sequence, TypeVar

# ANSI escape pattern for width calculation
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

# Type aliases for better readability
ColorType = Literal['cyan', 'green', 'yellow', 'blue', 'magenta', 'red', 'reset', 'bold']
BarStyleType = Literal['classic', 'gradient', 'braille', 'circles', 'blocks']

T = TypeVar('T')


def visible_len(s: str) -> int:
    """Return visible length (excluding ANSI codes).

    Args:
        s: String that may contain ANSI escape codes.

    Returns:
        The visible length of the string with ANSI codes removed.
    """
    return len(ANSI_RE.sub('', s))


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
    
    COLORS = {
        'cyan': '\033[96m', 'green': '\033[92m', 'yellow': '\033[93m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'red': '\033[91m',
        'reset': '\033[0m', 'bold': '\033[1m',
    }
    
    CLEAR_LINE = '\033[K'  # Clear from cursor to end of line
    CLEAR_DOWN = '\033[J'  # Clear from cursor to end of screen
    
    def __init__(
        self,
        total: int,
        desc: str = "",
        bar_style: BarStyleType = 'gradient',
        color: ColorType = 'cyan',
        width: int = 35,
        unit: str = "it",
        log_interval: float = 30.0,
    ) -> None:
        """Initialize the progress bar.

        Args:
            total: Total number of items/iterations.
            desc: Description text to display before the bar.
            bar_style: Visual style of the progress bar.
            color: Color scheme for the bar.
            width: Width of the progress bar in characters.
            unit: Unit label for the progress display (e.g., "it", "file").
            log_interval: Seconds between log updates in non-TTY mode.
        """
        self.total = total
        self.desc = desc
        self.bar_style = bar_style
        self.color = color
        self.width = width
        self.unit = unit
        self.current: int = 0
        self.start_time: float | None = None
        self.spinner_idx: int = 0
        self.suffix: str = ""
        self.log_interval = log_interval
        self.last_log_time: float = 0

        # Rule 6: TTY detection
        self.is_tty: bool = sys.stdout.isatty()
        self._last_drawn: int = -1  # For deduplication
        self._last_line_count: int = 1  # Track number of lines for clearing

        # Issue 2 fix: Use stdout fd for terminal size
        try:
            self.term_width: int = os.get_terminal_size(sys.stdout.fileno()).columns
        except OSError:
            self.term_width = 80
            
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

    def update(self, n: int = 1) -> None:
        """Update the progress by n steps.

        Args:
            n: Number of steps to increment progress by.
        """
        self.current = min(self.current + n, self.total)  # Improvement 3: Clamp
        self._display()

    def set_suffix(self, suffix: str) -> None:
        """Set a suffix to display after the progress bar.

        Args:
            suffix: The suffix text to display.
        """
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

    def _build_line(self) -> str:
        """Build the progress line with proper structure.

        Returns:
            The formatted progress line, potentially with newlines for wrapping.
        """
        progress = min(self.current / max(self.total, 1), 1.0)
        elapsed = time.time() - self.start_time if self.start_time else 0
        c = self.COLORS
        col = c.get(self.color, c['cyan'])
        
        # Spinner (advance only happens in _display for TTY)
        spinner = self.SPINNERS[self.spinner_idx % len(self.SPINNERS)] if self.current < self.total else '✓'
        
        # Speed & ETA
        speed = self.current / elapsed if elapsed > 0 else 0
        eta = (self.total - self.current) / speed if speed > 0 and self.current < self.total else 0
        
        bar = self._get_bar(progress)
        
        # Rule 5: Build parts with structural characters preserved
        parts = [
            spinner,
            f"{col}{self.desc}{c['reset']}" if self.desc else "",
            f"[{col}{bar}{c['reset']}]",  # Brackets always preserved
            f"{progress*100:5.1f}%",
            f"{self.current}/{self.total}",
            f"{speed:.1f} {self.unit}/s",
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
            if force or self.current == self.total:
                should_log = True
            # Log if interval passed
            elif self.log_interval and (now - self.last_log_time >= self.log_interval):
                should_log = True
                self.last_log_time = now
                
            if should_log:
                progress = min(self.current / max(self.total, 1), 1.0)
                msg = f"{self.desc}: {progress*100:.1f}% ({self.current}/{self.total})"
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