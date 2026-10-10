"""Actual PostgreSQL: writer fencing, proactive lease-loss detection and revision conflicts.

Requires M4_TEST_DATABASE_URL (a disposable database). Each test uses its own schema.
"""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

URL = os.getenv("M4_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="M4_TEST_DATABASE_URL is not set")


@pytest.fixture
def schema_url(monkeypatch):
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo
    schema = "m4_lease_" + uuid4().hex
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    url = make_conninfo(URL, options="-csearch_path=" + schema)
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("M4_STATE_BACKEND", "postgres")
    from app.db import workflow_store
    workflow_store.initialize()
    yield url
    workflow_store.close_lease(workflow_store._writer_lease)
    workflow_store.reset_lease_state()
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def incident(identity, revision, severity="high"):
    return {"incident_id": identity, "started_at": "2026-10-10T10:00:00+00:00", "status": "DETECTED",
            "severity": severity, "affected_services": ["payment-service"], "anomaly_ids": [],
            "_revision": revision}


def run_child(code, url):
    env = dict(os.environ, DATABASE_URL=url, M4_STATE_BACKEND="postgres",
               PYTHONPATH=str(Path(__file__).resolve().parents[1]) + os.pathsep + str(Path(__file__).resolve().parents[3]))
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=60)


def test_second_writer_cannot_acquire_while_first_is_alive(schema_url):
    from app.db import workflow_store
    workflow_store.acquire_lease()
    child = run_child("from app.db import workflow_store as w\ntry:\n    w.acquire_lease()\n    print('ACQUIRED')\n"
                      "except w.StorageError as e:\n    print('REFUSED', e)", schema_url)
    assert "REFUSED" in child.stdout, child.stdout + child.stderr


def test_takeover_is_detected_proactively_and_old_writes_are_fenced(schema_url):
    """The old owner keeps running after losing its session; it must not write after takeover."""
    import psycopg
    from app.db import workflow_store
    lease = workflow_store.acquire_lease()
    old_generation = workflow_store._lease_generation
    workflow_store.save_incidents([incident("INC-FENCE", 1)])
    # Simulate a partition: the server drops the old owner's lease session.
    pid = lease.execute("SELECT pg_backend_pid()").fetchone()[0]
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute("SELECT pg_terminate_backend(%s)", [pid])
    child = run_child("from app.db import workflow_store as w\nw.acquire_lease()\n"
                      "w.save_incidents([{'incident_id':'INC-FENCE','started_at':'2026-10-10T10:00:00+00:00',"
                      "'status':'CORRELATING','severity':'high','affected_services':['payment-service'],"
                      "'anomaly_ids':[],'_revision':2}])\nprint('GEN', w._lease_generation)", schema_url)
    assert "GEN" in child.stdout, child.stdout + child.stderr
    assert int(child.stdout.split()[-1]) == old_generation + 1
    # Idle detection: no write needed to notice the loss.
    assert workflow_store.check_lease() is False
    assert workflow_store.lease_lost() is True
    with pytest.raises(workflow_store.LeaseLost):
        workflow_store.save_incidents([incident("INC-FENCE", 3, severity="low")])
    with psycopg.connect(schema_url) as conn:
        status, severity, revision = conn.execute(
            "SELECT status, severity, revision FROM incidents WHERE incident_id='INC-FENCE'").fetchone()
    assert (status, severity, revision) == ("CORRELATING", "high", 2)


def test_fence_rejects_write_even_before_the_monitor_notices(schema_url):
    """Between takeover and the next lease check, the in-transaction fence still refuses."""
    import psycopg
    from app.db import workflow_store
    workflow_store.acquire_lease()
    with psycopg.connect(schema_url, autocommit=True) as conn:
        conn.execute("UPDATE m4_writer_lease SET generation = generation + 1")
    with pytest.raises(workflow_store.LeaseLost):
        workflow_store.save_incidents([incident("INC-RACE", 1)])
    with psycopg.connect(schema_url) as conn:
        assert conn.execute("SELECT count(*) FROM incidents").fetchone()[0] == 0


def test_revision_conflict_on_postgres(schema_url):
    from app.db import workflow_store
    workflow_store.acquire_lease()
    workflow_store.save_incidents([incident("INC-REV", 1)])
    workflow_store.save_incidents([incident("INC-REV", 2, severity="critical")])
    with pytest.raises(workflow_store.StorageConflict):
        workflow_store.save_incidents([incident("INC-REV", 2, severity="low")])
    with pytest.raises(workflow_store.StorageConflict):
        workflow_store.save_incidents([incident("INC-NEW", 5)])
    loaded = {row["incident_id"]: row for row in workflow_store.load("incidents")}
    assert loaded["INC-REV"]["severity"] == "critical" and loaded["INC-REV"]["_revision"] == 2
    assert "INC-NEW" not in loaded


def test_failed_transaction_writes_nothing(schema_url):
    from app.db import workflow_store
    workflow_store.acquire_lease()
    workflow_store.save_incidents([incident("INC-ATOMIC-A", 1)])
    with pytest.raises(workflow_store.StorageConflict):
        workflow_store.save_incidents([incident("INC-ATOMIC-B", 1), incident("INC-ATOMIC-A", 1)])
    assert {row["incident_id"] for row in workflow_store.load("incidents")} == {"INC-ATOMIC-A"}


def test_rows_written_before_revisions_existed_remain_writable(schema_url):
    import psycopg
    from psycopg.types.json import Jsonb
    from app.db import workflow_store
    workflow_store.acquire_lease()
    legacy = incident("INC-LEGACY", 0)
    legacy.pop("_revision")
    with psycopg.connect(schema_url) as conn:
        conn.execute("INSERT INTO incidents (incident_id, started_at, status, severity, payload) "
                     "VALUES (%s, %s, %s, %s, %s)", ["INC-LEGACY", legacy["started_at"], "DETECTED", "high", Jsonb(legacy)])
    loaded = {row["incident_id"]: row for row in workflow_store.load("incidents")}
    assert loaded["INC-LEGACY"]["_revision"] == 0
    workflow_store.save_incidents([incident("INC-LEGACY", 1, severity="critical")])
    with pytest.raises(workflow_store.StorageConflict):
        workflow_store.save_incidents([incident("INC-LEGACY", 1, severity="low")])
