import unittest
from zobar import AnimatedProgressBar, visible_len

class TestMultiline(unittest.TestCase):
    def test_multiline_wrap(self):
        """Test that line wraps when suffix is too long."""
        # Use a reasonable width
        pbar = AnimatedProgressBar(total=100, width=10)
        pbar.term_width = 80
        
        # Set a short description
        pbar.desc = "Test"
        
        # 1. Test short suffix (fits on one line)
        # Est length: ~60 chars
        pbar.set_suffix("Short")
        line = pbar._build_line()
        self.assertNotIn("\n", line)
        
        # 2. Test long suffix (should wrap)
        # Construct a suffix that guarantees overflow
        long_suffix = "X" * 100
        pbar.set_suffix(long_suffix)
        
        line = pbar._build_line()
        
        # Check if it contains a newline
        self.assertIn("\n", line)
        
        # Verify structure: Main line \n Suffix
        parts = line.split("\n")
        self.assertEqual(len(parts), 2)
        
        # Verify suffix is on second line
        # Note: formatting adds colors, so we check content
        # It will be truncated though! "X" * 100 > 80.
        self.assertIn("...", parts[1]) # It should be truncated
        self.assertIn("XXXX", parts[1])

if __name__ == '__main__':
    unittest.main()

