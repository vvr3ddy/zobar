import unittest
import sys
import io
from zobar import AnimatedProgressBar, visible_len

class TestZobar(unittest.TestCase):
    def test_visible_len(self):
        """Test ANSI-aware string length calculation."""
        text = "\033[31mHello\033[0m"
        self.assertEqual(visible_len(text), 5)
        self.assertEqual(visible_len("World"), 5)

    def test_progress_bar_initialization(self):
        """Test basic initialization."""
        pbar = AnimatedProgressBar(total=100)
        self.assertEqual(pbar.total, 100)
        self.assertEqual(pbar.current, 0)

    def test_progress_bar_update(self):
        """Test updating the progress bar."""
        pbar = AnimatedProgressBar(total=100)
        pbar.update(10)
        self.assertEqual(pbar.current, 10)
        pbar.update(5)
        self.assertEqual(pbar.current, 15)
        # Test clamping
        pbar.update(100)
        self.assertEqual(pbar.current, 100)

    def test_bar_generation_classic(self):
        """Test bar string generation for 'classic' style."""
        pbar = AnimatedProgressBar(total=10, width=10, bar_style='classic')
        # 50%
        bar_str = pbar._get_bar(0.5)
        self.assertEqual(bar_str, '█' * 5 + '░' * 5)

    def test_non_tty_behavior(self):
        """Test that it writes to stderr in non-TTY environments."""
        # Mock sys.stdout.isatty to return False
        original_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: False
        
        # Capture stderr
        captured_stderr = io.StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured_stderr

        try:
            with AnimatedProgressBar(total=10) as pbar:
                pbar.update(10)
            
            output = captured_stderr.getvalue()
            # In non-TTY, it should print percentage updates to stderr
            self.assertIn("100.0%", output)
            self.assertIn("Done", output)
        finally:
            sys.stdout.isatty = original_isatty
            sys.stderr = original_stderr

if __name__ == '__main__':
    unittest.main()
