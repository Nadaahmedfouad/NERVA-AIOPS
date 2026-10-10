from fastapi import APIRouter, Header
from pydantic import BaseModel
from app.api.auth import verify_operator_or_ingest
from app.decision_engine.engine import decide_from_rca
from app.decision_engine.models import DecisionResult
from app.orchestration.orchestrator import build_decision
from app.providers.errors import as_http_error

router = APIRouter(prefix="/internal/decisions", tags=["decisions"])

class DecisionRequest(BaseModel):
    rca: dict
    finops: dict | None = None

@router.post("/evaluate", response_model=DecisionResult)
def evaluate_decision(request: DecisionRequest):
    # Pure function of the request body: reads and changes no workflow state.
    return decide_from_rca(request.rca, request.finops)

@router.post("/build/{incident_id}", response_model=DecisionResult)
def build_incident_decision(incident_id: str, authorization: str | None = Header(default=None),
                            x_nexus_ingest_token: str | None = Header(default=None),
                            x_nexus_approver_token: str | None = Header(default=None)):
    verify_operator_or_ingest(authorization, x_nexus_ingest_token, x_nexus_approver_token)
    try:
        return build_decision(incident_id)
    except ValueError as exc:
        raise as_http_error(exc) from exc
