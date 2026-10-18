# Benchmark Seal

Bind a fixed binary benchmark's **actual case payloads and system bundle bytes**
to its Frozen Benchmark protocol. A portable JSON pack retains those bytes as
base64. Verification checks a separately retained seal, reports every asset's
size and SHA-256, and optionally admits complete paired observations using the
original Frozen Benchmark engine. Python 3.10+ standard library only; this folder
works by itself offline. It does not execute any supplied code.

From the repository root, one command shows it working:

```sh
python3 -B line-1/tools/benchmark-seal/benchmark_seal.py demo
```

When tried locally, the synthetic demo sealed three case payloads and three
system descriptors, admitted all three result rows, and rejected a changed case
even after the attacker recomputed the internal seal. **These are synthetic
fixtures, not executed systems or measured improvements.** The example seal is
`0d18499d7dcb9150785724d7121ffeafa8607ace1612900920b715c4f85b3947`.
The demo writes only stdout, without network, keys, accounts or installs.

## Before collecting outcomes

First use Frozen Benchmark to freeze a protocol and independently retain its
plan pin. Prepare an input JSON with exactly `manifest`, `cases`, and `systems`.
The manifest is the complete original Frozen Benchmark manifest. Each case or
system entry has exactly `id` and `data_b64`:

```json
{"id":"your-version-label","data_b64":"YWN0dWFsIGJ5dGVz"}
```

This tiny syntax illustration decodes to `actual bytes`; replace it with your
real asset. Cases must match all planned case IDs exactly. Systems must match
the baseline version and every candidate version. Input entries may arrive in
any order; sealing normalizes them to planned order. Include the complete case
input **and expected answer** in each case payload if the pass rule needs one.
Choose a deterministic bundle format for systems that retains source, prompts,
parameters and dependencies needed for your experiment. A mutable URL or version
label alone does not bind its target. Dependencies omitted from a bundle remain
unbound; the tool cannot know whether your bundle is complete.

Encode bytes with `base64.b64encode(raw).decode('ascii')` from Python's standard
library. No payload is executed, extracted, interpreted as a filename or fetched.
Assets are not compressed or redacted. An intentionally empty case can be
represented by structured bytes such as `{"input":""}`; zero-byte assets fail
to catch accidental omissions. See `example-content.json` for a complete,
explicitly synthetic example with the existing Frozen Benchmark demo protocol.

The included example can be sealed without creating any files:

```sh
python3 -B line-1/tools/benchmark-seal/benchmark_seal.py seal --input line-1/tools/benchmark-seal/example-content.json --expected-plan-sha256 13d5c3882c0082a7c603ad464645f312f6ebe6bee4622cc9f4c35710e8086f8e
```

For your real input, replace both the path and pin. Save stdout to a new intended
pack file and **retain its `seal_sha256` separately before collecting outcomes**.
The seal hashes the normalized content as sorted-key, compact, ASCII-escaped JSON
with a trailing LF. The seal covers the entire plan and all case and system
bytes, including each ID and its position. Formatting and input list ordering
are normalized. Asset byte changes, including line endings, change the seal.
Keep the actual pack too: a digest cannot restore its bytes.

## Verify and admit observations

This command checks the included example against its known synthetic seal:

```sh
python3 -B line-1/tools/benchmark-seal/benchmark_seal.py verify --pack line-1/tools/benchmark-seal/example-pack.json --expected-seal-sha256 0d18499d7dcb9150785724d7121ffeafa8607ace1612900920b715c4f85b3947 --results line-1/tools/benchmark-seal/example-results.csv
```

For a real run, use your pack and originally retained seal, rather than reading
an expected seal from the pack under review. Omit `--results` for asset-only
verification. With results, every planned case and candidate must be present
exactly once, with binary outcomes. Add `--emit-csv` to print only the fully
admitted CSV in planned order; it requires `--results`. That CSV can be passed
to Candidate Ladder with the protocol's alpha. The ladder's `input_sha256` must
match `observations.normalized_csv_sha256`. Preserve the original observations
and verification report as well. Never analyze stale output after a failed check.

Valid input exits 0 regardless of statistical significance; invalid input exits
2 with stderr and no partial stdout. Verification reports consistency, not a
statistical verdict. The nested legacy checker describes the limits of its own
ID-only layer; the outer seal additionally binds the supplied asset bytes.

## Boundaries

An independently trusted pre-outcome seal is essential. Replacing the pack and
its internal hash can pass against a *new* external pin. No digest proves time
of publication, truthful scoring, independence, representative selection,
execution of the sealed code, runtime environment identity, absence of repeated
looks or scientific validity. Code and prompt bytes are not execution traces.
Keep a fixed endpoint and use the existing exact McNemar/Holm workflow once.
Sharing the pack shares all its payloads; review their contents first.

Input paths must resolve to regular files within the current working directory.
Each JSON or CSV input and the pretty-printed emitted pack is limited to 2 MiB.
Base64 adds roughly one third overhead. Other bounds are Frozen Benchmark's:
1–10,000 cases, 2–16 candidates, 256-character labels and an 8,192-character pass
rule. Duplicate JSON members, extra fields, noncanonical base64, changed family,
empty assets and non-normalized packs fail. Paths are guarded by resolution,
not by an adversarial filesystem sandbox against concurrent swaps. No
environment variables are read and inputs are never modified.

## Verification and provenance

```sh
python3 -B -m unittest discover -s line-1/tools/benchmark-seal -v
```

All 18 tests passed locally: byte-exact binary payloads, external-pin forgeries,
independent canonical-hash calculation, membership, ordering, schemas, duplicate
JSON, base64, bounds, immutability, plan changes, CLI statuses/CSV and actual
Candidate Ladder digest agreement. The 47 predecessor tests also passed.
A copied-folder offline run passed 16 tests with two repository integrations
skipped. The standalone folder includes all runtime dependencies as ordinary
Python source files; no installation is needed.

`frozen_engine.py` is an unchanged snapshot of
`../frozen-benchmark/frozen_benchmark.py`. It retains its author's implementation,
plan validation, bounded reads and CSV admission rather than introducing a
different interpretation of the protocol. Its exact SHA-256 is recorded in
`provenance.json`. The predecessor folder remains untouched.
