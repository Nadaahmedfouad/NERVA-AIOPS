# Nerva AIOps runbook

Commands are PowerShell from the repository root unless marked otherwise.

## 1. Credentials

Four secrets, all at least 32 URL-safe characters. The ingest token must differ
from the approval token (M4 refuses to start otherwise).

| Secret | Holder | Purpose |
| --- | --- | --- |
| `NEXUS_APPROVAL_TOKEN` | M4, M5 (`M5_SHARED_API_TOKEN`) | operator decisions and M4 -> M5 archival |
| `NEXUS_INGEST_TOKEN` | M2, M4 | incident ingest, anomaly linking, diagnosis |
| `M5_UI_OPERATOR_TOKEN` | M5; typed by the operator per decision | dashboard trust boundary |
| `NEXUS_DB_PASSWORD` | PostgreSQL, M4/M5/M6 | workflow, memory and FinOps storage |

`scripts/start-stack.ps1` generates and keeps them in `.review-branches/stack-runtime.json`
(git-ignored) and never prints them. For Kubernetes, create the `nexus-runtime`
Secret privately with those keys plus `POSTGRES_*`, `DATABASE_URL` and `M5_OPERATOR_ID`
(see `docs/FULL_STACK_VERIFICATION.md`). Never commit a Secret.

Without `M5_UI_OPERATOR_TOKEN` the dashboard is read-only. `M5_UI_TRUSTED_NETWORK=true`
is an explicit alternative only when M5 is reachable solely from a trusted network.

## 2. Start the stack

```powershell
.\scripts\start-stack.ps1            # Compose: real providers, mock actuator, PostgreSQL
.\scripts\check-stack.ps1 -AllowMockActuator
```

Compose never changes infrastructure (`REMEDIATION_BACKEND=mock`). Real actions run only
in the isolated kind cluster `nexus`, namespace `nexus-demo` (`docs/FULL_STACK_VERIFICATION.md`).

Health: every service has `/health`; `/ready` is truthful (503 when storage, lease or a
required dependency is unavailable). M4 `/live` has no dependency I/O and fails only when
the writer lease is lost, so outages never restart M4 but a lost lease does.

## 3. Collect a baseline

Start constant traffic, wait at least three minutes, then measure the last 75 s:

```powershell
.\scripts\generate-traffic.ps1 -DurationSeconds 600 -Concurrency 5
$end = [DateTimeOffset]::UtcNow.AddSeconds(-15)
Invoke-RestMethod -Method Post http://localhost:8001/internal/baselines/measure -ContentType application/json -Body (@{
  service='payment-service'; start=$end.AddSeconds(-75).ToString('o'); end=$end.ToString('o'); step_seconds=15 } | ConvertTo-Json)
```

In the cluster, `scripts/live-drill.py` runs the same calls from inside a pod and reads
credentials only from that pod's environment:

```bash
kubectl -n nexus-demo exec -i deploy/shared-nexus-api -- python - baseline < scripts/live-drill.py
```

Keep the workload, traffic and pinned SLO unchanged from baseline through recovery.

## 4. Run the demonstration

1. Inject a fault in the isolated cluster only. A deployment fault must carry release
   provenance on the pod template (`nexus.io/previous-version`, `nexus.io/version`,
   `nexus.io/commit-sha`, `nexus.io/pipeline-id`); without it M1 records no deployment
   event and M3 correctly answers `unknown`.
2. M2 detects and hands off; M4 waits `M4_AUTO_BUILD_DELAY_SECONDS` (60) so diagnosis uses
   a developed reading, then calls M3, M6 and M1 evidence capture.
3. Review the proposal in the dashboard (`http://127.0.0.1:8005/`), enter the operator token,
   approve. The approval carries the proposal digest; M4 refuses a missing (428), stale
   (409) or expired (409) proposal.
4. M4 actuates once, records the result, then M1 measures recovery against the pinned
   baseline. Only M1's measurement resolves an incident.
5. M4 archives the terminal incident to M5. Workflows with any mock input or effect go to
   mock memory with `source:mixed`; real memory holds only fully real workflows.
6. Ask Copilot "Did it work?" — answers are deterministic and cite stored fields; an
   external model, if configured, is labelled as such.

Scripted path: `scripts/run-integration-incident.ps1 -AnomalyPath <file> -Approve`
(uses the ingest token for ingest/diagnosis and the operator token plus digest to approve).

## 5. Inspect failures

| Symptom | Where to look |
| --- | --- |
| Incident ESCALATED without action | `/api/incidents/{id}/context`: `rca` (`unknown` = insufficient evidence), `missing`, `audit` |
| Approval refused | 401 auth, 428 missing digest, 409 `proposal_expired` or changed proposal; rebuild via `POST /internal/decisions/build/{id}` |
| `execution_ambiguous` | outcome unknown after a restart; reconcile once with evidence: `POST /api/incidents/{id}/reconcile` (`outcome`, `evidence`, `X-Nexus-Approver`) |
| Stuck VALIDATING | `workflow.recovery_error`, `workflow.recovery_deadline`; M1 `/internal/recovery/{id}` |
| Archive not delivered | `workflow.archive_status/attempts/error`; `POST /api/incidents/{id}/archive/retry` |
| M4 503 `lease_lost` | another writer owns the database; restart the instance |
| M2 not handing off | M2 `/health`: `dependencies.shared_api`, `dispatch` (queue, deferred, failures) |
| Diagnosis 503 "M3 RCA unavailable" | M3 rejected stale or mismatched evidence; M2 re-links fresh alerts every 60 s |

Errors are `{"detail": {"category", "message", "retryable"}}` with secrets and paths redacted.

## 6. Repeat verification

```powershell
python -m pytest tests/contract tests/m1 tests/m2 tests/test_k8s_traffic.py tests/test_service_registry.py tests/test_deployment_wiring.py -q
foreach ($s in 'root-cause-analysis','shared-nexus-api','finops-engine') { Push-Location services/$s; python -m pytest tests -q; Pop-Location }
Push-Location services/incident-memory; python -m unittest discover -s tests -q; Pop-Location
node --test ui/copilot/storage.test.mjs ui/incident/view.test.mjs
python services/incident-memory/scripts/evaluate.py
# With a disposable PostgreSQL:
$env:M4_TEST_DATABASE_URL = $env:M5_TEST_DATABASE_URL = $env:NEXUS_INTEGRATION_DATABASE_URL = '<disposable database URL>'
python -m pytest tests/integration -q
```

On Windows keep pytest's temporary directory short (`--basetemp C:\t\run`): M1 writes
temporary files whose full paths can exceed 260 characters under deep temp folders.

M2 detector changes: retrain only from `capture1/2` (`python -m app.realdata train`),
freeze, then evaluate with `python -m app.evaluation.heldout` (it refuses training captures).
