"""The single source of truth for proposal freshness and integrity.

A proposal is approvable only while its creation timestamp is present,
timezone-aware, not in the future, and younger than the configured TTL.
Anything else (missing, malformed, naive, future) is treated as expired:
the check fails closed.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from app import config

CLOCK_SKEW_SECONDS = 5


def proposal_created_at(incident):
    raw = incident.get("_proposal_created_at")
    if not isinstance(raw, str):
        return None
    try:
        created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return created if created.tzinfo is not None else None


def proposal_expired(incident, now=None):
    now = now or datetime.now(timezone.utc)
    created = proposal_created_at(incident)
    if created is None or created > now + timedelta(seconds=CLOCK_SKEW_SECONDS):
        return True
    return (now - created).total_seconds() > config.PROPOSAL_TTL_SECONDS


def proposal_state(incident, now=None):
    if not incident.get("_proposal"):
        return None
    created = proposal_created_at(incident)
    return {"created_at": incident.get("_proposal_created_at"), "valid_timestamp": created is not None,
            "ttl_seconds": config.PROPOSAL_TTL_SECONDS,
            "expires_at": (created + timedelta(seconds=config.PROPOSAL_TTL_SECONDS)).isoformat() if created else None,
            "expired": proposal_expired(incident, now)}


def digest_of(proposal: dict, created_at: str | None = None) -> str:
    material = proposal if created_at is None else {"proposal": proposal, "created_at": created_at}
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def proposal_digest(incident) -> str:
    """Binds an approval to the exact proposal AND the diagnosis that produced it."""
    return digest_of(incident.get("_proposal") or {}, incident.get("_proposal_created_at") or "")
