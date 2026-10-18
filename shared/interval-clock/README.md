# Interval Clock

Carry Line 4's uncertain quantity arithmetic into Line 3's incident timeline
comparison. A worker can compute an enclosure for an **asserted total symmetric
clock bound**, round its upper endpoint upward to whole milliseconds, then
compare the same original log bytes under the old and calculated assumptions.
Python 3.10+ standard library only. Copy this entire directory for offline use.

```sh
python3 -B shared/interval-clock/interval_clock.py demo
```

Observed: asserted offset `[200,250] ms` plus drift `[100,250.1] ms` encloses
`[300,500.1] ms`. The upper endpoint rounds conservatively to **501 ms**.
The same two synthetic events change from definite order under zero bound to
unresolved overlap. Their original line hashes remain identical. At exactly
500 ms the half-open timestamp intervals still establish order. Ten tests passed,
including fifty exact fraction rounding checks and a copied standalone CLI run.
These are synthetic inputs, not measured clock errors or a real incident.

To see the complete request schema, print `example`. It emits exactly `format`,
`timeline`, `calculation`, `left`, `right`. Replace the timeline with a real
Timeline Replay pack, the calculation with your justified ranges, and the two
citations with `[source_name, physical_line_number]`. Then pipe it to `run`:

```sh
python3 -B shared/interval-clock/interval_clock.py example | python3 -B shared/interval-clock/interval_clock.py run
```

`run` reads at most 16 MiB of UTF-8 JSON from stdin and writes one deterministic
ASCII JSON result. Duplicate members, nonfinite numbers, excessive nesting,
invalid citations and inconsistent timeline reports fail. `calculation` follows
Interval Flint's request schema: `variables`, `expression`, `to`, `within`.
It keeps that engine's 65,536-byte request and parser/arithmetic budgets.
The whole calculated enclosure must have time dimensions and lie in `[0,1 day]`.
A failed `within` claim is rejected. Display conversions do not affect the bound.
The upper endpoint in base seconds is multiplied by 1000 and rounded with exact
rational ceiling; no floating point arithmetic enters this decision.

The entire original pack replays before any option is trusted. The new pack
retains every embedded input byte, source name, physical citation and omission
policy. Both packs replay again through the unmodified Timeline Diff engine.
Missing/omitted pair citations explicitly report `unavailable`. Calendar overflow
fails the whole operation. The result contains a comparison, not a new portable
pack; retain the request and this folder to recompute it. No embedded filename
is opened, and no services or supplied code are executed.

Success exits 0 even if order is unresolved; invalid input exits 2 with escaped
stderr and no partial stdout. `--expect-sha256` on `run` checks an independently
retained lowercase SHA-256 of the **exact stdin bytes**, including whitespace.
Without it, replay checks internal consistency only. With it, trust still depends
on where the expected digest came from. The separate content hash normalizes JSON
with the bundled replay engine; it is not the exact-input pin.

## Limits and provenance

Input ranges, their formula and the interpretation as a total symmetric clock
bound are analyst assertions. The tool does not estimate skew, infer causality,
measure clocks, combine probabilities or establish truthful/complete logs.
Interval arithmetic can overestimate when variables repeat (`x-x` need not be
zero). A conservative upper bound can remove a definite order; it cannot justify
an inaccurately small supplied range. No per-source/asymmetric bound is modeled.
Packs embed full unredacted evidence. Output includes source names and hashes;
review them before sharing. Same-parser replay can reproduce the same parser bug.

`provenance.json` pins six unchanged ordinary-file snapshots from Lines 3 and 4.
There are no dependencies to install, network calls, environment/configuration
lookups, signing, payments or deployments. ZTO and IMD are unnecessary here.
The older shared tools remain intact.

```sh
python3 -B -m unittest discover -s shared/interval-clock -v
```
