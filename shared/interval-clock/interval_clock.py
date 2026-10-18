#!/usr/bin/env python3
"""Replay a timeline under a conservatively rounded, calculated interval bound."""
import argparse
import base64
from fractions import Fraction
import hashlib
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'engines'))
import interval_flint as interval
import timeline_diff as diff

FORMAT = 'interval-clock/1'
MAX_BYTES = diff.replay.MAX_PACK_BYTES
MAX_BOUND_MS = 86400000


def canonical(value):
    return diff.replay.canonical(value)


def calculated_bound(request):
    # Keep the upstream request budget even for an embedded request.
    encoded = canonical(request)
    if len(encoded) > interval.MAX_BYTES:
        raise ValueError('calculation request exceeds 65536 bytes')
    request = interval.decode(encoded)
    result = interval.evaluate(request)
    if result.get('within', {}).get('fully_within') is False:
        raise ValueError('calculation fails its requested acceptance interval')
    if result['dimensions'] != dict(length=0, mass=0, time=1, data=0):
        raise ValueError('clock bound must have time dimensions')
    lower, upper = Fraction(result['base_lower']), Fraction(result['base_upper'])
    if lower < 0 or upper > 86400:
        raise ValueError('entire bound enclosure must be between zero and one day')
    ms = upper * 1000
    # Round upward, never silently understate the asserted enclosure.
    bound = -(-ms.numerator // ms.denominator)
    return result, bound


def analyze(bundle):
    if type(bundle) is not dict or set(bundle) != {'format', 'timeline', 'calculation', 'left', 'right'}:
        raise ValueError('request needs exactly format, timeline, calculation, left, right')
    if bundle['format'] != FORMAT:
        raise ValueError('unsupported interval-clock format')
    if len(canonical(bundle)) > MAX_BYTES:
        raise ValueError('request exceeds 16 MiB')
    for side in ('left', 'right'):
        pair = bundle[side]
        if type(pair) is not list or len(pair) != 2:
            raise ValueError('citation must be [source, physical_line]')
        diff.citation(*pair)
    before = bundle['timeline']
    diff.replay.verify_pack(before)
    calculation, bound = calculated_bound(bundle['calculation'])
    inputs = [(item['source'], base64.b64decode(item['base64'], validate=True))
              for item in before['inputs']]
    after = diff.replay.make_pack(inputs,
        ignore_unmatched=before['options']['ignore_unmatched'], clock_uncertainty_ms=bound)
    comparison = diff.compare(before, after, *bundle['left'], *bundle['right'])
    return {'format': FORMAT, 'verified': True,
            'request_content_sha256': hashlib.sha256(canonical(bundle)).hexdigest(),
            'calculation': calculation, 'asserted_total_bound_ms': bound,
            'rounding': 'ceiling of upper enclosure endpoint in milliseconds',
            'comparison': comparison,
            'meaning': 'Ranges and total symmetric clock bound are analyst assertions, not measured skew. Order is temporal, not causal. Replay checks consistency, not authenticity.'}


def demo_bundle():
    pack = diff.replay.make_pack([
        ('accepted.log', b'2026-10-18T10:00:00Z accepted\n'),
        ('completed.log', b'2026-10-18T10:00:02Z completed\n')])
    return dict(format=FORMAT, timeline=pack,
        calculation=dict(variables={'offset': ['200 ms', '250 ms'],
                                    'drift': ['100 ms', '250.1 ms']},
                         expression='offset + drift', to='ms', within=['0 s', '1 s']),
        left=['accepted.log', 1], right=['completed.log', 1])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['demo', 'example', 'run'])
    parser.add_argument('--expect-sha256', help='independently retained SHA-256 of exact stdin bytes')
    args = parser.parse_args(argv)
    try:
        if args.command != 'run' and args.expect_sha256 is not None:
            raise ValueError('--expect-sha256 applies only to run')
        if args.command == 'example':
            result = demo_bundle()
        elif args.command == 'demo':
            result = analyze(demo_bundle())
            result['data_kind'] = 'synthetic example; no clock measurement'
        else:
            raw = sys.stdin.buffer.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError('request exceeds 16 MiB')
            digest = hashlib.sha256(raw).hexdigest()
            if args.expect_sha256 is not None:
                if re.fullmatch('[0-9a-f]{64}', args.expect_sha256) is None or digest != args.expect_sha256:
                    raise ValueError('input differs from independently retained digest')
            result = analyze(diff.replay.load_pack(raw))
            result.update(input_sha256=digest, digest_pin_checked=args.expect_sha256 is not None)
        sys.stdout.buffer.write(canonical(result) + b'\n')
        return 0
    except (ValueError, OSError, TypeError, RecursionError, interval.engine.UnitError) as exc:
        print('interval-clock: ' + diff.replay.engine.visible(str(exc)), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
