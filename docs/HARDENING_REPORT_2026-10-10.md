# Nerva AIOps hardening report — 2026-10-10

Branch `claude/nerva-aiops-hardening-c01ba3` (worktree), from `b1c19ac`. Nothing was
pushed, merged or published. Evidence: [`docs/evidence/hardening-2026-10-10/`](evidence/hardening-2026-10-10/).
Operating guide: [`RUNBOOK.md`](RUNBOOK.md).

## 1. Audit verification

The supplied audit described `b1c19ac`. Each claim was reproduced first: the
regressions in `services/shared-nexus-api/tests/test_audit_reproductions.py` assert the
correct behaviour and **failed on `b1c19ac` (12 of 13)** before any change.

| Audit claim | Verdict | Now |
| --- | --- | --- |
| `NameError` when `M4_AUTO_BUILD_DELAY_SECONDS > 0` | Reproduced bug | Fixed, tested; delay now deployed (60 s) |
| Reconcile accepts incidents escalated before execution | Reproduced bug | Requires durable intent + unknown outcome |
| Reconcile repeatable, rewrites history | Reproduced bug | Once, immutable; identical repeat idempotent, contradiction 409 |
| Reconcile fabricates a SUCCESS `ActionResult` | Reproduced bug | Operator observation stored separately; no ActionResult |
| TTL wipe of RCA/evidence/proposal on a terminal incident | Reproduced bug | Decided incidents returned unchanged |
| TTL fails open on parse errors; duplicated logic | Reproduced bug | One helper; missing/malformed/naive/future = expired |
| Digest optional | Reproduced bug | Required for any real approval (428/409) |
| `POST /internal/decisions/build` unauthenticated | Reproduced bug | Ingest or operator token |
| Raw `Authorization` accepted for ingest | Reproduced bug | Strict `Bearer`, constant-time compare |
| Global lock blocks other incidents during RCA I/O | Reproduced bug (5 s stall) | Per-incident locks; all network I/O outside locks |
| Registry silently falls back when explicit file missing/invalid | Reproduced bug | Fails startup with a clear `RegistryError` |
| `max_scale_step`, tier, depends_on not enforced | Reproduced | Step enforced in M4 and M6; tier/depends_on validated and documented as informational |
| Hard-coded replica bound in approvals | Reproduced | Removed; registry only |
| Dispatcher drops on full queue, one thread, no close | Reproduced (3 of 6 lost) | Bounded workers, deferral + sweep, drain on close |
| Ingest token / async dispatch / registry not in any deployment | Reproduced | Wired into Compose, Dockerfiles, all manifests; gated by tests |
| `requests.post` monkeypatch branch in production | Reproduced | Removed; explicit transport injection |
| `conflict_error` missing; plain-string 409s | Reproduced | One taxonomy `{category, message, retryable}` |
| Lease loss noticed only on next write | Reproduced | Fencing token in every write + idle lease monitor |
| Actuator outside the lock | Partially fixed | The HTTP approve path still held the lock across `kubectl`; fixed |
| Lock-free reads, 3-state breaker, archive outbox | Already fixed | Kept; breaker now also recovers a lost half-open probe |
| Reconcile FAILED should pass through FAILED_REMEDIATION | Not applicable | Operator-observed failure stays ESCALATED (no actuator result exists); restart escalation now uses an explicit gated edge |
| Root/M3 suites and kind pipeline not run | Environment-verified | All suites run; live kind drills below |

Additional defects found during this work: `pyyaml`/`config/` missing from images (registry
could never load in containers); M6 offered scale targets M4 must refuse; M1 created an
HTTP client per request and probed storage on the event loop; a SCALE proposal always said
`LOW` risk; M2 false positives on healthy workloads (section 4); three defects found live
(section 5). The uncommitted provenance work in the main checkout was preserved (copied
verbatim as commit `1a6869a`) and then superseded; the main checkout was not modified.

## 2. What changed and why

| Area | Change |
| --- | --- |
| M4 state | Per-incident locks; each incident committed alone with optimistic revisions (`StorageConflict` on stale writes); committed copies published only after commit |
| M4 I/O | Diagnosis and recovery run begin (locked) → I/O (unlocked) → commit (locked, attempt token); stale results discarded; concurrent callers join the in-flight attempt (bounded) |
| M4 lease | PostgreSQL fencing generation checked inside every write transaction; monitor detects loss while idle; mutations, `/ready`, `/live` fail closed |
| M4 safety | Reconciliation, proposal freshness, digest, authentication as in section 1; provenance recorded per actual use and persisted |
| M4 ops | `/live` without I/O; health in the threadpool; worker pool; sanitized errors; registry info and breaker states in `/health` |
| Registry | Strict schema; explicit config must load; default lists only `payment-service` (the only workload with telemetry); multi-service example kept separately |
| M2 | Bounded, observable dispatcher; retry sweep; evidence refresh for active incidents; load scored per replica and only above normal; recalibrated frozen reference |
| M5/UI | Explicit operator boundary; digest-bound approvals; provenance, missing evidence, intent vs actuator vs operator observation, deadline, archive state; external-model answers labelled |
| M6 | Scale options limited by the registry |
| M1 | Pooled HTTP clients; storage probe off the event loop |
| Delivery | Wiring in Compose/Docker/Kubernetes; CI gates; runbook; drill helper |

## 3. Test results (final commit, Windows 11, Python 3.11.9, Node 24)

From [`test-results.txt`](evidence/hardening-2026-10-10/test-results.txt), PostgreSQL 16 in a
disposable container:

| Suite | Result |
| --- | --- |
| Root: contracts, M1, M2, registry, deployment wiring | 505 passed |
| M3 | 45 passed |
| M4 incl. real PostgreSQL restart, fencing, revisions | 180 passed (concurrency/audit set 3× stable) |
| M6 incl. PostgreSQL readback | 133 passed |
| M5 incl. PostgreSQL | 61 OK |
| UI behaviour | 11/11 |
| Grounded-answer evaluation | 9/9 |
| Six-service HTTP integration, PostgreSQL, restarts, M5 outage | 6 passed |
| Images | all 7 build |
| Compose config, YAML, all PowerShell scripts | valid |

Before changes the baseline was green except environment issues (Windows temp/path
length). One pre-existing timing test (`test_payment_probe_concurrency`) was flaky on this
host; its bound was widened from 0.2 s to 1.0 s (the blocked sink holds 5 s).
**CI gates are configured, not proven: no remote CI run happened.**

## 4. M2 detection: false positives and recalibration

Genuine telemetry from the isolated cluster, fetched through M1's window API.
References are frozen before evaluation; `capture3` never trained anything.

| Data | Before (2026-10-09 reference) | After |
| --- | --- | --- |
| capture3 bad deployment (held out) | recall 19/20, first alert 25 s | identical |
| capture3 traffic spike (held out) | recall 15/16, first alert 22 s | identical |
| capture3 healthy + post-recovery (held out) | 0/54 false alarms | 0/54 |
| **Independent** live healthy, 8 replicas, 10 RPS | **12/12 false alarms** | **0/12** |
| Healthy scaled-out, 8 replicas, 228 RPS (rule design) | 133/133 | 0/133 |
| Healthy quiet, 3 replicas, 30 RPS (rule design) | 24/181 | 21/181 (all during a measured 318 ms p95 excursion) |

Cause: absolute, two-sided `request_rate` and its relative change scored a healthy load
change as a fault. Fix: load is scored per replica and only above normal; its change only
counts when load is above normal. Honest limits: precision/recall are per reading on one
held-out drill; the independent healthy window has only 12 readings; the in-sample capture2
bad-deployment first alert moved from 15 s to 30 s. Live, the deployed version no longer
alerted on traffic onset (20:20:01) where the previous version had (19:19:54).

## 5. Live scenarios (kind cluster `nexus`, namespace `nexus-demo`)

New images ran against the cluster's existing PostgreSQL. All providers real, Kubernetes
actuator. Workload: `payment-service` v1, CPU 100m/500m, memory 128Mi/512Mi, constant
10 RPS generator from baseline through recovery; pinned M1 baseline thresholds unchanged.

**Rollback — RESOLVED** (`INC-20261010-193515`): v2 injected 19:34:18.198 → M2 alert
19:35:15 (57 s) → M3 `faulty_deployment` 0.9 → proposal 19:35:19 → M4 refused approval
without digest (428), M5 refused without operator token (401) → approved via M5 → real
rollback 19:35:58–19:36:13 → **M4 pod deleted 19:36:30, replacement took lease generation 2**
and resumed → M1 recovery 19:37:48: p95 737.5 → 9.52 ms, 5xx 9.0% → 0%, 94.4 s, hold
19:37:17–19:37:47 under the 11.875 ms ceiling. **M5 was down 19:36:30–19:38:18**: the
outbox retried (ConnectionError) and delivered on attempt 6 at 19:38:59. Real memory record;
Copilot citations all equal the stored record; unknown incident → `insufficient_evidence`.

**Scale — RESOLVED** (`INC-20261010-202515`): 150 RPS spike 20:24:47 on one replica → alert
20:25:15 → 60 s settle → M3 `traffic_spike` 1.0 (p95 2380 ms, CPU saturated) → M6 options
2/HIGH, 8/MEDIUM (8 = registry step cap) → approved → real SCALE 1→8 20:26:55–20:27:04 →
M1 recovery 20:28:37: p95 2377.9 → 9.51 ms, 0% 5xx, 92.5 s, ~160 RPS sustained through the
hold. Real memory; Copilot citations verified. Note: the 2026-10-09 drill scaled 1→10 (a
step of 9); the registry's declared `max_scale_step: 7` now forbids that.

**Safe failures observed (attempt 1 of each, kept as evidence):**
- Rollback attempt 1: drill patch lacked release annotations → M1 no deployment event →
  M3 `unknown` → M4 escalated, no action. Operator restored v1 manually.
- Scale attempt 1: diagnosis 10 s into the spike sized 2 replicas from a half-developed
  reading; not approved; expired approval refused (409); re-diagnosis blocked because M3
  rejected 5-minute-old evidence; after a usage-limit pause the spike had ended → `unknown`
  → escalated, no action.
- A traffic-onset false alarm (19:19:54) → M3 `unknown` → escalated, no action.

Defects these exposed, fixed and redeployed before attempt 2: missing settle delay, no M2
evidence refresh, change scoring on idle/falling load, stale recovery message, scale risk
label. **Restore:** traffic pods removed; `payment-service` template byte-identical to before
and back to 8 replicas; all five services rolled back to their recorded revisions (images,
env, replicas verified identical); added Secret keys and node images removed; original
services healthy. Retained: the drill incidents in PostgreSQL and two additive schema
changes (`incidents.revision`, `m4_writer_lease`), which the restored M4 ignores.

## 6. Remaining limitations

- One M4 writer per database; HA requires leader election (fencing already prevents split-brain writes).
- M2 keeps candidates in memory: a restart forgets undelivered handoffs (M4 dedups on retry).
- M2 evidence: three drills at one operating point plus short live windows; per-reading metrics only; no long-term false-alarm rate.
- The controlled HTTP fixture presents itself as a real M1, so harness memory can be "real"; real-memory claims rest on the live drills.
- Operator identity is asserted (`X-Nexus-Approver`) behind a shared token, not per-user authentication; no TLS between services.
- Multi-service is policy only: one service has telemetry and an actuator.
- Recovery is measured on a single 30 s hold; the generator's offered rate dropped during overload (145.5 RPS average for a 150 RPS target).
- Remote CI has not run these gates.

## 7. Next priorities

1. Run the CI workflow remotely and fix whatever differs from this Windows host.
2. Per-user operator authentication (OIDC) and TLS/mTLS between services.
3. Persist M2 correlation/handoff state; add leader election for M4.
4. More genuine captures at several operating points; report false-alarm rate per hour.
5. Pod-template release annotations from a real CD pipeline instead of drill values.

## 8. Assessment

**Demo-ready:** yes, for a supervised graduation demonstration in the local kind cluster.
Both fault scenarios ran end to end with real providers, human approval, real actuation,
measured recovery, restart and outage resilience, and grounded memory; failures degraded to
escalation without action. **Not production-ready:** single-writer M4, shared-secret operator
model, no TLS, in-memory M2 state, a single instrumented service and limited detection
evidence remain.
