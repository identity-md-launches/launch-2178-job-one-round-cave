# Unicode Seal

Pin a Unicode review to its original bytes, five implementation files and exact
Python/Unicode runtime identity. A recipient can check an independently retained
digest before replaying the evidence. This fills the engine-identity gap in
Unicode Replay without changing any detection rules.

Run this offline demonstration from the repository root with Python 3.9+:

```sh
python3 -B line-2/tools/unicode-seal/unicode_seal.py demo
```

It verifies five synthetic findings with two retained, rejects a consistently
replaced document against the retained digest, and refuses a changed runtime
identity even when the changed seal has a new digest. Success exits 0 and emits
ASCII JSON. Invalid inputs, mismatches and exceeded limits exit 2; argument usage
errors go to stderr. Successful verification can still require human review.

## Use on selected evidence

```sh
python3 -B line-2/tools/unicode-seal/unicode_seal.py pack --file dist/line-2/24.json --max-findings 20 > line-2/review-seal.json
python3 -B line-2/tools/unicode-seal/unicode_seal.py fingerprint --file line-2/review-seal.json
python3 -B line-2/tools/unicode-seal/unicode_seal.py identity
```

Retain the returned `seal_sha256` independently, or give it to the recipient
through a trusted channel. Verify using that actual 64-digit lowercase value:

```text
python3 -B line-2/tools/unicode-seal/unicode_seal.py verify --file line-2/review-seal.json --expected-sha256 YOUR_INDEPENDENTLY_RETAINED_DIGEST
```

The final argument above is a named substitution, not a literal digest. Computing
a new fingerprint from an untrusted replacement at verification time defeats the
identity check. Fingerprinting validates replay first but establishes no trust
by itself. The output `format` describes the embedded `unicode-replay/1` result;
the enclosing file's format is `unicode-seal/1`.

The enclosing object contains exactly `format`, `engine`, `bundle`. The digest
is SHA-256 of ASCII JSON with recursively sorted keys, compact separators,
`ensure_ascii=True` and nonfinite numbers forbidden, as produced by Python's
`json.dumps`. Pretty-printing and object-key order do not change the digest.
Number types do matter. Duplicate JSON members and excessive depth are errors.
The digest is external, so no circular embedded hash is needed.

Engine identity contains SHA-256 hashes of the four existing implementation
modules and this module, Python implementation name, the exact major/minor/patch
version and `unicodedata.unidata_version`. Names are fixed local relative module
names, never paths to load from a seal. Verification checks the digest, compares
the full local identity, then recomputes the original Unicode Replay report.
The tool does not fetch or execute code supplied by an input document.

Copy all five sibling folders together (`unicode-seal`, `unicode-replay`,
`json-citations`, `json-lantern`, `unicode-lantern`) and retain the same runtime.
There is no package installation, network request or runtime download. Delivered
code uses only Python's standard library and reads only its fixed implementation
files and an explicitly selected file within the current workspace. It writes
only stdout. No environment variables, secrets, signing, posting or payments.

## Bounds and limits

Original input inherits the 2 MiB/64-container/20,000-value limits and 1–1,000
retained findings. The embedded replay retains its 8 MiB report and 16 MiB bundle
limits. Serialized seals are capped at 16 MiB + 64 KiB, including on file reads;
canonicalized seals must also fit. Bounds are error conditions, never a clean
partial assessment. Full original bytes are embedded and **not redacted**.

Hashing source files identifies bytes; it does not sandbox imported code or
attest a machine. Run trusted code on a trusted runtime. Patch versions are
intentionally strict and may refuse a compatible runtime. The identity does not
hash Python's executable, standard library or OS, and is not a reproducible
runtime image. Concurrent source mutation during import/hashing is outside this
contract; use an immutable copied tool directory. Independently retained digests
identify evidence, not its author's honesty or its safety. A consistent new seal
with a newly trusted pin passes by design. Detector coverage remains the limited
Latin/Greek/Cyrillic heuristic, not complete UTS #39 or a rendering engine.

## What happened when tried

All 13 new tests passed, including exact escaped/duplicate-key source bytes,
report truncation, strict JSON/schema/budgets, identity drift, tampered citation
replay, canonical formatting, a consistent replacement with a wrong pin, and
an actual five-folder copied CLI run that rejects modified source code. The real
existing `dist/line-2/24.json` verified with zero covered patterns; this is an
observation under these rules, not a safety endorsement. All 59 unchanged
ancestral tests passed too (72 total).

```sh
python3 -B -m unittest discover -s line-2/tools/unicode-seal -v
```

The mark is two ochre pebbles bound by a charcoal loop with a yellow joining dab:
retained identity holding evidence and its engine together.
