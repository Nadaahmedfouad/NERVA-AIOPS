"""Operator and service-to-service authentication.

* Tokens are accepted only as `Authorization: Bearer <token>` (case-insensitive
  scheme, exactly one token) or the explicit X-Nexus-*-Token header.
* Secrets are compared in constant time (hmac.compare_digest on bytes).
* Without a configured token an endpoint is open ONLY in all-mock mode. Real
  operation without a configured secret fails closed with 503.
"""
import hmac
import os
import re
from fastapi import HTTPException

_BEARER = re.compile(r"^Bearer ([A-Za-z0-9\-._~+/]+=*)$", re.IGNORECASE)
_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._@:+-]{0,119}$")


def _error(status, category, message):
    return HTTPException(status_code=status, detail={"category": category, "message": message, "retryable": False},
                         headers={"WWW-Authenticate": "Bearer"} if status == 401 else None)


def bearer_token(authorization):
    """Strictly parse `Bearer <token>`; anything else is no credential at all."""
    if not isinstance(authorization, str):
        return None
    match = _BEARER.match(authorization.strip())
    return match.group(1) if match else None


def _matches(received, expected):
    return isinstance(received, str) and hmac.compare_digest(received.encode("utf-8"), expected.encode("utf-8"))


def _real_operation():
    from app.remediation import executor
    from app.orchestration.provenance import configured_modes
    return executor.REMEDIATION_BACKEND != "mock" or "real" in configured_modes().values()


def _identity(value, default, kind):
    identity = (value if isinstance(value, str) else default).strip()
    if not _IDENTITY.match(identity):
        raise _error(422, "invalid_request", f"{kind} identity must be 1-120 safe characters")
    return identity


def approval_token():
    return os.getenv("NEXUS_APPROVAL_TOKEN") or os.getenv("M5_SHARED_API_TOKEN")


def ingest_token():
    return os.getenv("NEXUS_INGEST_TOKEN") or os.getenv("NEXUS_SERVICE_TOKEN")


def verify_approver_auth(authorization=None, token=None, approver=None):
    from app.remediation import executor
    expected = approval_token()
    if not expected:
        if executor.REMEDIATION_BACKEND != "mock":
            raise _error(503, "not_configured", "Operator approval token is not configured")
        return _identity(approver, "operator", "Operator")
    received = token if isinstance(token, str) and token else bearer_token(authorization)
    if not _matches(received, expected):
        raise _error(401, "authentication_error", "Invalid or missing operator approval token")
    return _identity(approver, "operator", "Operator")


def require_explicit_identity(approver):
    """Actions that record an operator's own observation must name that operator."""
    if not isinstance(approver, str) or not approver.strip():
        raise _error(422, "invalid_request", "X-Nexus-Approver must name the reconciling operator")
    return _identity(approver, approver, "Operator")


def verify_ingest_auth(authorization: str | None = None, token: str | None = None, sender: str | None = None) -> str:
    """Service-to-service authentication for incident creation, anomaly ingest and diagnosis."""
    expected = ingest_token()
    if not expected:
        if _real_operation():
            raise _error(503, "not_configured", "Ingest token is not configured; real operation requires NEXUS_INGEST_TOKEN")
        return _identity(sender, "anonymous", "Sender")
    received = token if isinstance(token, str) and token else bearer_token(authorization)
    if not _matches(received, expected):
        raise _error(401, "authentication_error", "Invalid or missing ingest authentication token")
    return _identity(sender, "ingest-service", "Sender")


def verify_operator_or_ingest(authorization=None, ingest=None, approver_token=None):
    """Diagnosis may be triggered by an operator or by the ingest service."""
    if ingest_token() and _matches(ingest if ingest else bearer_token(authorization), ingest_token()):
        return "ingest-service"
    if approval_token() and _matches(approver_token if approver_token else bearer_token(authorization), approval_token()):
        return "operator"
    if not ingest_token() and not approval_token() and not _real_operation():
        return "anonymous"
    if not ingest_token() and not approval_token():
        raise _error(503, "not_configured", "Diagnosis requires a configured ingest or operator token")
    raise _error(401, "authentication_error", "Invalid or missing operator or ingest token")
