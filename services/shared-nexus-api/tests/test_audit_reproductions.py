"""Regressions for the b1c19ac audit findings.

Each test asserts the *correct* behaviour. They were first run against the
unmodified b1c19ac code, where each failed (see docs/evidence/hardening-2026-10-10).
"""
import threading
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.incidents import find_incident, incident_operation, persist_incidents
from app.orchestration import orchestrator
from app.orchestration.orchestrator import build_decision, execute_approved_action
from app.remediation.audit import audit_records

client = TestClient(app)
TOKEN = "audit-repro-token"
AUTH = {"Authorization": "Bearer " + TOKEN, "X-Nexus-Approver": "alice"}


@pytest.fixture(autouse=True)
def operator_token(monkeypatch):
    monkeypatch.setenv("NEXUS_APPROVAL_TOKEN", TOKEN)


def create(incident_id, service="payment-service"):
    response = client.post("/api/incidents/", json={"incident_id": incident_id, "severity": "high",
                                                    "affected_services": [service]})
    assert response.status_code == 200, response.text


def anomaly(anomaly_id, service="payment-service"):
    return {"anomaly_id": anomaly_id, "timestamp": datetime.now(timezone.utc).isoformat(), "service": service,
            "score": 0.9, "severity": "high", "model": "test",
            "features": {"latency_p95_ms": 900.0, "http_5xx_rate": 0.2, "cpu": 0.4,
                         "memory": 0.4, "request_rate": 10.0}}


def test_settle_delay_ingest_does_not_raise(monkeypatch):
    """Audit #8: M4_AUTO_BUILD_DELAY_SECONDS > 0 raised NameError (timedelta)."""
    monkeypatch.setenv("M4_AUTO_BUILD_DELAY_SECONDS", "60")
    create("INC-DELAY")
    response = client.post("/internal/anomalies?incident_id=INC-DELAY", json=anomaly("ANO-DELAY"))
    assert response.status_code == 200, response.text
    not_before = datetime.fromisoformat(find_incident("INC-DELAY")["_diagnosis_not_before"])
    assert 50 <= (not_before - datetime.now(timezone.utc)).total_seconds() <= 60


def test_reconcile_rejects_incident_escalated_before_execution():
    """Audit #3: an engine escalation without any execution intent was reconciled to VALIDATING."""
    create("INC-NOEXEC")
    with incident_operation("INC-NOEXEC"):
        find_incident("INC-NOEXEC")["status"] = "ESCALATED"
        persist_incidents()
    response = client.post("/api/incidents/INC-NOEXEC/reconcile", headers=AUTH,
                           json={"outcome": "CONFIRMED", "note": "looks fine", "evidence": "kubectl rollout status"})
    assert response.status_code == 409
    incident = find_incident("INC-NOEXEC")
    assert incident["status"] == "ESCALATED"
    assert "_action_result" not in incident


def ambiguous(incident_id):
    create(incident_id)
    build_decision(incident_id)
    with incident_operation(incident_id):
        incident = find_incident(incident_id)
        incident["status"] = "ESCALATED"
        incident["_execution_ambiguous"] = True
        incident["_execution_intent"] = {"action_id": "ACT-AMBIG", "incident_id": incident_id, "action": "ROLLBACK",
                                         "replicas": None, "target": "payment-service",
                                         "started_at": datetime.now(timezone.utc).isoformat(),
                                         "approver": "alice", "status": "INTENT"}
        persist_incidents()


def test_reconcile_is_immutable_and_rejects_contradiction():
    """Audit #3: FAILED followed by CONFIRMED rewrote history and ended in VALIDATING."""
    ambiguous("INC-TWICE")
    body = {"outcome": "FAILED", "note": "rollout never progressed", "evidence": "kubectl rollout history rev 4"}
    first = client.post("/api/incidents/INC-TWICE/reconcile", headers=AUTH, json=body)
    assert first.status_code == 200, first.text
    contradiction = client.post("/api/incidents/INC-TWICE/reconcile", headers=AUTH,
                                json={**body, "outcome": "CONFIRMED"})
    assert contradiction.status_code == 409
    assert find_incident("INC-TWICE")["status"] == "ESCALATED"


def test_reconcile_never_fabricates_an_actuator_success():
    """Audit #3: reconcile wrote a SUCCESS ActionResult that no actuator produced."""
    ambiguous("INC-NOFAB")
    response = client.post("/api/incidents/INC-NOFAB/reconcile", headers=AUTH,
                           json={"outcome": "CONFIRMED", "note": "pods on v1", "evidence": "kubectl get rs"})
    assert response.status_code == 200, response.text
    incident = find_incident("INC-NOFAB")
    assert incident.get("_action_result") is None
    assert incident["_reconciliation"]["outcome"] == "CONFIRMED"
    assert incident["_reconciliation"]["observed_by"] == "alice"
    assert incident["_reconciliation"]["kind"] == "operator_observation"


def test_expired_proposal_on_resolved_incident_keeps_its_history():
    """Audit #4: build_decision on an expired RESOLVED incident wiped _rca/_evidence/_proposal."""
    create("INC-KEEP")
    build_decision("INC-KEEP")
    with incident_operation("INC-KEEP"):
        incident = find_incident("INC-KEEP")
        incident["status"] = "RESOLVED"
        incident["_proposal_created_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        persist_incidents()
    before = {key: find_incident("INC-KEEP").get(key) for key in ("_rca", "_evidence", "_proposal", "_decision")}
    response = client.post("/internal/decisions/build/INC-KEEP", headers=AUTH)
    # A decided workflow is history: the stored decision is returned, nothing is rewritten.
    assert response.status_code == 200
    after = {key: find_incident("INC-KEEP").get(key) for key in before}
    assert after == before and all(value is not None for value in after.values())


@pytest.mark.parametrize("created_at", ["not-a-timestamp", "2026-10-10T10:00:00", None])
def test_malformed_or_missing_proposal_timestamp_fails_closed(created_at):
    """Audit #4: a parse error (or missing timestamp) failed open and allowed approval."""
    create("INC-BADTS")
    build_decision("INC-BADTS")
    with incident_operation("INC-BADTS"):
        incident = find_incident("INC-BADTS")
        if created_at is None:
            incident.pop("_proposal_created_at")
        else:
            incident["_proposal_created_at"] = created_at
        persist_incidents()
    response = client.post("/api/incidents/INC-BADTS/approve", headers=AUTH)
    assert response.status_code == 409
    assert find_incident("INC-BADTS")["status"] == "AWAITING_APPROVAL"
    assert "_execution_intent" not in find_incident("INC-BADTS")


def test_build_endpoint_requires_authentication(monkeypatch):
    """Audit #5: POST /internal/decisions/build/{id} had no authentication."""
    monkeypatch.setenv("NEXUS_INGEST_TOKEN", "ingest-secret")
    create_headers = {"Authorization": "Bearer ingest-secret"}
    assert client.post("/api/incidents/", headers=create_headers, json={
        "incident_id": "INC-BUILDAUTH", "severity": "high", "affected_services": ["payment-service"]}).status_code == 200
    assert client.post("/internal/decisions/build/INC-BUILDAUTH").status_code == 401
    assert find_incident("INC-BUILDAUTH")["status"] == "DETECTED"


def test_ingest_rejects_non_bearer_authorization(monkeypatch):
    """Audit #5: a raw Authorization value without the Bearer scheme was accepted."""
    monkeypatch.setenv("NEXUS_INGEST_TOKEN", "ingest-secret")
    response = client.post("/api/incidents/", headers={"Authorization": "ingest-secret"}, json={
        "incident_id": "INC-RAW", "severity": "high", "affected_services": ["payment-service"]})
    assert response.status_code == 401


def test_real_approval_requires_the_current_proposal_digest(monkeypatch):
    """Audit #8: omitting x-proposal-digest skipped the integrity check."""
    create("INC-DIGEST")
    build_decision("INC-DIGEST")
    monkeypatch.setattr(orchestrator.remediation_backend, "REMEDIATION_BACKEND", "kubernetes")
    called = []
    monkeypatch.setattr(orchestrator, "execute_remediation", lambda *a, **k: called.append(1))
    response = client.post("/api/incidents/INC-DIGEST/approve", headers=AUTH)
    assert response.status_code == 428
    assert not called
    assert find_incident("INC-DIGEST")["status"] == "AWAITING_APPROVAL"


def test_slow_diagnosis_does_not_block_other_incidents(monkeypatch):
    """Audit #2: RCA I/O under the global lock blocked every other incident's mutation."""
    create("INC-SLOW")
    create("INC-FAST")
    entered, release = threading.Event(), threading.Event()
    real_rca = orchestrator.get_rca_result

    def slow_rca(incident_id):
        if incident_id == "INC-SLOW":
            entered.set()
            release.wait(5)
        return real_rca(incident_id)

    monkeypatch.setattr(orchestrator, "get_rca_result", slow_rca)
    worker = threading.Thread(target=build_decision, args=("INC-SLOW",))
    worker.start()
    try:
        assert entered.wait(2)
        started = time.monotonic()
        build_decision("INC-FAST")
        assert time.monotonic() - started < 1.0
        assert find_incident("INC-FAST")["status"] == "AWAITING_APPROVAL"
    finally:
        release.set()
        worker.join(5)
    assert find_incident("INC-SLOW")["status"] == "AWAITING_APPROVAL"


def test_reconcile_requires_operator_authentication():
    ambiguous("INC-RECAUTH")
    response = client.post("/api/incidents/INC-RECAUTH/reconcile",
                           json={"outcome": "CONFIRMED", "note": "n", "evidence": "kubectl shows v1 ready"})
    assert response.status_code == 401
    assert find_incident("INC-RECAUTH")["_execution_ambiguous"] is True
    assert not any(r["event_type"].startswith("MANUAL_RECONCILIATION") for r in audit_records)
