"""Which providers a workflow ACTUALLY used, recorded at the moment of use.

Configuration may change between diagnosis, execution and recovery (for
example a restart with a mock actuator). The workflow's provenance is the set
of providers it really consumed, persisted with the incident, never the
configuration that happens to be active when it is read. One mock input or
effect makes the whole workflow non-real.
"""
from app.providers import evidence_provider, finops_provider, rca_provider, recovery_provider
from app.remediation import executor

ROLES = ("rca", "evidence", "finops", "remediation", "recovery")


def configured_modes():
    """The configuration now; describes what WOULD be used, not what was."""
    return {"rca": rca_provider.RCA_PROVIDER, "evidence": evidence_provider.EVIDENCE_PROVIDER,
            "finops": finops_provider.FINOPS_PROVIDER, "recovery": recovery_provider.RECOVERY_PROVIDER,
            "remediation": "mock" if executor.REMEDIATION_BACKEND == "mock" else "real"}


def _normalize(mode):
    return "mock" if mode == "mock" else "real"


def provider_use(incident):
    """{role: [modes used, in order]}. Legacy incidents fall back to their stored snapshot."""
    used = incident.get("_provider_use")
    if isinstance(used, dict):
        return used
    legacy = incident.get("_provenance")
    return {role: [_normalize(mode)] for role, mode in legacy.items()} if isinstance(legacy, dict) else {}


def _derive(used):
    return {role: ("mock" if "mock" in modes else "real") for role, modes in used.items() if modes}


def record_provider_use(incident, role, mode=None):
    """Record the provider about to be consumed for `role` and refresh the derived summary."""
    if role not in ROLES:
        raise ValueError(f"Unknown provider role {role}")
    used = {key: list(value) for key, value in provider_use(incident).items()}
    actual = _normalize(mode if mode is not None else configured_modes()[role])
    history = used.setdefault(role, [])
    if actual not in history:
        history.append(actual)
    incident["_provider_use"] = used
    incident["_provenance"] = _derive(used)
    return actual


def workflow_source(incident):
    """real only when every provider actually used was real; mixed if both kinds were used."""
    modes = set(_derive(provider_use(incident)).values())
    if not modes:
        return "mock" if "mock" in configured_modes().values() else "real"
    if modes == {"real"}:
        return "real"
    return "mock" if modes == {"mock"} else "mixed"


def provenance_view(incident):
    used = provider_use(incident)
    return {"source": workflow_source(incident), "modes": _derive(used), "used": used,
            "unused": [role for role in ROLES if not used.get(role)], "configured_now": configured_modes()}
