"""
Test runner script for all lab work tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src' / 'python'))

if __name__ == '__main__':
    import unittest
    
    loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent / 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    sys.exit(0 if result.wasSuccessful() else 1)
