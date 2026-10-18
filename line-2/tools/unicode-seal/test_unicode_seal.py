import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import unicode_seal as tool


class SealTests(unittest.TestCase):
    def test_demo(self):
        result = tool.demo()
        self.assertEqual(result['finding_count'], 5)
        self.assertEqual(result['retained_findings'], 2)
        self.assertTrue(result['truncated'])
        self.assertTrue(result['consistent_replacement_rejected'])
        self.assertTrue(result['runtime_mismatch_rejected'])

    def test_identity_hashes_actual_fixed_files(self):
        identity = tool.identity()
        self.assertEqual(len(identity['files']), 5)
        for name, actual in identity['files'].items():
            self.assertEqual(actual, hashlib.sha256((tool.ROOT / name).read_bytes()).hexdigest())
        self.assertEqual(identity['python_version'], list(sys.version_info[:3]))

    def test_original_bytes_roundtrip(self):
        raw = ' \r\n{"é":"🐸","owner":1,"\\u006fwner":2}\r\n'.encode()
        seal = tool.pack(raw)
        result = tool.verify(tool.parse(tool.canonical(seal)), tool.fingerprint(seal))
        self.assertEqual(result['source_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertGreater(result['finding_count'], 0)

    def test_reformatting_preserves_identity(self):
        seal = tool.pack(b'{}')
        pretty = json.dumps(seal, indent=3, sort_keys=True).encode()
        self.assertTrue(tool.verify(tool.parse(pretty), tool.fingerprint(seal))['verified'])

    def test_independent_digest_rejects_consistent_replacement(self):
        first, second = tool.pack(b'{"a":1}'), tool.pack(b'{"a":2}')
        self.assertTrue(tool.replay.verify(second['bundle'])['verified'])
        with self.assertRaisesRegex(ValueError, 'retained digest'):
            tool.verify(second, tool.fingerprint(first))

    def test_repinning_does_not_hide_bad_replay(self):
        seal = tool.pack(tool.replay.citations.DEMO)
        seal['bundle']['report']['findings'][0]['source_token']['byte_start'] += 1
        with self.assertRaisesRegex(ValueError, 'replay'):
            tool.verify(seal, tool.fingerprint(seal))

    def test_every_identity_component_checked(self):
        original = tool.pack(b'{}')
        for key, value in [('files', {}), ('python_implementation', 'other'),
                           ('python_version', [0, 0, 0]), ('unicode_version', 'other')]:
            seal = copy.deepcopy(original)
            seal['engine'][key] = value
            with self.assertRaisesRegex(ValueError, 'identity'):
                tool.verify(seal, tool.fingerprint(seal))
        seal = copy.deepcopy(original)
        seal['engine']['python_version'][0] = float(sys.version_info.major)
        with self.assertRaises(ValueError):
            tool.verify(seal, tool.fingerprint(seal))

    def test_engine_checked_before_replay(self):
        seal = tool.pack(b'{}')
        seal['engine']['files'] = {'../../arbitrary': 'not opened'}
        with patch.object(tool.replay, 'verify', side_effect=AssertionError('should not replay')):
            with self.assertRaisesRegex(ValueError, 'identity'):
                tool.verify(seal, tool.fingerprint(seal))

    def test_pin_and_schema_validation(self):
        seal = tool.pack(b'{}')
        for pin in ('', 'A' * 64, '0' * 63, True, None):
            with self.assertRaises(ValueError):
                tool.verify(seal, pin)
        for bad in ([], dict(seal, extra=1), dict(seal, format='other')):
            with self.assertRaises(ValueError):
                tool.verify(bad, '0' * 64)

    def test_strict_input_and_budgets(self):
        for raw in (b'{"x":1,"x":2}', b'NaN', b'Infinity', b'\xff',
                    b'\xef\xbb\xbf{}', b'[' * 65 + b'0' + b']' * 65):
            with self.assertRaises(ValueError):
                tool.parse(raw)
        with patch.object(tool, 'MAX_BYTES', 10):
            with self.assertRaises(ValueError):
                tool.parse(b' ' * 11)
            with self.assertRaises(ValueError):
                tool.pack(b'{}')
        for limit in (True, 0, 1001):
            with self.assertRaises(ValueError):
                tool.pack(b'{}', limit)

    def test_same_engine_consistent_replacement_with_new_pin_can_pass(self):
        # Explicitly demonstrate that the digest's provenance is essential.
        seal = tool.pack(b'{"replacement":true}')
        self.assertTrue(tool.verify(seal, tool.fingerprint(seal))['verified'])

    def test_real_record(self):
        raw = Path('dist/line-2/24.json').read_bytes()
        seal = tool.pack(raw)
        result = tool.verify(seal, tool.fingerprint(seal))
        self.assertEqual(result['finding_count'], 0)

    def test_portable_copy_cli_and_changed_source(self):
        with tempfile.TemporaryDirectory(prefix='unicode-seal-', dir='/tmp') as directory:
            root = Path(directory)
            for name in {Path(p).parts[0] for p in tool.FILES}:
                shutil.copytree(tool.ROOT / name, root / name)
            script = root / 'unicode-seal/unicode_seal.py'
            source = root / 'input.json'
            source.write_bytes(tool.replay.citations.DEMO)
            def run(*args):
                return subprocess.run([sys.executable, '-B', str(script), *args],
                                      cwd=root, capture_output=True)
            made = run('pack', '--file', 'input.json', '--max-findings', '1')
            self.assertEqual(made.returncode, 0, made.stderr)
            seal = tool.parse(made.stdout)
            self.assertEqual(seal['engine'], tool.identity())
            packed = root / 'seal.json'
            packed.write_bytes(made.stdout)
            pinned = run('fingerprint', '--file', 'seal.json')
            self.assertEqual(pinned.returncode, 0, pinned.stdout)
            pin = json.loads(pinned.stdout)['seal_sha256']
            checked = run('verify', '--file', 'seal.json', '--expected-sha256', pin)
            self.assertEqual(checked.returncode, 0, checked.stdout)
            self.assertTrue(json.loads(checked.stdout)['truncated'])
            bad = run('verify', '--file', 'seal.json', '--expected-sha256', '0' * 64)
            self.assertEqual(bad.returncode, 2)
            self.assertIn('error', json.loads(bad.stdout))
            self.assertEqual(run('pack', '--file', '../outside.json').returncode, 2)
            engine = root / tool.FILES[0]
            engine.write_bytes(engine.read_bytes() + b'\n# deliberate test-only drift\n')
            drift = run('verify', '--file', 'seal.json', '--expected-sha256', pin)
            self.assertEqual(drift.returncode, 2)
            self.assertIn('identity', json.loads(drift.stdout)['error'])


if __name__ == '__main__':
    unittest.main()
