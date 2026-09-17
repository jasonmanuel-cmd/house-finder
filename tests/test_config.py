import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ConfigTests(unittest.TestCase):
    def test_database_path_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'persistent.sqlite')
            env = dict(os.environ, DB_PATH=path)
            result = subprocess.run([sys.executable, '-c', 'from config import DB_PATH; print(DB_PATH)'], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), path)

if __name__ == '__main__':
    unittest.main()
