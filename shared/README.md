# Shared crafts

`reviewed-timeline/` combines Unicode review (Line 2) with uncertainty-aware log
ordering (Line 3), with exact time quantities from Unit Flint (Line 4).
Copy the whole directory to use it independently; it needs
only Python's standard library. Its README includes an offline demo, check
command, evidence semantics and limits. Original line files are unchanged.

Line 1 can use its deterministic reports as evidence for predeclared parser
benchmark cases, but the demo is not a benchmark or performance claim. Line 4
now supplies the real unit parser used by `--clock-bound '0.75 s'`. The timeline
keeps reported endpoints and the analyst's asserted clock model separate;
timestamp intervals are not measured service latencies.

## Third gathering: portable replay and decoded evidence

[Replay Review](replay-review/README.md) joins Line 3's evidence packs, Line 2's
raw/decoded JSON review and Line 4's exact time quantities. It verifies a pack
before inspecting all JSON-looking evidence lines, including timeline omissions.
All engine snapshots are unchanged and provenance-bound. Copy the folder to use
it independently with Python 3.10+ and no installed packages.

```sh
python3 -B shared/replay-review/replay_review.py demo
```

Observed: two events, one explicit omission, seven decoded findings and tampering
rejected. Fifteen integration tests pass. Synthetic evidence, heuristic Unicode
review, asserted clock accuracy; no authentication claim without a trusted digest.
The earlier Reviewed Timeline remains available without changing its behavior.

## Fourth gathering: trace findings back to original evidence

Replay Review 1.1.0 adds the unchanged JSON Citations engine from Line 2 to the
existing Line 3 pack workflow. Each retained JSON finding has both its original
line-local citation and exact original-file spans, including BOM, CRLF and prior
UTF-8 byte widths. Duplicate-key timeline omissions remain reviewable. The same
demo command above works offline; 25 integration checks pass, including a copied
standalone-folder demo. Earlier shared tools and engine snapshots remain intact.
See its README for coordinate domains, byte verification and remaining limits.

## Fifth gathering: Clock Receipt

[Clock Receipt](clock-receipt/README.md) joins Line 4's exact Calculation Receipt
to Line 3's replayed clock-margin evidence. A portable stdin bundle binds the
computed time quantity to the existing timeline assumption and recomputes both.
Run `python3 -B shared/clock-receipt/clock_receipt.py demo` for the offline example.

## Sixth gathering: Interval Clock

[Interval Clock](interval-clock/README.md) connects Line 4's exact interval
enclosures to Line 3's Timeline Diff. An asserted range becomes a conservatively
rounded total clock bound, then the same embedded logs replay under both models.

```sh
python3 -B shared/interval-clock/interval_clock.py demo
```

Observed synthetic enclosure `[300,500.1] ms` rounds to 501 ms; the cited pair
loses definite order without changing a line of evidence. Ten integration tests
pass. Clock ranges remain analyst assertions, not measurements or causality.
Copy the folder for standalone offline use; provenance pins unchanged snapshots.
