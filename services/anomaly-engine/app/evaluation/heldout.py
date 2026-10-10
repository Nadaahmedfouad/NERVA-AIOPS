"""Held-out evaluation of FROZEN references on genuine captures and healthy windows.

Fault captures give recall and detection latency per scenario; healthy M1
windows (fetched from /internal/telemetry/window) give false alarms at
operating points the reference was not trained on. Nothing here trains or tunes.

    python -m app.evaluation.heldout --reference old.json --reference new.json \
        --capture capture3.json --healthy window-a.json --healthy window-b.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from shared.contracts import TelemetrySnapshot

from ..pipeline import Pipeline
from ..reference import load_reference
from .timeline import score_capture


def _time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def fault_metrics(reference, capture, settle_s=90.0):
    rows = score_capture(reference, capture, settle_s)
    marks = {event["name"]: _time(event["at"]) for event in capture["events"]}
    result = {}
    for name in ("bad_deployment", "traffic_spike"):
        segment = [row for row in rows if row["segment"] == "fault:" + name]
        alerts = [row for row in segment if row["alert"]]
        first = min((_time(row["timestamp"]) for row in alerts), default=None)
        result[name] = {"readings": len(segment), "alerts": len(alerts),
                        "recall": round(len(alerts) / len(segment), 3) if segment else None,
                        "detection_latency_s": (first - marks[name + "_start"]).total_seconds() if first else None}
    normal = [row for row in rows if row["segment"] == "healthy" or row["segment"].startswith("after:")]
    result["normal"] = {"readings": len(normal), "false_alarms": sum(row["alert"] for row in normal)}
    return result


def healthy_metrics(reference, window):
    pipeline = Pipeline(reference=reference)
    alarms, drivers = 0, {}
    for point in window["points"]:
        reading = pipeline.process(TelemetrySnapshot.model_validate(
            {"timestamp": point["timestamp"], "service": window["service"], "version": window["version"],
             "metrics": point["metrics"]}))
        if reading.alert:
            alarms += 1
            top = max(reading.wobbles.items(), key=lambda item: item[1])[0]
            drivers[top] = drivers.get(top, 0) + 1
    return {"readings": len(window["points"]), "alarms": alarms, "drivers": drivers}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", action="append", required=True)
    parser.add_argument("--capture", action="append", default=[])
    parser.add_argument("--healthy", action="append", default=[])
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    report = {}
    for path in args.reference:
        reference = load_reference(path)
        entry = {"trained_on": list(reference.trained_on), "load_features": list(reference.load_features),
                 "alert_line_wobbles": reference.alert.wobbles, "captures": {}, "healthy_windows": {}}
        for capture in args.capture:
            name = Path(capture).name
            if name in reference.trained_on:
                raise SystemExit(f"{name} trained {path}; a held-out evaluation cannot use it")
            entry["captures"][name] = fault_metrics(reference, json.loads(Path(capture).read_text(encoding="utf-8")))
        for window in args.healthy:
            entry["healthy_windows"][Path(window).name] = healthy_metrics(
                reference, json.loads(Path(window).read_text(encoding="utf-8")))
        report[Path(path).name] = entry
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
