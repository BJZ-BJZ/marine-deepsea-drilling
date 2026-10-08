"""Drilling P26-194: verification entry points must refuse to run with assertions disabled."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = ['src/verify.py']

class VerificationGuards(unittest.TestCase):
    def test_optimized_entry_points_refuse_to_report_success(self):
        for rel in SCRIPTS:
            path = ROOT / rel
            with self.subTest(path=rel):
                result = subprocess.run([sys.executable, '-O', str(path)],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Verification requires assertions', result.stderr)


class Contracts(unittest.TestCase):
    def test_envelope_rejects_missing_and_negative_residual(self):
        import importlib.util
        import numpy as np
        spec = importlib.util.spec_from_file_location('envelope', ROOT / 'src/envelope.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for args in [(np.nan, 0, 1), (100, 0, -1)]:
            with self.assertRaises(ValueError):
                module.select_candidate(*args)

if __name__ == '__main__':
    unittest.main()
