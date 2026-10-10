"""One error taxonomy for every M4 HTTP failure.

Every error body is {"detail": {"category", "message", "retryable"}}. Messages
are sanitized: first line only, internal paths and credentials redacted, and
bounded in length, so a dependency's error text never leaks to callers.
"""
import re
from fastapi import HTTPException

_PATH = re.compile(r"[a-zA-Z]:\\[\w\\\.-]+|/(?:[\w\.-]+/)+[\w\.-]+")
_SECRET = re.compile(r"(?i)(bearer\s+|password=|passwd=|token=|secret=|apikey=|api_key=)[^\s&;,'\"]+")
_URL_CREDENTIALS = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s:@]+:[^/\s@]+@")


def sanitize_message(msg: str) -> str:
    """First line only, credentials and internal paths redacted, at most 200 characters."""
    if not isinstance(msg, str):
        msg = str(msg)
    first_line = msg.split("\n")[0].strip()
    sanitized = _URL_CREDENTIALS.sub(r"\1<redacted>@", first_line)
    sanitized = _SECRET.sub(r"\1<redacted>", sanitized)
    sanitized = _PATH.sub("<internal-path>", sanitized)
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + "..."
    return sanitized


class IntegrationError(ValueError):
    category = "dependency_error"

    def __init__(self, message: str, *, status_code: int = 503, retryable: bool = True):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class RecoveryPending(IntegrationError):
    category = "recovery_pending"

    def __init__(self, message: str = "M1 is collecting post-action recovery evidence"):
        super().__init__(message, status_code=202, retryable=True)


class ConflictError(IntegrationError):
    """The request conflicts with the incident's current workflow state."""
    category = "conflict"

    def __init__(self, message: str, *, retryable: bool = False, status_code: int = 409):
        super().__init__(message, status_code=status_code, retryable=retryable)


class ProposalExpired(ConflictError):
    category = "proposal_expired"


class PreconditionRequired(ConflictError):
    category = "precondition_required"

    def __init__(self, message: str):
        super().__init__(message, status_code=428)


def api_error(status_code: int, category: str, message: str, retryable: bool = False) -> HTTPException:
    return HTTPException(status_code=status_code,
                         detail={"category": category, "message": sanitize_message(message), "retryable": retryable},
                         headers={"Retry-After": "15"} if retryable else None)


def as_http_error(error: ValueError) -> HTTPException:
    if isinstance(error, IntegrationError):
        return api_error(error.status_code, error.category, str(error), error.retryable)
    return api_error(400, "invalid_request", str(error))
