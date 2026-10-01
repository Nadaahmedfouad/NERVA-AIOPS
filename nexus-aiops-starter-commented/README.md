# NEXUS — Autonomous AIOps & FinOps Platform

<!--
WHY THIS FILE EXISTS
====================
README.md is the first file anyone sees when they open the GitHub repository.

Its job is to answer:
1. What are we building?
2. Why are we building it?
3. How are the 6 members divided?
4. How do all modules connect?
5. How do I run or contribute to the project?
6. What counts as "done"?

WHO USES IT?
------------
- All 6 team members
- Your NTI instructors/reviewers
- Anyone reviewing the GitHub repository
- A new teammate who wants to understand the project quickly

WHY IT MATTERS
--------------
Without a strong README, the repository looks like random folders.
With this README, the repository tells one complete AIOps story.
-->

> NTI AIOps Final Project · 6-member team · 14-day delivery

NEXUS is one integrated AIOps lifecycle, not six disconnected assignments.

---

## 1. Project Mission

<!--
This section gives the one-sentence idea behind the entire project.
Every feature you add should contribute to this lifecycle.
-->

NEXUS should:

**DETECT → UNDERSTAND → DECIDE → HEAL → VALIDATE → LEARN → OPTIMIZE**

That means:

- detect an operational problem,
- understand what is happening,
- determine the root cause,
- recommend the safest action,
- require approval,
- execute the action,
- validate whether the system recovered,
- store the incident as reusable knowledge,
- use cost/resource context where relevant.

---

## 2. Main Demo Scenarios

<!--
WHY THIS SECTION EXISTS
-----------------------
Your final project should not be a collection of unrelated features.
These scenarios give the team two concrete end-to-end stories to build and test.

Whenever someone proposes a feature, ask:
"Does this help Scenario A or Scenario B?"
If not, it is probably not P0.
-->

### Scenario A — Bad Deployment

```text
healthy payment-service:v1
→ deploy faulty payment-service:v2
→ telemetry degrades
→ anomaly detected
→ incident created
→ RCA identifies faulty deployment
→ M4 recommends rollback
→ human approves
→ rollback
→ M1 validates recovery
→ M5 stores incident
```

### Scenario B — Traffic Spike

```text
healthy system
→ controlled traffic spike
→ request rate / CPU / latency increase
→ anomaly detected
→ RCA identifies legitimate demand increase
→ M6 compares cost/resource options
→ M4 recommends safe scale-up
→ human approves
→ scale
→ M1 validates recovery
→ M5 stores incident
```

---

## 3. Team Ownership

<!--
WHY THIS TABLE EXISTS
---------------------
It prevents duplicated work and confusion about ownership.

Each member has:
- a PRIMARY AIOps module,
- a small SHARED PLATFORM responsibility.

Nobody is "just backend" or "just frontend".
-->

| Member | Primary capability | Shared platform contribution |
|---|---|---|
| M1 | Observability & Telemetry Intelligence | health/config/logging conventions, smoke checks |
| M2 | ML Anomaly Detection & Correlation | shared Pydantic contracts + contract fixtures/tests |
| M3 | AI Root Cause Analysis | provider interfaces + timeout/error/fallback conventions |
| M4 | Decision Intelligence & Controlled Self-Healing | FastAPI bootstrap + state machine + incident/approval routes + orchestration |
| M5 | Incident Memory, RAG & Copilot | minimal NEXUS UI + incident/Copilot presentation |
| M6 | FinOps & Resource Optimization | PostgreSQL foundation + experiment/result persistence |

---

## 4. Architecture

<!--
WHY THIS DIAGRAM EXISTS
-----------------------
It shows the dependency direction between modules.

Important:
M4 does NOT invent the root cause.
M3 provides RCA.
M4 uses RCA + policies + FinOps context to produce a safe decision.
-->

```text
                         ┌──────────────────────┐
                         │       NEXUS UI       │
                         │   Shared Platform    │
                         └──────────┬───────────┘
                                    │
                            Shared FastAPI Core
                                    │
        ┌───────────────┬───────────┼───────────┬──────────────┬──────────────┐
        │               │           │           │              │              │
        ▼               ▼           ▼           ▼              ▼              ▼
 M1 Telemetry      M2 Anomaly   M3 RCA      M5 Memory      M6 FinOps    Shared Core
                   + Correlation              + Copilot
        │               │           │              │              │
        └───────────────┴───────────┴──────────────┴──────┬───────┘
                                                          ▼
                                                     M4 Decision
                                                     + Guardrails
                                                     + Remediation
                                                          │
                                                          ▼
                                                     Kubernetes
                                                          │
                                                          ▼
                                                   M1 Validation
                                                          │
                                                          ▼
                                                   M5 Memory
```

---

## 5. Repository Layout

<!--
WHY THESE FOLDERS EXIST
-----------------------
Each folder has one responsibility.
Avoid putting random files at repository root.
-->

```text
nexus/
├── apps/                     # Demo application that we intentionally stress/break
├── services/                 # M1-M6 + shared API services
├── observability/            # Prometheus/Grafana/Loki configuration
├── infrastructure/           # Docker/Kubernetes deployment resources
├── ci/                       # Jenkins / CI/CD configuration
├── contracts/                # Shared request/response schemas
├── mocks/                    # Fake but schema-valid upstream/downstream responses
├── data/                     # Datasets and experiment outputs
├── tests/                    # Contract + integration tests
├── scripts/                  # Reusable helper scripts
└── docs/                     # Team/architecture documentation
```

---

## 6. The Anti-Waiting Rule

<!--
THIS IS ONE OF THE MOST IMPORTANT RULES IN THE PROJECT.

Example:
M4 needs RCAResult from M3.
If M3 is not finished, M4 does NOT wait.

M4 uses a valid mock RCAResult and continues building the Decision Engine.
Later, the provider changes from "mock" to "real".
-->

If an upstream dependency is unavailable:

1. use the canonical contract,
2. use the canonical mock,
3. keep implementing,
4. replace the mock with the real provider at an integration checkpoint.

```text
M1 not ready → M2 uses mock metrics
M2 not ready → M3 uses mock anomaly
M3 not ready → M4 uses mock RCA
M6 not ready → M4 uses mock FinOps
M4 not ready → M5 uses mock action result
```

---

## 7. Incident State Machine

<!--
WHY A STATE MACHINE?
--------------------
Incidents cannot randomly jump between stages.

Example:
ACTION_PROPOSED → EXECUTING should be rejected
if approval has not happened.

This gives the project safety and predictable behavior.
-->

```text
DETECTED
  ↓
CORRELATING
  ↓
DIAGNOSING
  ↓
DIAGNOSED
  ↓
ACTION_PROPOSED
  ↓
AWAITING_APPROVAL
  ↓
EXECUTING
  ↓
VALIDATING
  ↓
RESOLVED
```

Failure path:

```text
VALIDATING
  ↓
FAILED_REMEDIATION
  ↓
ESCALATED
```

Important invariants:

- `EXECUTING` requires approval.
- `RESOLVED` requires successful M1 recovery validation.
- LLM output never directly becomes shell or kubectl execution.

---

## 8. API Ownership

<!--
WHY THIS TABLE EXISTS
---------------------
When someone needs an endpoint, this tells them which member owns it.
It also avoids two people implementing the same route.
-->

| Path | Owner |
|---|---|
| `/internal/telemetry/*` | M1 |
| `/internal/anomalies/*` | M2 |
| `/internal/correlation/*` | M2 |
| `/internal/rca/*` | M3 |
| `/internal/decisions/*` | M4 |
| `/internal/remediation/*` | M4 |
| `/internal/recovery/*` | M1 |
| `/internal/memory/*` | M5 |
| `/internal/copilot/*` | M5 |
| `/internal/finops/*` | M6 |
| `/api/incidents/*` | Shared Core |
| `/api/dashboard/*` | Shared Core |

Every service should expose:

```http
GET /health
```

---

## 9. Git Workflow

<!--
WHY THIS EXISTS
---------------
6 people editing one repository can easily overwrite each other.
Branches + Pull Requests reduce that risk.
-->

Recommended:

```text
main
develop

feature/m1-telemetry
feature/m2-anomaly
feature/m3-rca
feature/m4-decision
feature/m5-memory
feature/m6-finops
```

Rules:

- no direct push to `main`,
- create a feature branch,
- open a Pull Request,
- at least one teammate reviews,
- shared contract changes require producer + consumer agreement.

---

## 10. Day 1 Goal

<!--
DO NOT start by building every real component.

Day 1 is about creating a shared language between all members:
contracts, mocks, ownership, and skeleton.
-->

By end of Day 1:

- [ ] repo created
- [ ] ownership agreed
- [ ] contracts frozen
- [ ] mocks created
- [ ] shared FastAPI skeleton runs
- [ ] `/health` convention agreed
- [ ] state machine defined
- [ ] branch rules agreed
- [ ] local environment agreed

---

## 11. Day 3 Goal

<!--
WHY MOCKED END-TO-END FIRST?
----------------------------
If the full lifecycle works with mocks, integration architecture is correct.
Then each fake provider can be replaced by a real module independently.
-->

```text
mock anomaly
→ mock RCA
→ mock FinOps
→ M4 decision
→ approval
→ mock action
→ mock recovery
→ mock memory
```

---

## 12. Tools

### Core
- Git / GitHub
- Python
- FastAPI
- Pydantic
- PostgreSQL
- Docker
- Kubernetes
- kubectl

### Observability
- Prometheus
- Grafana
- Loki

### ML
- pandas
- scikit-learn

### Testing
- pytest
- FastAPI TestClient / httpx

### CI/CD
- Jenkins or GitHub Actions

### Bonus only after P0 works
- OpenTelemetry
- Tempo
- pgvector
- Terraform/AWS
- predictive scaling

---

## 13. M4 — Your Starting Order

<!--
YOU ARE M4.

Your job is NOT "make an AI agent that runs kubectl".

Your job is:
RCA result
→ deterministic decision
→ policy/guardrails
→ human approval
→ allowlisted remediation
→ request recovery validation
-->

Start in this order:

```text
1. shared FastAPI /health
2. IncidentStatus enum
3. allowed state transitions
4. state-machine tests
5. incident API
6. approve/reject API
7. provider interface using mocks
8. decision API
9. remediation API using mock executor
10. mocked end-to-end orchestration
11. real Kubernetes executor later
```

P0 actions:

```text
ROLLBACK
SCALE
ESCALATE
```

---

## 14. Definition of Done

A module is not done just because the code runs on one laptop.

It is done only when:

- it runs,
- contract is stable,
- tests exist,
- failures are handled,
- another module can consume it,
- evidence/results can be stored,
- it is integrated or has a valid mock,
- it contributes to the final lifecycle.
