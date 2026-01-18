import unittest
import sys
import io
from zobar import AnimatedProgressBar

class TestSuffixLogging(unittest.TestCase):
    def test_suffix_in_non_tty(self):
        """Test that suffix is included in logs in non-TTY environments."""
        # Mock sys.stdout.isatty to return False
        original_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: False
        
        # Capture stderr
        captured_stderr = io.StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured_stderr

        try:
            with AnimatedProgressBar(total=10) as pbar:
                pbar.set_suffix("loss=0.123")
                pbar.update(10) # Update to completion to trigger non-TTY print
            
            output = captured_stderr.getvalue()
            # Check if suffix is present in the output
            self.assertIn("loss=0.123", output)
        finally:
            sys.stdout.isatty = original_isatty
            sys.stderr = original_stderr

if __name__ == '__main__':
    unittest.main()
