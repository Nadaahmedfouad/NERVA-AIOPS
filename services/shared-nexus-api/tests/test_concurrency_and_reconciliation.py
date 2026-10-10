"""Concurrency, stale-result rejection, competing writers and reconciliation."""
import threading
import time
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.incidents import find_incident, incidents, lock_for, persist_incidents
from app.db import workflow_store
from app.orchestration import orchestrator
from app.orchestration.lifecycle import restore_state
from app.orchestration.orchestrator import build_decision
from app.api.anomalies import anomalies
from app.remediation.audit import audit_records

client = TestClient(app)
TOKEN = "secret-token"
OPERATOR = {"Authorization": "Bearer " + TOKEN, "X-Nexus-Approver": "alice"}


@pytest.fixture(autouse=True)
def operator_token(monkeypatch):
    monkeypatch.setenv("NEXUS_APPROVAL_TOKEN", TOKEN)


@pytest.fixture
def durable_state(monkeypatch, tmp_path):
    monkeypatch.setenv("M4_STATE_BACKEND", "sqlite")
    monkeypatch.setenv("M4_SQLITE_PATH", str(tmp_path / "workflow.sqlite"))
    workflow_store.initialize()
    return tmp_path / "workflow.sqlite"


def restart():
    incidents.clear()
    anomalies.clear()
    audit_records.clear()
    restore_state()


def create(incident_id, service="payment-service"):
    response = client.post("/api/incidents/", json={"incident_id": incident_id, "severity": "high",
                                                    "affected_services": [service]})
    assert response.status_code == 200, response.text


def ambiguous(incident_id):
    create(incident_id)
    build_decision(incident_id)
    with lock_for(incident_id):
        incident = find_incident(incident_id)
        incident["status"] = "ESCALATED"
        incident["_execution_ambiguous"] = True
        incident["_execution_intent"] = {"action_id": "ACT-" + incident_id, "incident_id": incident_id,
                                         "action": "ROLLBACK", "replicas": None, "target": "payment-service",
                                         "started_at": datetime.now(timezone.utc).isoformat(),
                                         "approver": "alice", "status": "INTENT"}
        persist_incidents()


def reconcile(incident_id, outcome="CONFIRMED", headers=OPERATOR, evidence="kubectl shows revision 4 ready on v1"):
    return client.post(f"/api/incidents/{incident_id}/reconcile", headers=headers,
                       json={"outcome": outcome, "evidence": evidence, "note": "checked by hand"})


# -- concurrency ---------------------------------------------------------------

def test_reads_never_wait_for_a_mutation():
    create("INC-CONCUR-A")
    create("INC-CONCUR-B", service="cart-service")
    holding, release = threading.Event(), threading.Event()

    def hold():
        with lock_for("INC-CONCUR-A"):
            holding.set()
            release.wait(5)

    thread = threading.Thread(target=hold)
    thread.start()
    try:
        assert holding.wait(2)
        started = time.monotonic()
        assert client.get("/api/incidents/INC-CONCUR-A/context").status_code == 200
        assert client.get("/api/incidents/INC-CONCUR-B").status_code == 200
        assert time.monotonic() - started < 1.0
    finally:
        release.set()
        thread.join(3)


def test_two_incidents_progress_concurrently_through_slow_dependencies(monkeypatch):
    """A slow RCA for A and a slow actuator for B do not serialize each other."""
    create("INC-A")
    create("INC-B")
    build_decision("INC-B")
    rca_entered, rca_release = threading.Event(), threading.Event()
    act_entered, act_release = threading.Event(), threading.Event()
    real_rca, real_execute = orchestrator.get_rca_result, orchestrator.execute_remediation

    def slow_rca(incident_id):
        rca_entered.set()
        rca_release.wait(5)
        return real_rca(incident_id)

    def slow_execute(*args, **kwargs):
        act_entered.set()
        act_release.wait(5)
        return real_execute(*args, **kwargs)

    monkeypatch.setattr(orchestrator, "get_rca_result", slow_rca)
    monkeypatch.setattr(orchestrator, "execute_remediation", slow_execute)
    results = {}
    a = threading.Thread(target=lambda: results.setdefault("A", build_decision("INC-A")))
    b = threading.Thread(target=lambda: results.setdefault("B", client.post("/api/incidents/INC-B/approve",
                                                                            headers=OPERATOR).status_code))
    a.start()
    b.start()
    try:
        assert rca_entered.wait(2) and act_entered.wait(2), "both slow calls must be in flight at once"
        # While both dependencies are blocked, either incident still accepts other work.
        create("INC-C")
        assert client.get("/api/incidents/INC-A/context").json()["incident"]["status"] == "DIAGNOSING"
        assert client.get("/api/incidents/INC-B/context").json()["incident"]["status"] == "EXECUTING"
        assert reconcile("INC-B").status_code == 409  # executing, not ambiguous
        duplicate = client.post("/api/incidents/INC-B/approve", headers=OPERATOR)
        assert duplicate.status_code == 409 and duplicate.json()["detail"]["retryable"] is True
    finally:
        rca_release.set()
        act_release.set()
        a.join(5)
        b.join(5)
    assert results["B"] == 200
    assert find_incident("INC-A")["status"] == "AWAITING_APPROVAL"
    assert find_incident("INC-B")["status"] == "VALIDATING"


def test_concurrent_duplicate_diagnosis_is_rejected_not_duplicated(monkeypatch):
    create("INC-DUP")
    entered, release = threading.Event(), threading.Event()
    calls = []
    real_rca = orchestrator.get_rca_result

    def slow(incident_id):
        calls.append(incident_id)
        entered.set()
        release.wait(5)
        return real_rca(incident_id)

    monkeypatch.setattr(orchestrator, "get_rca_result", slow)
    worker = threading.Thread(target=build_decision, args=("INC-DUP",))
    worker.start()
    try:
        assert entered.wait(2)
        response = client.post("/internal/decisions/build/INC-DUP", headers=OPERATOR)
        assert response.status_code == 409 and response.json()["detail"]["retryable"] is True
    finally:
        release.set()
        worker.join(5)
    assert calls == ["INC-DUP"]
    assert find_incident("INC-DUP")["status"] == "AWAITING_APPROVAL"


def test_stale_diagnosis_result_is_discarded(monkeypatch):
    """A result whose attempt was superseded (e.g. incident escalated meanwhile) is never applied."""
    create("INC-STALE")
    entered, release = threading.Event(), threading.Event()
    real_rca = orchestrator.get_rca_result

    def slow(incident_id):
        entered.set()
        release.wait(5)
        return real_rca(incident_id)

    monkeypatch.setattr(orchestrator, "get_rca_result", slow)
    outcome = {}

    def run():
        try:
            build_decision("INC-STALE")
        except Exception as exc:  # noqa: BLE001 - asserted below
            outcome["error"] = exc

    worker = threading.Thread(target=run)
    worker.start()
    assert entered.wait(2)
    with lock_for("INC-STALE"):
        find_incident("INC-STALE")["_diagnosis_attempt"]["attempt_id"] = "DIAG-superseded"
        persist_incidents()
    release.set()
    worker.join(5)
    assert "superseded" in str(outcome["error"])
    incident = find_incident("INC-STALE")
    assert "_proposal" not in incident and "_rca" not in incident


def test_stale_recovery_measurement_is_discarded(monkeypatch):
    create("INC-RSTALE")
    build_decision("INC-RSTALE")
    assert client.post("/api/incidents/INC-RSTALE/approve", headers=OPERATOR).status_code == 200
    entered, release = threading.Event(), threading.Event()

    def slow_measure(*args, **kwargs):
        entered.set()
        release.wait(5)
        return {"incident_id": "INC-RSTALE", "success": True, "source": "mock"}

    monkeypatch.setattr(orchestrator, "validate_recovery", slow_measure)
    responses = {}
    worker = threading.Thread(target=lambda: responses.setdefault(
        "r", client.post("/internal/recovery/validate/INC-RSTALE")))
    worker.start()
    assert entered.wait(2)
    with lock_for("INC-RSTALE"):
        # A competing change to the action under measurement.
        find_incident("INC-RSTALE")["action_completed_at"] = datetime.now(timezone.utc).isoformat()
        persist_incidents()
    release.set()
    worker.join(5)
    assert responses["r"].status_code == 409
    assert find_incident("INC-RSTALE")["status"] == "VALIDATING"


def test_competing_writer_cannot_overwrite_a_newer_revision(durable_state):
    """Two processes sharing storage: the stale writer's update is rejected, not applied."""
    create("INC-RACE")
    stale_copy = dict(find_incident("INC-RACE"))
    with lock_for("INC-RACE"):
        find_incident("INC-RACE")["severity"] = "critical"
        persist_incidents()
    stale_copy["_revision"] += 1  # The other writer believes it is next.
    stale_copy["severity"] = "low"
    with pytest.raises(workflow_store.StorageConflict):
        workflow_store.save_incidents([stale_copy])
    restart()
    assert find_incident("INC-RACE")["severity"] == "critical"


def test_database_failure_leaves_committed_state_and_reports_storage_unavailable(durable_state, monkeypatch):
    create("INC-DBFAIL")
    with monkeypatch.context() as failing:
        failing.setattr(workflow_store, "save_incidents", Mock(side_effect=workflow_store.StorageError("outage")))
        response = client.post("/internal/decisions/build/INC-DBFAIL", headers=OPERATOR)
        assert response.status_code == 503
        assert response.json()["detail"]["category"] == "storage_unavailable"
    assert find_incident("INC-DBFAIL")["status"] == "DETECTED"
    assert client.post("/internal/decisions/build/INC-DBFAIL", headers=OPERATOR).status_code == 200


def test_lost_lease_fails_mutations_and_readiness(monkeypatch):
    create("INC-LEASE")
    monkeypatch.setattr(workflow_store, "_lease_lost", True)
    monkeypatch.setattr(workflow_store, "backend", lambda: "sqlite")
    response = client.post("/internal/decisions/build/INC-LEASE", headers=OPERATOR)
    assert response.status_code == 503 and response.json()["detail"]["category"] == "lease_lost"
    assert client.get("/ready").status_code == 503
    assert client.get("/live").status_code == 503
    assert find_incident("INC-LEASE")["status"] == "DETECTED"


# -- reconciliation ------------------------------------------------------------

def test_reconcile_requires_authentication_and_explicit_operator():
    ambiguous("INC-REC-AUTH")
    assert reconcile("INC-REC-AUTH", headers={}).status_code == 401
    assert reconcile("INC-REC-AUTH", headers={"Authorization": "Bearer wrong", "X-Nexus-Approver": "a"}).status_code == 401
    assert reconcile("INC-REC-AUTH", headers={"Authorization": "Bearer " + TOKEN}).status_code == 422
    assert find_incident("INC-REC-AUTH")["_execution_ambiguous"] is True


def test_reconcile_requires_evidence():
    ambiguous("INC-REC-EVID")
    assert reconcile("INC-REC-EVID", evidence="ok").status_code == 422
    assert find_incident("INC-REC-EVID")["_execution_ambiguous"] is True


def test_reconcile_rejects_nonexistent_execution():
    create("INC-REC-NONE")
    build_decision("INC-REC-NONE")
    assert client.post("/api/incidents/INC-REC-NONE/reject", headers=OPERATOR).status_code == 200
    with lock_for("INC-REC-NONE"):
        find_incident("INC-REC-NONE")["_execution_ambiguous"] = True  # flag without any durable intent
        persist_incidents()
    assert reconcile("INC-REC-NONE").status_code == 409
    assert reconcile("UNKNOWN-INCIDENT").status_code == 404


def test_reconcile_confirmed_measures_recovery_without_fabricating_an_action_result():
    ambiguous("INC-REC-OK")
    response = reconcile("INC-REC-OK")
    assert response.status_code == 200 and response.json()["status"] == "VALIDATING"
    incident = find_incident("INC-REC-OK")
    assert incident.get("_action_result") is None and incident.get("_execution_result") is None
    assert incident["_reconciliation"]["observed_by"] == "alice"
    assert incident["_action_completed_source"] == "operator_reconciliation"
    deadline = datetime.fromisoformat(incident["recovery_deadline_at"])
    reconciled = datetime.fromisoformat(incident["_reconciliation"]["reconciled_at"])
    from app import config
    assert (deadline - reconciled).total_seconds() == pytest.approx(config.RECOVERY_TIMEOUT_SECONDS)
    assert client.get("/api/incidents/INC-REC-OK/actions/latest").status_code == 404
    assert reconcile("INC-REC-OK").status_code == 200  # identical repeat is idempotent
    assert reconcile("INC-REC-OK", outcome="FAILED").status_code == 409
    resolved = client.post("/internal/recovery/validate/INC-REC-OK")
    assert resolved.status_code == 200 and resolved.json()["status"] == "RESOLVED"
    memory = find_incident("INC-REC-OK")["_archive_outbox"]["payload"]["memory"]
    assert "action_outcome:operator_observed_confirmed" in memory["tags"]


def test_reconcile_failed_is_final_and_archived_as_failure():
    ambiguous("INC-REC-FAIL")
    assert reconcile("INC-REC-FAIL", outcome="FAILED").status_code == 200
    incident = find_incident("INC-REC-FAIL")
    assert incident["status"] == "ESCALATED" and incident.get("_action_result") is None
    assert reconcile("INC-REC-FAIL", outcome="CONFIRMED").status_code == 409
    assert find_incident("INC-REC-FAIL")["status"] == "ESCALATED"
    payload = incident["_archive_outbox"]["payload"]
    assert payload["memory"]["action_success"] is False and payload["resolved"] is False
    execute = Mock()
    import app.orchestration.orchestrator as module
    module_execute, module.execute_remediation = module.execute_remediation, execute
    try:
        assert client.post("/api/incidents/INC-REC-FAIL/approve", headers=OPERATOR).status_code == 409
    finally:
        module.execute_remediation = module_execute
    execute.assert_not_called()


def test_reconciliation_survives_restart_and_stays_immutable(durable_state):
    ambiguous("INC-REC-RESTART")
    assert reconcile("INC-REC-RESTART").status_code == 200
    restart()
    incident = find_incident("INC-REC-RESTART")
    assert incident["_reconciliation"]["outcome"] == "CONFIRMED" and incident["status"] == "VALIDATING"
    assert reconcile("INC-REC-RESTART", outcome="FAILED").status_code == 409
    assert any(r["event_type"] == "MANUAL_RECONCILIATION_CONFIRMED" for r in audit_records)
