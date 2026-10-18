# Interval Flint

Check the range implied by uncertain numerical inputs with exact rational
arithmetic and explicit unit dimensions. Input is one JSON object on stdin.
Each named input is an inclusive pair of quantity expressions. The formula
uses those names, the units accepted by Unit Flint, parentheses, `+ - * /`,
unary signs, and integer powers `^ -12..12`. It never evaluates Python code.
The result is an **enclosure**: every value allowed by the supplied input
intervals lies between the reported endpoints, provided the formula is defined
throughout those intervals.

One command from the repository root shows it working:

```sh
python3 -B line-4/tools/interval-flint/interval_flint.py demo
```

Tried locally: hypothetical transfer size `[9, 11] MiB` divided by a rate
`[2, 2.5] MiB/s` yields exactly `[3.6, 5.5] s`. The inclusive check against
`[3, 6] s` reports `fully_within: true` and exits 0. Nine regression tests
passed, including 200 seeded products and 200 nonzero divisions compared
with an independent `fractions.Fraction` corner oracle, dimensional errors, a zero-containing
denominator, even and odd powers across zero, duplicate JSON keys, and real
subprocess exit statuses.

To supply a calculation, pipe JSON to `run`:

```sh
printf '%s\n' '{"variables":{"distance":["9.9 km","10.1 km"],"time":["1.9 h","2.1 h"]},"expression":"distance / time","to":"km/h","within":["4 km/h","6 km/h"]}' | python3 -B line-4/tools/interval-flint/interval_flint.py run
```

The four top-level fields are required. `to` and `within` may be null.
`variables` holds at most 32 ASCII lowercase names of up to 32 characters,
beginning with a letter and then containing letters or digits. Names cannot
shadow built-in units. Each value is `[lower, upper]`, with both endpoints
having the same dimensions and lower no greater than upper. `expression`
contains the formula. `to` changes only display units. `within` gives an
inclusive allowed range with the same dimensions; `fully_within` is true only
when the entire calculated enclosure fits. `overlaps` distinguishes partial
overlap from separation. Exit codes are 0 for a valid result that passes any
supplied `within` check, 1 for a valid result that is not fully within, and 2
for invalid input or a formula undefined anywhere in the input ranges.

The parser bounds input to 65,536 JSON bytes, a 4,096-character formula, 256
tokens, 32 grammar levels, and 2,048-bit exact endpoints. It rejects JSON
numbers; write quantities as strings. Duplicate keys and invalid UTF-8 are
errors. All mathematical output values are exact decimal or fraction strings.
The fixed sibling `engine.py` is a byte-identical snapshot of Unit Flint at
mark 24, SHA-256
`c683e558cdbdf6cf73d4b32572b6fa498b80e7816483b882bf2d51adfff3062e`.
Copy this entire folder for offline use. Only Python's standard library is
needed; the tool reads stdin and its own code, with no network, wallet,
environment or configuration access.

**Limits:** Standard interval arithmetic loses relationships between repeated
uses of the same variable: `x-x` for `x=[1,2] m` reports `[-1,1] m`, an
honest but loose enclosure. The tool rejects division by an interval including
zero, even where algebraic cancellation might make a formula meaningful.
Input intervals are user claims, not measurements verified by this program.
No probability distribution, covariance, rounding model, currency value, or
token price is inferred. ZTO and IMD are not needed to perform this exact
arithmetic.

Run the focused regression suite:

```sh
python3 -B -m unittest discover -s line-4/tools/interval-flint -v
```
