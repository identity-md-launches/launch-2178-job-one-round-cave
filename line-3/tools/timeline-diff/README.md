# Timeline Diff

Compare two independently verified Timeline Replay packs without executing the
services or reopening any path named inside a pack. The report shows source-byte
changes, physical-line additions and changes, explicit omissions, changed clock
assumptions, and the temporal relation of one cited event pair in each pack.
Python 3.10+, standard library only. Copy this entire folder, including `vendor/`,
for standalone offline use.

One command from the repository root shows it working without writing files:

```sh
python3 -B line-3/tools/timeline-diff/timeline_diff.py demo
```

Observed locally: the same two **synthetic** log lines are definitely ordered
with a zero clock bound, but overlap under an asserted ±750 ms bound. Their line
hashes stay identical; two intervals and the relation change. Eight tests passed.
This demonstrates an assumption change, not measured clock error or a real incident.

For two existing packs, give actual source names and physical line numbers:

```sh
python3 -B line-3/tools/timeline-diff/timeline_diff.py compare test/scratch/before.json test/scratch/after.json --left client.log 1 --right server.log 2
```

`--expect-before-sha256 DIGEST` and `--expect-after-sha256 DIGEST` optionally pin
the exact bytes of each pack to independently retained lowercase SHA-256 values.
Both full packs are replayed before comparison. A bad pack, altered timeline, bad
digest or invalid citation returns exit 2. A missing or omitted cited event
returns `unavailable` rather than pretending to compare its order. Successful
comparisons, including a changed or unresolved order, return exit 0. Output is
deterministic JSON; terminal diagnostics escape control characters.

The tool matches physical `source` and `line` citations, then compares hashes of
the complete source bytes and each nonblank line. If lines move, their old and new
positions count as removals and additions. `same_line_evidence` means the selected
pair's text hashes match at those positions in both verified packs. A changed
relation is labeled `relation-changed` only in that case. If pair evidence differs
or a cited line is absent or omitted, assessment is
`different-or-unavailable-evidence`; the two individual relations remain visible.
This avoids calling a same-looking conclusion stable when the evidence changed.

Line-change counts are exact. At most the first 200 change details, sorted by
source and line, are emitted; `omitted_details` gives the remainder. The report
does not echo log messages or full source bytes, although source names and hashes
are shown. It reads only explicit regular pack files inside the current workspace;
pack source names are inert strings. The inherited verifier bounds each pack to
16 MiB, embedded logs to 2 MiB, sources to 64, and physical lines to 100,000.
Two full packs are resident in memory. It writes no files and uses no network,
wallet, key, transaction, payment or coin.

Verified packs establish internal consistency, not truthful or complete logs.
An independently trusted digest is needed to bind a particular pack; a hash
derived from the same untrusted pack is insufficient. Clock bounds are analyst
assertions. Temporal order does not establish causality, and an unresolved overlap
does not establish simultaneity. Line hashes do not prove an event is the same
after it moves to a different physical citation. Path checks are not a filesystem
sandbox against concurrent changes.

```sh
python3 -B -m unittest discover -s line-3/tools/timeline-diff -v
```

Observed: eight tests passed for assumption-only relation changes, changed line
evidence, missing events, line movement, explicit omission, tamper rejection,
determinism, and bounded detail output. `PROVENANCE.json` pins the unchanged local
Replay and Time Flint snapshots used by this standalone tool.
