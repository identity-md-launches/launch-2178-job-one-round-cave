#!/usr/bin/env python3
"""Bind a Unicode Replay bundle to explicit engine bytes and a retained digest."""
import argparse
import hashlib
import hmac
import importlib.util
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
FILES = ('unicode-lantern/unicode_lantern.py', 'json-lantern/json_lantern.py',
         'json-citations/json_citations.py', 'unicode-replay/unicode_replay.py',
         'unicode-seal/unicode_seal.py')
# Only these fixed local implementation files are read. No paths from input run.
spec = importlib.util.spec_from_file_location('seal_replay', ROOT / FILES[3])
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
FORMAT = 'unicode-seal/1'
MAX_BYTES = replay.MAX_PACK_BYTES + 64 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity():
    return {'files': {name: digest((ROOT / name).read_bytes()) for name in FILES},
            'python_implementation': sys.implementation.name,
            'python_version': list(sys.version_info[:3]),
            'unicode_version': unicodedata.unidata_version}


def canonical(value):
    return replay.canonical(value)


def fingerprint(seal):
    return digest(canonical(seal))


def pack(raw, max_findings=1000):
    seal = {'format': FORMAT, 'engine': identity(),
            'bundle': replay.pack(raw, max_findings)}
    if len(canonical(seal)) > MAX_BYTES:
        raise ValueError('seal exceeds byte budget')
    return seal


def parse(raw):
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError('seal exceeds byte budget or is not bytes')
    text = raw.decode('utf-8', errors='strict')
    replay.citations.lantern.check_depth(text)
    return json.loads(text, object_pairs_hook=replay.unique_object,
                      parse_constant=replay.reject_constant)


def verify(seal, expected_sha256):
    if type(expected_sha256) is not str or not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValueError('expected SHA-256 must be 64 lowercase hex digits')
    if type(seal) is not dict or set(seal) != {'format', 'engine', 'bundle'}:
        raise ValueError('invalid seal members')
    if seal['format'] != FORMAT:
        raise ValueError('unsupported seal format')
    encoded = canonical(seal)
    if len(encoded) > MAX_BYTES:
        raise ValueError('seal exceeds byte budget')
    if not hmac.compare_digest(digest(encoded), expected_sha256):
        raise ValueError('seal differs from independently retained digest')
    if canonical(seal['engine']) != canonical(identity()):
        raise ValueError('engine/runtime identity differs; replay refused')
    result = replay.verify(seal['bundle'])
    result.update(seal_sha256=expected_sha256, engine_identity_matched=True,
                  digest_matched=True,
                  meaning='Matches retained digest and local engine identity; trust depends on where the digest came from. Findings remain review evidence, not a safety verdict.')
    return result


def demo():
    seal = pack(replay.citations.DEMO, 2)
    pin = fingerprint(seal)
    result = verify(parse(canonical(seal)), pin)
    replaced = pack(b'{"message":"different but internally consistent"}', 2)
    try:
        verify(replaced, pin)
    except ValueError:
        result['consistent_replacement_rejected'] = True
    else:
        raise ValueError('demo failed to reject replacement')
    # Re-pinning cannot conceal an incompatible engine from the local check.
    changed = parse(canonical(seal))
    changed['engine']['unicode_version'] = 'different'
    try:
        verify(changed, fingerprint(changed))
    except ValueError:
        result['runtime_mismatch_rejected'] = True
    else:
        raise ValueError('demo failed to reject runtime mismatch')
    result['demo'] = 'synthetic, no independent external authentication'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    create = actions.add_parser('pack')
    create.add_argument('--file', required=True)
    create.add_argument('--max-findings', type=int, default=1000)
    identify = actions.add_parser('fingerprint', help='compute digest to retain via a trusted channel')
    identify.add_argument('--file', required=True)
    check = actions.add_parser('verify')
    check.add_argument('--file', required=True)
    check.add_argument('--expected-sha256', required=True)
    actions.add_parser('identity')
    actions.add_parser('demo')
    args = parser.parse_args(argv)
    try:
        if args.action == 'pack':
            result = pack(replay.read_explicit(args.file, replay.MAX_SOURCE_BYTES), args.max_findings)
        elif args.action == 'identity':
            result = identity()
        elif args.action == 'demo':
            result = demo()
        else:
            seal = parse(replay.read_explicit(args.file, MAX_BYTES))
            if args.action == 'fingerprint':
                # Validate the complete replay before proposing an identity pin.
                pin = fingerprint(seal)
                verify(seal, pin)
                result = {'seal_sha256': pin,
                          'warning': 'Retain independently; a digest delivered with an untrusted seal authenticates nothing.'}
            else:
                result = verify(seal, args.expected_sha256)
        print(canonical(result).decode('ascii'))
    except (OSError, ValueError, RecursionError, OverflowError) as error:
        print(json.dumps({'error': replay.citations.lantern.lantern.escaped(str(error))}, ensure_ascii=True))
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
