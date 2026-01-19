import unittest
import sys
import io
import time
from unittest.mock import patch
from zobar import AnimatedProgressBar

class TestNonTTYInterval(unittest.TestCase):
    def test_log_interval(self):
        """Test that non-TTY logs occur at intervals."""
        # Mock sys.stdout.isatty to return False
        original_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: False
        
        # Capture stderr
        captured_stderr = io.StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured_stderr

        try:
            # Set interval to 10s
            with patch('time.time') as mock_time:
                mock_time.return_value = 1000.0
                
                with AnimatedProgressBar(total=100, log_interval=10.0) as pbar:
                    # Initial state, should not log yet (only on enter? No, _display called on enter)
                    # _display calls time.time() -> 1000.0. last_log_time = 1000.0
                    
                    # Update 1: time advances by 5s (less than interval)
                    mock_time.return_value = 1005.0
                    pbar.update(10)
                    # Should NOT have logged
                    self.assertEqual(captured_stderr.getvalue(), "")
                    
                    # Update 2: time advances by 6s (total 11s > 10s)
                    mock_time.return_value = 1011.0
                    pbar.update(10)
                    
                    # Should HAVE logged
                    output = captured_stderr.getvalue()
                    self.assertIn("20.0%", output)
                    
                    # Clear buffer to test next interval
                    captured_stderr.truncate(0)
                    captured_stderr.seek(0)
                    
                    # Update 3: time advances by 5s (total 16s, 5s since last log)
                    mock_time.return_value = 1016.0
                    pbar.update(10)
                    # Should NOT log
                    self.assertEqual(captured_stderr.getvalue(), "")
                    
                    # Update 4: Finish
                    pbar.current = 100
                    pbar.update(0) # Force update to complete logic? update calls _display
                    
            # Check final output
            output = captured_stderr.getvalue()
            # It logs on finish (force=False, but current==total)
            # Depending on how logic flows, it might print 100% or "Done" or both.
            # In __exit__, it prints "Done"
            
        finally:
            sys.stdout.isatty = original_isatty
            sys.stderr = original_stderr

if __name__ == '__main__':
    unittest.main()
