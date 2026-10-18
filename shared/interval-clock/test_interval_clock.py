import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import interval_clock as tool


class IntervalClockTests(unittest.TestCase):
    def setUp(self):
        self.bundle = tool.demo_bundle()

    def bound(self, low, high):
        bundle = copy.deepcopy(self.bundle)
        bundle['calculation'] = dict(variables={'bound': [low, high]},
                                     expression='bound', to='ms', within=None)
        return tool.analyze(bundle)

    def test_conservative_rounding_changes_order(self):
        result = tool.analyze(self.bundle)
        self.assertEqual(result['calculation']['upper'], '500.1')
        self.assertEqual(result['asserted_total_bound_ms'], 501)
        comparison = result['comparison']
        self.assertEqual(comparison['pair']['before']['relation'], 'left-before-right')
        self.assertEqual(comparison['pair']['after']['relation'], 'unresolved-overlap')
        self.assertTrue(comparison['pair']['same_line_evidence'])
        self.assertEqual(comparison['source_changes'], [])
        self.assertEqual(comparison['line_changes']['counts']['changed-interval'], 2)

    def test_exact_half_open_boundary(self):
        self.assertEqual(self.bound('0 ms', '500 ms')['comparison']['pair']['after']['relation'],
                         'left-before-right')
        self.assertEqual(self.bound('0 ms', '500.0001 ms')['asserted_total_bound_ms'], 501)
        self.assertEqual(self.bound('0 ms', '0 ms')['asserted_total_bound_ms'], 0)
        self.assertEqual(self.bound('1 day', '1 day')['asserted_total_bound_ms'], 86400000)

    def test_fraction_rounding_independent_oracle(self):
        for n in range(1, 51):
            result = self.bound('0 s', f'1 s / {n}')
            exact = Fraction(1000, n)
            got = result['asserted_total_bound_ms']
            self.assertLessEqual(exact, got)
            self.assertLess(got - exact, 1)

    def test_invalid_domains_and_failed_claim(self):
        for low, high in [('0 m', '1 m'), ('-1 ms', '1 ms'), ('0 s', '86400.001 s'),
                          ('1 s', '0 s')]:
            with self.subTest(low=low), self.assertRaises(ValueError):
                self.bound(low, high)
        self.bundle['calculation']['within'] = ['0 ms', '500 ms']
        with self.assertRaisesRegex(ValueError, 'acceptance'):
            tool.analyze(self.bundle)

    def test_tampering_and_schema(self):
        broken = copy.deepcopy(self.bundle)
        broken['timeline']['timeline']['events'][0]['message'] = 'changed'
        with self.assertRaises(ValueError):
            tool.analyze(broken)
        for broken in ([], dict(self.bundle, extra=True), dict(self.bundle, format='other'),
                       dict(self.bundle, left=['accepted.log', True])):
            with self.assertRaises(ValueError):
                tool.analyze(broken)

    def test_inert_names_and_omissions(self):
        self.bundle['timeline'] = tool.diff.replay.make_pack([
            ('../../inert-not-opened', b'no timestamp\n'),
            ('completed.log', b'2026-10-18T10:00:02Z completed\n')], ignore_unmatched=True)
        self.bundle['left'] = ['../../inert-not-opened', 1]
        pair = tool.analyze(self.bundle)['comparison']['pair']
        self.assertEqual(pair['before']['relation'], 'unavailable')
        self.assertEqual(pair['after']['relation'], 'unavailable')
        self.assertEqual(pair['after']['left']['status'], 'omitted')

    def test_determinism_and_immutable_input(self):
        before = copy.deepcopy(self.bundle)
        self.assertEqual(tool.analyze(self.bundle), tool.analyze(self.bundle))
        self.assertEqual(before, self.bundle)

    def test_strict_json_and_budget(self):
        for raw in (b'{"x":1,"x":2}', b'NaN', b'\xff'):
            with self.assertRaises(ValueError):
                tool.diff.replay.load_pack(raw)
        self.bundle['calculation']['expression'] = ' ' * 66000
        with self.assertRaisesRegex(ValueError, '65536'):
            tool.analyze(self.bundle)

    def test_snapshot_provenance(self):
        root = Path(__file__).resolve().parent
        repo = root.parents[1]
        for row in json.loads((root / 'provenance.json').read_text()):
            snapshot = root / Path(row['snapshot']).relative_to('shared/interval-clock')
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), row['sha256'])
            source = repo / row['source']
            if source.is_file():
                self.assertEqual(source.read_bytes(), snapshot.read_bytes())

    def test_portable_cli_and_exact_byte_pin(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            target = Path(directory) / 'portable'
            shutil.copytree(Path(__file__).parent, target)
            script = (target / 'interval_clock.py').resolve()
            raw = tool.canonical(self.bundle)
            def run(data, *args):
                return subprocess.run([sys.executable, '-B', str(script), 'run', *args],
                                      input=data, capture_output=True, cwd=target, timeout=20)
            result = run(raw, '--expect-sha256', hashlib.sha256(raw).hexdigest())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['digest_pin_checked'])
            result = run(raw + b' ', '--expect-sha256', hashlib.sha256(raw).hexdigest())
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b'')
            self.assertEqual(run(b'{}').returncode, 2)


if __name__ == '__main__':
    unittest.main()
