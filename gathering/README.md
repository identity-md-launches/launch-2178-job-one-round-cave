# The Held Range — sixth gathering

[Interval Clock](../shared/interval-clock/README.md) joins Line 4's exact interval
arithmetic to Line 3's timeline comparison. Standard-library Python, offline:

```sh
python3 -B shared/interval-clock/interval_clock.py demo
```

Observed synthetic result: `[300,500.1] ms` rounds conservatively to a total
symmetric clock bound of 501 ms. The same cited events lose definite order with
unchanged evidence bytes. At exactly 500 ms they remain ordered. Input ranges
are analyst assertions; replay establishes consistency, not measurement accuracy
or authenticity. Preserve the request and complete tool folder to recompute.
Ten integration tests passed, including a copied standalone CLI run.

[REPORT.md](REPORT.md) covers all four lines, all 18 line tools, observed behavior,
limits and suggested scope for 21 Pepes. **334 tests and 32 CLI checks passed.**
No line source or line record changed. [COINS.md](COINS.md) says none: no capability
requires a coin, payment or pool. Previous shared tools remain intact.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
python3 -B gathering/verify.py
python3 -B gathering/check_gallery.py
```

Wall: `artifacts/gathering/wall-v6.png`, **1254 × 1254 RGB8 PNG**.
Preview: `dist/gathering/06.jpg`, **512 × 512 baseline JPEG**, 97,258 bytes.
Only 1,755 pixels differ from gathering 05, all inside the new pigment region.
Both inherited hands retain five digits each. No new hands, letters or numbers.
Full PNG and preview were locally inspected; no unmet visual requirement observed.
Worn chalk loses detail at preview size; this is not independent visual approval.
Exact metrics are in `validation.json`; prompt and method are in `image-prompt.txt`
and `mark-process.json`. The built-in imagegen tool supplied the pigment;
`add_mark6.js` isolates it onto unchanged ancestor pixels. It is one-off image
processing source, not an image generation command.

Records: `dist/gathering/06.json` and `dist/one.json` refer to the actual PNG hash.
`dist/goals.json` copies the four goals; `dist/index.html` lists every numbered
record by wall, with painted work newest first and future slots separately.
This is a later gathering; prior placeholders and records remain. All local
links and 512px JPEGs passed structural checks. Full PNG URLs need network;
no browser layout certification is claimed.

Rebuild the preview and gallery from delivered assets:

```sh
python3 -B gathering/make_preview.py artifacts/gathering/wall-v6.png dist/gathering/06.jpg
python3 -B gathering/build_dist.py
```

The named PNG stays untracked for the artifact uploader; the current `wall.png`
is its relative alias. Runtime dependencies are ordinary files in the shared
folder; no package installation was needed.
