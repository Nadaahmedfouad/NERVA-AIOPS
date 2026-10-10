from pathlib import Path

import pytest

from shared import registry
from shared.registry import RegistryError, default_registry, load

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "config" / "services.multi-example.yaml"
VALID = """version: 1
services:
  - name: payment-service
    namespace: nexus-demo
    workload: {kind: Deployment, name: payment-service}
    remediation: {actions: [SCALE], min_replicas: 1, max_replicas: 6, max_scale_step: 2}
"""


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.delenv("NEXUS_SERVICES_CONFIG", raising=False)
    registry.set_registry(None)
    yield
    registry.set_registry(None)


def write(tmp_path, text):
    path = tmp_path / "services.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_default_registry_has_payment_service():
    reg = default_registry()
    assert reg.allowed_services() == {"payment-service"}
    assert reg.target_for("payment-service").workload.name == "payment-service"


def test_repository_registry_lists_only_services_with_telemetry_and_a_workload():
    reg = load()
    assert reg.allowed_services() == {"payment-service"}
    assert registry.registry_info()["source"].endswith("services.yaml")


def test_multi_service_example_is_valid_but_not_loaded_by_default():
    reg = load(EXAMPLE)
    assert {"payment-service", "cart-service", "frontend"} == reg.allowed_services()
    assert reg.allowed_actions("cart-service") == {"SCALE"}
    assert reg.replica_bounds("cart-service") == (1, 5)
    assert reg.target_for("frontend").depends_on == ["payment-service", "cart-service"]
    with pytest.raises(ValueError, match="not allowed for remediation"):
        reg.target_for("non-existent-service")


def test_explicit_missing_registry_fails_startup(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXUS_SERVICES_CONFIG", str(tmp_path / "absent.yaml"))
    with pytest.raises(RegistryError, match="does not exist"):
        registry.get_registry()


@pytest.mark.parametrize("text,problem", [
    ("services: [", "not valid YAML"),
    ("version: 2\nservices: []", "invalid"),
    (VALID.replace("[SCALE]", "[RESTART]"), "unsupported remediation actions"),
    (VALID.replace("max_scale_step: 2", "max_scale_step: 9"), "max_scale_step"),
    (VALID.replace("min_replicas: 1", "min_replicas: 8"), "min_replicas"),
    (VALID.replace("kind: Deployment", "kind: StatefulSet"), "invalid"),
    (VALID.replace("namespace: nexus-demo", "namespace: Nexus_Demo"), "DNS-1123"),
    (VALID + "    depends_on: [ghost]\n", "invalid"),
    (VALID.replace("    remediation:", "    typo_field: 1\n    remediation:"), "invalid"),
])
def test_explicit_invalid_registry_fails_loudly(monkeypatch, tmp_path, text, problem):
    monkeypatch.setenv("NEXUS_SERVICES_CONFIG", str(write(tmp_path, text)))
    with pytest.raises(RegistryError, match=problem):
        registry.get_registry()


def test_scale_policy_enforces_bounds_and_step(tmp_path):
    reg = load(write(tmp_path, VALID))
    assert reg.scale_allowed("payment-service", 2, 4) is None
    assert "at most 2" in reg.scale_allowed("payment-service", 1, 4)
    assert "between 1 and 6" in reg.scale_allowed("payment-service", 5, 7)
    assert "increase" in reg.scale_allowed("payment-service", 3, 3)
    assert "not registered" in reg.scale_allowed("cart-service", 1, 2)
