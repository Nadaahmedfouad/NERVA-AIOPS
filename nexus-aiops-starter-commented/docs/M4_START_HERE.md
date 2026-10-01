# M4 — Start Here

<!--
THIS FILE IS SPECIFICALLY FOR YOU.

M4 owns:
1. Decision Intelligence
2. Controlled Self-Healing
3. Shared orchestration coordination

The most important design idea:
M4 does NOT allow an LLM to execute arbitrary commands.

Instead:

RCA
→ structured decision
→ policy validation
→ human approval
→ allowlisted executor
→ recovery validation
-->

## Step 1 — Shared FastAPI Bootstrap

Create:

```text
services/shared-nexus-api/
└── app/
    ├── main.py
    ├── api/
    │   ├── incidents.py
    │   └── approvals.py
    ├── state_machine/
    ├── providers/
    └── config/
```

Why?

Because the shared API coordinates the lifecycle between modules.

Start with:

```http
GET /health
```

Do not start with Kubernetes automation.

---

## Step 2 — Incident State Machine

States:

```text
DETECTED
CORRELATING
DIAGNOSING
DIAGNOSED
ACTION_PROPOSED
AWAITING_APPROVAL
EXECUTING
VALIDATING
RESOLVED
FAILED_REMEDIATION
ESCALATED
```

Why?

Without a state machine, an incident could accidentally jump from:

```text
DETECTED → RESOLVED
```

which makes no sense.

Tests must reject:

- illegal state jumps,
- `EXECUTING` without approval,
- `RESOLVED` without successful M1 validation.

---

## Step 3 — Incident APIs

Implement:

```http
POST /api/incidents
GET  /api/incidents
GET  /api/incidents/{id}
POST /api/incidents/{id}/approve
POST /api/incidents/{id}/reject
```

Why?

M5 UI and the shared lifecycle need one place to read/change incident state.

---

## Step 4 — Decision Engine

Endpoint:

```http
POST /internal/decisions/evaluate
```

Input should eventually include:

```text
RCAResult
FinOpsContext (when needed)
runtime/policy context
```

Output:

```text
DecisionProposal
```

### Bad deployment policy

```text
IF RCA = faulty_deployment
AND confidence >= threshold
AND previous version exists
THEN recommend ROLLBACK
AND require approval
```

### Traffic policy

```text
IF RCA = traffic_spike
AND SLO is degraded
AND target is allowed
AND requested replicas are safe
THEN compare M6 options
AND recommend SCALE
AND require approval
```

### Unknown

```text
ESCALATE
```

---

## Step 5 — Remediation API

Endpoint:

```http
POST /internal/remediation/execute
```

FIRST VERSION:

```text
MockExecutor
```

Later:

```text
KubernetesExecutor
```

Why start with a mock?

Because you need to prove orchestration before introducing real operational risk.

---

## Step 6 — Day-3 Vertical Slice

Get this working:

```text
mock anomaly
→ mock RCA
→ mock FinOps
→ M4 decision
→ approval
→ mock action
→ mock recovery
```

If this works, your architecture is alive even before all real modules are finished.

---

## Step 7 — Real Kubernetes Execution

Only after the mock flow works.

Safety rules:

- allowlist namespace,
- allowlist service,
- validate parameters,
- require approval,
- store audit record,
- never execute arbitrary user/LLM shell text.

Actions:

```text
ROLLBACK
SCALE
ESCALATE
```
