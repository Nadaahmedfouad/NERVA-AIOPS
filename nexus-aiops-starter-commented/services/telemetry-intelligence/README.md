# M1 — Telemetry Intelligence

<!--
OWNER: M1

WHY IT EXISTS
=============
Converts raw operational signals into normalized telemetry used by the other modules.

Typical inputs:
- Prometheus metrics
- Loki logs
- Kubernetes/deployment events

Typical outputs:
- TelemetrySnapshot
- evidence windows
- RecoveryResult

Consumers:
M2, M3, M4/shared core, M6.
-->
