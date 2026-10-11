from unittest.mock import patch

import pytest

from app.api.incidents import (
    IncidentCreate,
    create_incident,
    find_incident,
)
from app.orchestration.lifecycle import _diagnose
from app.providers.errors import IntegrationError


@pytest.mark.parametrize(
    "retryable",
    [False, True],
)
def test_diagnosis_retry_policy(retryable):
    incident_id = f"INC-RETRY-POLICY-{retryable}"

    create_incident(
        IncidentCreate(
            incident_id=incident_id,
            severity="high",
            affected_services=["payment-service"],
        )
    )

    incident = find_incident(incident_id)
    incident["status"] = "DIAGNOSING"
    incident["_diagnosis_pending"] = True

    error = IntegrationError(
        "M3 RCA request failed with status 502",
        status_code=503,
        retryable=retryable,
    )

    with patch(
        "app.orchestration.orchestrator.build_decision",
        side_effect=error,
    ):
        _diagnose(incident_id)

    updated = find_incident(incident_id)

    assert updated["_diagnosis_pending"] is retryable
    assert updated["_diagnosis_last_error"] == str(error)

    if retryable:
        assert updated.get("_diagnosis_retry_at") is not None
    else:
        assert updated.get("_diagnosis_retry_at") is None
        assert updated.get("_diagnosis_attempt") is None