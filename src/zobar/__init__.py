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
import sys
import time
import os
import re

# ANSI escape pattern for width calculation
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def visible_len(s: str) -> int:
    """Return visible length (excluding ANSI codes)."""
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
    
    def __init__(self, total: int, desc: str = "", bar_style: str = 'gradient',
                 color: str = 'cyan', width: int = 35, unit: str = "it"):
        self.total = total
        self.desc = desc
        self.bar_style = bar_style
        self.color = color
        self.width = width
        self.unit = unit
        self.current = 0
        self.start_time = None
        self.spinner_idx = 0
        self.suffix = ""
        
        # Rule 6: TTY detection
        self.is_tty = sys.stdout.isatty()
        self._last_drawn = -1  # For deduplication
        
        # Issue 2 fix: Use stdout fd for terminal size
        try:
            self.term_width = os.get_terminal_size(sys.stdout.fileno()).columns
        except OSError:
            self.term_width = 80
            
    def __enter__(self):
        self.start_time = time.time()
        self._display()
        return self
    
    def __exit__(self, *args):
        # Issue 1 fix: Don't redraw twice, just show final message
        c = self.COLORS
        if self.is_tty:
            sys.stdout.write(f"\r{self.CLEAR_LINE}{c['green']}✓ Done{c['reset']}\n")
            sys.stdout.flush()
        else:
            print("✓ Done", file=sys.stderr)
    
    def update(self, n: int = 1):
        self.current = min(self.current + n, self.total)  # Improvement 3: Clamp
        self._display()
    
    def set_suffix(self, suffix: str):
        """Set a suffix to display after the progress bar."""
        self.suffix = suffix
    
    def _get_bar(self, progress: float) -> str:
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
    
    def _build_line(self) -> str:
        """Build the progress line with proper structure."""
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
            f"{c['yellow']}{self.suffix}{c['reset']}" if self.suffix else "",
        ]
        line = " ".join(p for p in parts if p)
        
        # Rule 4: ANSI-aware truncation
        if visible_len(line) > self.term_width - 2:
            # Truncate content, preserve structure
            max_len = self.term_width - 5
            truncated = ""
            for char in line:
                if visible_len(truncated + char + "...") > max_len:
                    break
                truncated += char
            line = truncated + "..."
        
        # Rule 5: Always end with color reset
        if not line.endswith(c['reset']):
            line += c['reset']
        
        return line
    
    def _display(self, force: bool = False):
        # Improvement 1: Avoid redraw if nothing changed (reduces flicker)
        if not force and self.current == self._last_drawn:
            return
        self._last_drawn = self.current
        
        # Rule 6: Graceful degradation for non-TTY
        if not self.is_tty:
            if force or self.current == self.total:
                progress = min(self.current / max(self.total, 1), 1.0)
                print(f"{self.desc}: {progress*100:.1f}% ({self.current}/{self.total})", file=sys.stderr)
            return
        
        line = self._build_line()
        
        # Improvement 2: Spinner advance only on actual TTY redraw
        self.spinner_idx += 1
        
        # Rule 2: Clear line before redraw
        sys.stdout.write(f"\r{self.CLEAR_LINE}{line}")
        sys.stdout.flush()


# Backwards compatible alias
ProgressBar = AnimatedProgressBar


def progress_bar(iterable, desc: str = "", total: int = None, **kwargs):
    """Iterator wrapper with progress bar."""
    total = total or len(iterable)
    with AnimatedProgressBar(total=total, desc=desc, **kwargs) as pbar:
        for item in iterable:
            yield item
            pbar.update(1)