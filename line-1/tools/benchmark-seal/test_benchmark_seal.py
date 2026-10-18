import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import benchmark_seal as seal


class SealTests(unittest.TestCase):
    def setUp(self):
        self.demo = seal.demo()
        self.pack = self.demo['pack']
        self.pin = self.pack['seal_sha256']
        self.content = self.pack['content']
        self.plan_pin = self.content['manifest']['plan_sha256']

    def verify(self, pack=None, pin=None, results=None):
        return seal.verify(seal.canonical(self.pack if pack is None else pack),
                           self.pin if pin is None else pin, results)

    def test_demo_replays_complete_results(self):
        report, csv = self.verify(results=self.demo['normalized_csv'].encode())
        self.assertEqual(report['observations']['case_count'], 3)
        self.assertEqual(seal.digest(csv), report['observations']['normalized_csv_sha256'])
        self.assertEqual(len(report['assets']['systems']), 3)
        self.assertIn('seal mismatch', self.demo['rejected_rehashed_replacement'])

    def test_independent_hash_oracle(self):
        import hashlib
        raw = (json.dumps(self.content, sort_keys=True, ensure_ascii=True,
                          separators=(',', ':'), allow_nan=False) + '\n').encode()
        self.assertEqual(self.pin, hashlib.sha256(raw).hexdigest())

    def test_rehashed_asset_forgery(self):
        for kind in ('cases', 'systems'):
            pack = copy.deepcopy(self.pack)
            pack['content'][kind][0]['data_b64'] = seal.encode(b'changed bytes')
            pack['seal_sha256'] = seal.digest(seal.canonical(pack['content']))
            with self.assertRaises(seal.InputError):
                self.verify(pack)
            # A new external pin accepts a new pack: identity is external, not authenticity.
            self.verify(pack, pack['seal_sha256'])

    def test_no_mutation(self):
        before = copy.deepcopy(self.pack)
        self.verify()
        seal.seal(seal.canonical(self.content), self.plan_pin)
        self.assertEqual(before, self.pack)

    def test_input_order_normalization(self):
        content = copy.deepcopy(self.content)
        for kind in ('cases', 'systems'):
            content[kind].reverse()
        self.assertEqual(seal.seal(seal.canonical(content), self.plan_pin), self.pack)
        pack = copy.deepcopy(self.pack)
        pack['content']['cases'].reverse()
        with self.assertRaises(seal.InputError):
            self.verify(pack)

    def test_membership_is_complete(self):
        for kind in ('cases', 'systems'):
            for edit in ('missing', 'extra', 'duplicate', 'unknown'):
                content = copy.deepcopy(self.content)
                values = content[kind]
                if edit == 'missing':
                    values.pop()
                elif edit == 'extra':
                    values.append(copy.deepcopy(values[0]))
                elif edit == 'duplicate':
                    values[1] = copy.deepcopy(values[0])
                else:
                    values[0]['id'] = 'unplanned'
                with self.subTest(kind=kind, edit=edit), self.assertRaises(seal.InputError):
                    seal.seal(seal.canonical(content), self.plan_pin)

    def test_base64_is_strict(self):
        for value in ('', '!!!', 'YQ', 'YR==', 'YQ==\n', 5, None, [], '\u2603'):
            with self.subTest(value=value), self.assertRaises(seal.InputError):
                seal.decode_blob(value)
        self.assertEqual(seal.decode_blob('AAE='), b'\x00\x01')

    def test_unknown_fields_and_schemas(self):
        for target in ('pack', 'content', 'manifest', 'asset'):
            pack = copy.deepcopy(self.pack)
            obj = {'pack': pack, 'content': pack['content'],
                   'manifest': pack['content']['manifest'],
                   'asset': pack['content']['cases'][0]}[target]
            obj['unknown'] = True
            with self.subTest(target=target), self.assertRaises(seal.InputError):
                self.verify(pack)
        pack = copy.deepcopy(self.pack)
        pack['schema'] = 'other'
        with self.assertRaises(seal.InputError):
            self.verify(pack)

    def test_duplicate_json_and_nonfinite(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff'):
            with self.assertRaises(seal.InputError):
                seal.seal(raw, self.plan_pin)

    def test_wrong_and_bad_pins(self):
        for value in ('f' * 64, 'A' * 64, '', 'ab', None, 7):
            with self.subTest(value=value), self.assertRaises(seal.InputError):
                seal.verify(seal.canonical(self.pack), value)
            with self.subTest(plan_value=value), self.assertRaises(seal.InputError):
                seal.seal(seal.canonical(self.content), value)

    def test_plan_tamper(self):
        pack = copy.deepcopy(self.pack)
        pack['content']['manifest']['plan']['pass_rule'] = 'New scoring rule'
        with self.assertRaises(seal.InputError):
            self.verify(pack)

    def test_missing_results_and_family_drift(self):
        raw = self.demo['normalized_csv'].encode()
        for bad in (raw.rsplit(b'\n', 2)[0] + b'\n',
                    raw.replace(b'synthetic-fast-v1', b'new-system'),
                    raw + b'extra,1,1,1\n', raw.replace(b',0,', b',2,')):
            with self.assertRaises(seal.InputError):
                self.verify(results=bad)

    def test_binary_payload_is_exact(self):
        content = copy.deepcopy(self.content)
        raw = bytes(range(256))
        content['cases'][0]['data_b64'] = seal.encode(raw)
        pack = seal.seal(seal.canonical(content), self.plan_pin)
        report, _ = self.verify(pack, pack['seal_sha256'])
        self.assertEqual(report['assets']['cases'][0]['sha256'], seal.digest(raw))
        self.assertEqual(report['assets']['cases'][0]['bytes'], 256)

    def test_limits(self):
        with self.assertRaises(seal.InputError):
            seal.seal(b' ' * (seal.frozen.MAX_BYTES + 1), self.plan_pin)
        content = copy.deepcopy(self.content)
        content['cases'][0]['data_b64'] = seal.encode(b'x' * 1600000)
        with self.assertRaises(seal.InputError):
            seal.seal(seal.canonical(content), self.plan_pin)

    def test_cli_demo_and_error_no_stdout(self):
        script = str(Path(seal.__file__).resolve())
        demo = subprocess.run([sys.executable, '-B', script, 'demo'], capture_output=True)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertEqual(json.loads(demo.stdout)['pack'], self.pack)
        bad = subprocess.run([sys.executable, '-B', script, 'verify', '--pack', script,
                              '--expected-seal-sha256', self.pin], capture_output=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(bad.stdout, b'')

    def test_cli_seal_verify_and_emit(self):
        script = Path(seal.__file__).resolve()
        folder = script.parent
        made = subprocess.run([sys.executable, '-B', str(script), 'seal', '--input',
                               str(folder / 'example-content.json'), '--expected-plan-sha256',
                               self.plan_pin], capture_output=True)
        self.assertEqual(made.returncode, 0, made.stderr)
        self.assertEqual(json.loads(made.stdout), self.pack)
        command = [sys.executable, '-B', str(script), 'verify', '--pack',
                   str(folder / 'example-pack.json'), '--expected-seal-sha256', self.pin,
                   '--results', str(folder / 'example-results.csv')]
        checked = subprocess.run(command, capture_output=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(json.loads(checked.stdout)['observations']['case_count'], 3)
        emitted = subprocess.run(command + ['--emit-csv'], capture_output=True)
        self.assertEqual(emitted.returncode, 0, emitted.stderr)
        self.assertEqual(emitted.stdout.decode(), self.demo['normalized_csv'])

    def test_downstream_ladder(self):
        path = Path(seal.__file__).resolve().parent.parent / 'candidate-ladder' / 'candidate_ladder.py'
        if not path.is_file():
            self.skipTest('standalone folder has no downstream ladder')
        # Use its actual CLI, so no private analysis API is assumed.
        result = subprocess.run([sys.executable, '-B', str(path), '--input',
                                 str(Path(seal.__file__).resolve().parent / 'example-results.csv'),
                                 '--alpha', '0.05'], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['input_sha256'],
                         self.demo['check']['observations']['normalized_csv_sha256'])

    def test_snapshot_matches_ancestor(self):
        source = Path(seal.__file__).resolve().parent.parent / 'frozen-benchmark' / 'frozen_benchmark.py'
        if not source.is_file():
            self.skipTest('standalone folder has no ancestor to compare')
        self.assertEqual(source.read_bytes(), Path(seal.frozen.__file__).read_bytes())


if __name__ == '__main__':
    unittest.main()
