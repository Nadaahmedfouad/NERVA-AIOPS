"""Score every reading of a capture in time order, segment by segment.

`python -m app.realdata evaluate` judges one labelled run per scenario. This
replays the whole capture through a FROZEN reference, including the quiet
stretches after each fault is removed, where a remediated workload (new pods,
different memory) must read as healthy again. Each reading is labelled by the
capture's own events; the first `settle_s` seconds after a fault ends are
excluded because M1's one-minute rate windows still contain the fault.

    python -m app.evaluation.timeline reference/reference.json ../../docs/evidence/m2/capture3.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta

from shared.contracts import TelemetrySnapshot

from ..features import FEATURE_ORDER
from ..pipeline import Pipeline
from ..reference import load_reference


def _time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def segments(events, settle_s):
    marks = {event["name"]: _time(event["at"]) for event in events}
    found = []
    if "healthy_start" in marks and "healthy_end" in marks:
        found.append(("healthy", marks["healthy_start"], marks["healthy_end"]))
    starts = sorted((at, name[:-6]) for name, at in marks.items() if name.endswith("_start")
                    and name not in {"healthy_start", "drill_start"})
    for index, (start, name) in enumerate(starts):
        end = marks.get(name + "_end")
        if end is None:
            continue
        found.append(("fault:" + name, start, end))
        following = starts[index + 1][0] if index + 1 < len(starts) else marks.get("drill_end")
        if following is not None and end + timedelta(seconds=settle_s) < following:
            found.append(("after:" + name, end + timedelta(seconds=settle_s), following))
    return found


def label(moment, found):
    for name, start, end in found:
        if start <= moment < end:
            return name
    return "unlabelled"


def score_capture(reference, capture, settle_s=90.0):
    found = segments(capture["events"], settle_s)
    pipeline = Pipeline(reference=reference)
    rows = []
    for point in sorted(capture["points"], key=lambda p: p["timestamp"]):
        snapshot = TelemetrySnapshot.model_validate(point)
        reading = pipeline.process(snapshot)
        wobbles = reading.wobbles or {}
        top = max(wobbles.items(), key=lambda item: item[1]) if wobbles else (None, None)
        rows.append({"timestamp": point["timestamp"], "segment": label(snapshot.timestamp, found),
                     "alert": reading.alert, "score": reading.event.score,
                     "top_feature": top[0], "top_wobbles": None if top[1] is None else round(top[1], 2),
                     "memory": point["metrics"]["memory"], "request_rate": round(point["metrics"]["request_rate"], 2)})
    return rows


def summarize(rows):
    summary = {}
    for row in rows:
        entry = summary.setdefault(row["segment"], {"readings": 0, "alerts": 0, "drivers": {}})
        entry["readings"] += 1
        if row["alert"]:
            entry["alerts"] += 1
            entry["drivers"][row["top_feature"]] = entry["drivers"].get(row["top_feature"], 0) + 1
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("reference")
    parser.add_argument("captures", nargs="+")
    parser.add_argument("--settle-s", type=float, default=90.0)
    parser.add_argument("--json", action="store_true", help="print every scored reading")
    args = parser.parse_args(argv)
    reference = load_reference(args.reference)
    for path in args.captures:
        with open(path, encoding="utf-8") as handle:
            rows = score_capture(reference, json.load(handle), args.settle_s)
        trained = " (IN-SAMPLE: the reference was built from this capture)" if path.replace("\\", "/").rsplit("/", 1)[-1] in reference.trained_on else ""
        print(f"== {path}{trained}")
        print(json.dumps(summarize(rows), indent=2))
        if args.json:
            print(json.dumps(rows, indent=1))
    print("features:", ", ".join(FEATURE_ORDER), "| alert line (wobbles):", reference.alert.wobbles)


if __name__ == "__main__":
    main()
