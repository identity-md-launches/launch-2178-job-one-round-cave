#!/usr/bin/env python3
"""Compare two verified incident-timeline packs and a cited event pair offline."""

import argparse
from datetime import datetime
import re
import sys

import replay

FORMAT = "timeline-diff/1"
DETAIL_LIMIT = 200
HEX = re.compile(r"[0-9a-f]{64}\Z")


def citation(source, line):
    if not isinstance(source, str) or type(line) is not int or line < 1:
        raise replay.ReplayError("citation requires a source string and positive line number")
    return {"source": source, "line": line}


def entries(pack):
    """Index parsed and explicitly omitted physical lines by their inert citations."""
    result = {}
    for kind, field in (("event", "events"), ("omitted", "omitted")):
        for item in pack["timeline"][field]:
            key = (item["source"], item["line"])
            if key in result:
                raise replay.ReplayError("duplicate physical citation in verified report")
            result[key] = {"kind": kind, "line_sha256": item["line_sha256"],
                           "item": item}
    return result


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def relation(left, right):
    if left is right:
        return "same-event"
    if instant(left["end_utc_exclusive"]) <= instant(right["start_utc"]):
        return "left-before-right"
    if instant(right["end_utc_exclusive"]) <= instant(left["start_utc"]):
        return "right-before-left"
    return "unresolved-overlap"


def pair_snapshot(index, left_key, right_key):
    left, right = index.get(left_key), index.get(right_key)
    def show(entry):
        if entry is None:
            return {"status": "absent"}
        result = {"status": entry["kind"], "line_sha256": entry["line_sha256"]}
        if entry["kind"] == "event":
            event = entry["item"]
            result.update(start_utc=event["start_utc"],
                          end_utc_exclusive=event["end_utc_exclusive"])
        return result
    return {"relation": relation(left["item"], right["item"])
            if left and right and left["kind"] == right["kind"] == "event"
            else "unavailable", "left": show(left), "right": show(right)}


def line_state(entry):
    return None if entry is None else {"kind": entry["kind"],
                                       "line_sha256": entry["line_sha256"]}


def change_kind(old, new):
    if old is None:
        return "added"
    if new is None:
        return "removed"
    if old["line_sha256"] != new["line_sha256"]:
        return "changed-line"
    if old["kind"] != new["kind"]:
        return "reclassified"
    if old["kind"] == "event":
        a, b = old["item"], new["item"]
        if (a["start_utc"], a["end_utc_exclusive"]) != (b["start_utc"], b["end_utc_exclusive"]):
            return "changed-interval"
    return None


def compare(before, after, left_source, left_line, right_source, right_line):
    left_key = (left_source, left_line)
    right_key = (right_source, right_line)
    citation(*left_key)
    citation(*right_key)
    before_replay = replay.verify_pack(before)
    after_replay = replay.verify_pack(after)
    older, newer = entries(before), entries(after)
    counts = {kind: 0 for kind in ("added", "removed", "changed-line", "reclassified", "changed-interval")}
    changes = []
    for key in sorted(older.keys() | newer.keys()):
        old, new = older.get(key), newer.get(key)
        kind = change_kind(old, new)
        if kind is None:
            continue
        counts[kind] += 1
        if len(changes) < DETAIL_LIMIT:
            changes.append({"source": key[0], "line": key[1], "change": kind,
                            "before": line_state(old), "after": line_state(new)})
    old_sources = {item["source"]: item["sha256"] for item in before["inputs"]}
    new_sources = {item["source"]: item["sha256"] for item in after["inputs"]}
    source_changes = []
    for name in sorted(old_sources.keys() | new_sources.keys()):
        a, b = old_sources.get(name), new_sources.get(name)
        if a != b:
            source_changes.append({"source": name, "before_sha256": a, "after_sha256": b})
    old_pair = pair_snapshot(older, left_key, right_key)
    new_pair = pair_snapshot(newer, left_key, right_key)
    same_evidence = all(older.get(key) is not None and newer.get(key) is not None and
                        older[key]["kind"] == newer[key]["kind"] == "event" and
                        older[key]["line_sha256"] == newer[key]["line_sha256"]
                        for key in (left_key, right_key))
    if not same_evidence:
        assessment = "different-or-unavailable-evidence"
    elif old_pair["relation"] == new_pair["relation"]:
        assessment = "relation-stable"
    else:
        assessment = "relation-changed"
    return {
        "format": FORMAT,
        "before_replay": before_replay,
        "after_replay": after_replay,
        "options": {"before": before["options"], "after": after["options"],
                    "changed": before["options"] != after["options"]},
        "source_changes": source_changes,
        "line_changes": {"counts": counts, "total": sum(counts.values()),
                         "shown": changes, "omitted_details": sum(counts.values()) - len(changes)},
        "pair": {"left_citation": citation(*left_key), "right_citation": citation(*right_key),
                 "before": old_pair, "after": new_pair, "same_line_evidence": same_evidence,
                 "assessment": assessment},
        "interpretation": "Citations are physical source and line positions. Identical line hashes bind text at those positions, not event identity after line movement. Order is temporal under each asserted clock bound, not causality or measured skew. Verified packs establish internal consistency; authentic evidence requires independently trusted digests."
    }


def checked_pack(name, expected):
    raw = replay.read_workspace(name, replay.MAX_PACK_BYTES)
    actual = replay.digest(raw)
    if expected is not None:
        if HEX.fullmatch(expected) is None:
            raise replay.ReplayError("expected digest must be 64 lowercase hex digits")
        if expected != actual:
            raise replay.ReplayError("pack does not match expected SHA-256")
    return replay.load_pack(raw), actual


def demo():
    # Same exact synthetic log bytes; only the asserted clock bound changes.
    inputs = [("accepted.log", b"2026-10-18T10:00:00Z accepted\n"),
              ("completed.log", b"2026-10-18T10:00:02Z completed\n")]
    before = replay.make_pack(inputs)
    after = replay.make_pack(inputs, clock_uncertainty_ms=750)
    result = compare(before, after, "accepted.log", 1, "completed.log", 1)
    result["example"] = "synthetic, not a real incident"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="compare synthetic packs under two clock assumptions")
    command = sub.add_parser("compare", help="compare verified packs and one cited pair")
    command.add_argument("before")
    command.add_argument("after")
    command.add_argument("--left", nargs=2, required=True, metavar=("SOURCE", "LINE"))
    command.add_argument("--right", nargs=2, required=True, metavar=("SOURCE", "LINE"))
    command.add_argument("--expect-before-sha256")
    command.add_argument("--expect-after-sha256")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo()
        else:
            before, before_hash = checked_pack(args.before, args.expect_before_sha256)
            after, after_hash = checked_pack(args.after, args.expect_after_sha256)
            result = compare(before, after, args.left[0], int(args.left[1]),
                             args.right[0], int(args.right[1]))
            result["before_pack_sha256"] = before_hash
            result["after_pack_sha256"] = after_hash
        sys.stdout.buffer.write(replay.canonical(result) + b"\n")
        return 0
    except (OSError, ValueError, RecursionError) as exc:
        print("timeline-diff: " + replay.engine.visible(str(exc)), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
