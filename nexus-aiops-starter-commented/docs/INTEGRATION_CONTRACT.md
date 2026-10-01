# Integration Contract

<!--
WHY THIS FILE EXISTS
====================
The six modules communicate using structured data.

If every member invents their own JSON format, integration will fail.

This document reminds the team that schemas are SHARED contracts.
-->

## Canonical Records

```text
TelemetrySnapshot
DeploymentEvent
AnomalyEvent
Incident
RCAResult
FinOpsContext
DecisionProposal
ActionResult
RecoveryResult
IncidentMemory
FinOpsRecommendation
```

## Example dependency

```text
M3 produces RCAResult
        ↓
M4 consumes RCAResult
```

So if M3 changes:

```json
"root_cause"
```

to:

```json
"cause"
```

M4 will break.

Therefore:

> Breaking changes require agreement from the producer and all consumers.

---

## Mocks

Mocks must use the SAME schema as real responses.

Why?

So this:

```text
MockRCAProvider
```

can later become:

```text
RealM3RCAProvider
```

without changing M4's decision logic.
